from __future__ import annotations


class InMemoryEvidenceRepository:
    def __init__(self):
        self.claims = {}
        self.links = {}
        self.assessments = []
        self.decisions = []
        self._sources = {}

    async def add_claim(self, x):
        self.claims[x.id] = x

    async def get_claim(self, i):
        return self.claims.get(i)

    async def get_claim_by_fingerprint(self, p, f):
        return next(
            (x for x in self.claims.values() if x.project_id == p and x.fingerprint == f), None
        )

    async def update_claim(self, x):
        self.claims[x.id] = x

    async def add_link(self, x):
        self.links[x.id] = x

    async def links_for_claim(self, i):
        return [x for x in self.links.values() if x.claim_id == i]

    async def add_assessment(self, x):
        self.assessments.append(x)

    async def add_review(self, x):
        self.decisions.append(x)

    async def sources(self):
        return self._sources
