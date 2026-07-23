import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  ConfidenceBadge,
  ImmutableVersionControls,
  JsonEditor,
  ProtectedContentBlock,
  QuestionOriginBadge,
  QualityGateStatus,
  RegressionDelta,
} from "@/components/phase10c";

describe("Phase 10C safety primitives", () => {
  it("renders confidence and origin as text", () => {
    render(
      <>
        <ConfidenceBadge value="CONFIRMED" />
        <QuestionOriginBadge value="AI_SYNTHESIZED" />
      </>,
    );
    expect(screen.getByText(/CONFIRMED/)).toBeVisible();
    expect(screen.getByText(/AI_SYNTHESIZED/)).toBeVisible();
  });
  it("keeps published versions immutable", () => {
    render(<ImmutableVersionControls status="PUBLISHED" />);
    expect(screen.getByText(/immutable/)).toBeVisible();
    expect(screen.queryByText("Validate with API")).toBeNull();
  });
  it("marks protected content and does not execute markup", () => {
    render(
      <ProtectedContentBlock content={"<img src=x onerror=alert(1)>safe"} />,
    );
    expect(screen.getByText(/Human-authored lock/)).toBeVisible();
    expect(document.querySelector("img")).toBeNull();
  });
  it("reports invalid JSON without execution", () => {
    render(<JsonEditor label="Case JSON" value="{" />);
    expect(screen.getByRole("alert")).toHaveTextContent(/valid JSON/);
  });
  it("renders gate and non-color regression information", () => {
    render(
      <>
        <QualityGateStatus value="FAILED" />
        <RegressionDelta value={-0.2} />
      </>,
    );
    expect(screen.getByText(/Quality gate: FAILED/)).toBeVisible();
    expect(screen.getByLabelText("Metric regression")).toHaveTextContent(
      "-0.20",
    );
  });
});
