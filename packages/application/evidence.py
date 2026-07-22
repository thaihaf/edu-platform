"""Deterministic Phase 6 evidence policies and in-memory-friendly use cases."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from packages.domain.evidence import (
    Claim,
    ClaimConfidenceAssessment,
    ClaimStatus,
    ClaimType,
    EvidenceError,
    EvidenceLink,
    EvidenceRelation,
    ReviewDecision,
    ReviewDecisionType,
    ReviewStatus,
    claim_fingerprint,
    normalize,
)


@dataclass(frozen=True)
class ConfidencePolicy:
    version: str = "phase6.v1"

    def assess(
        self, claim: Claim, links: Iterable[EvidenceLink], sources: dict[UUID, object]
    ) -> ClaimConfidenceAssessment:
        items = list(links)
        clusters = {x.independence_cluster_id or x.source_id for x in items}

        def vals(name: str, default: float = 0.5) -> list[float]:
            return [
                float(getattr(sources.get(x.source_id), name, default) or default) for x in items
            ]

        authority = sum(vals("authority_score")) / len(items) if items else 0
        direct = sum(x.directness for x in items) / len(items) if items else 0
        fresh = sum(vals("freshness_score")) / len(items) if items else 0
        specificity = sum(x.strength for x in items) / len(items) if items else 0
        temporal = sum(x.temporal_relevance for x in items) / len(items) if items else 0
        independent = min(1, len(clusters) / 2)
        corroboration = min(1, len(clusters) / 3)
        contrad = sum(x.relation is EvidenceRelation.CONTRADICTS for x in items) / max(
            1, len(items)
        )
        bias = sum(vals("commercial_bias_score", 0)) / len(items) if items else 0
        reviewer = 1 if claim.review_status is ReviewStatus.HUMAN_APPROVED else 0
        final = max(
            0,
            min(
                1,
                (
                    authority
                    + direct
                    + fresh
                    + specificity
                    + independent
                    + corroboration
                    + temporal
                    + reviewer
                )
                / 8
                - contrad * 0.35
                - bias * 0.15,
            ),
        )
        return ClaimConfidenceAssessment(
            claim.id,
            authority,
            direct,
            fresh,
            specificity,
            independent,
            corroboration,
            contrad,
            bias,
            temporal,
            reviewer,
            final,
            self.version,
            "Deterministic weighted components; duplicate-cluster members count once.",
        )


class EvidenceService:
    def __init__(self, repository: object, policy: ConfidencePolicy | None = None):
        self.repo = repository
        self.policy = policy or ConfidencePolicy()
        self.keys: dict[str, str] = {}

    async def build(
        self, project_id: UUID, observations: Iterable[object], key: str
    ) -> list[Claim]:
        observations = list(observations)

        def observation_text(observation: object) -> str:
            """Read Phase 5 observations before compatibility fields."""
            return str(
                getattr(
                    observation,
                    "normalized_text",
                    getattr(observation, "text", getattr(observation, "statement", "")),
                )
            )

        payload = repr([(getattr(x, "id", None), observation_text(x)) for x in observations])
        if key in self.keys and self.keys[key] != payload:
            raise EvidenceError("IDEMPOTENCY_CONFLICT", "Idempotency key has a different payload")
        self.keys[key] = payload
        created = []
        for observation in observations:
            statement = normalize(observation_text(observation))
            if not statement:
                continue
            claim = Claim(
                project_id,
                statement,
                ClaimType.OTHER,
                created_from_observation_ids=(observation.id,),
                normalization_metadata={
                    "method": "deterministic",
                    "schema_version": "phase6.v1",
                    "fingerprint": claim_fingerprint(statement, (), ClaimType.OTHER, {}),
                },
            )
            existing = await self.repo.get_claim_by_fingerprint(project_id, claim.fingerprint)
            if existing:
                continue
            await self.repo.add_claim(claim)
            created.append(claim)
        return created

    async def recalculate(self, claim_id: UUID) -> ClaimConfidenceAssessment:
        claim = await self.repo.get_claim(claim_id)
        if not claim:
            raise EvidenceError("CLAIM_NOT_FOUND", "Claim not found")
        assessment = self.policy.assess(
            claim, await self.repo.links_for_claim(claim_id), await self.repo.sources()
        )
        claim.confidence = assessment.final_confidence
        claim.confidence_components = {
            "policy_version": assessment.policy_version,
            "final": assessment.final_confidence,
        }
        await self.repo.update_claim(claim)
        await self.repo.add_assessment(assessment)
        return assessment

    async def review_claim(
        self, claim_id: UUID, reviewer: UUID, decision: ReviewDecisionType, reason: str
    ) -> Claim:
        claim = await self.repo.get_claim(claim_id)
        if not claim:
            raise EvidenceError("CLAIM_NOT_FOUND", "Claim not found")
        old = claim.status.value
        targets = {
            ReviewDecisionType.APPROVE: (ClaimStatus.VERIFIED, ReviewStatus.HUMAN_APPROVED),
            ReviewDecisionType.REJECT: (ClaimStatus.REJECTED, ReviewStatus.HUMAN_REJECTED),
            ReviewDecisionType.MARK_DISPUTED: (ClaimStatus.DISPUTED, ReviewStatus.NEEDS_REVIEW),
            ReviewDecisionType.MARK_OBSOLETE: (ClaimStatus.OBSOLETE, ReviewStatus.HUMAN_APPROVED),
            ReviewDecisionType.REQUEST_CHANGES: (Claim.status, ReviewStatus.NEEDS_REVIEW),
        }
        if decision not in targets:
            raise EvidenceError("REVIEW_DECISION_INVALID", "Decision does not apply to a claim")
        target, review = targets[decision]
        verified = target is not ClaimStatus.VERIFIED or (
            claim.confidence >= 0.6
            and not any(
                x.relation is EvidenceRelation.CONTRADICTS
                for x in await self.repo.links_for_claim(claim.id)
            )
        )
        # Human approval is allowed to complete the candidate -> probable -> verified
        # lifecycle in one reviewed operation once the verification policy is satisfied.
        if target is ClaimStatus.VERIFIED and claim.status is ClaimStatus.CANDIDATE and verified:
            claim.transition(ClaimStatus.PROBABLE)
        if target is not claim.status:
            claim.transition(target, verified=verified)
        claim.review_status = review
        await self.repo.update_claim(claim)
        await self.repo.add_review(
            ReviewDecision(
                claim.project_id,
                reviewer,
                "CLAIM",
                claim.id,
                decision,
                reason,
                old,
                claim.status.value,
            )
        )
        return claim
