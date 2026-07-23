import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SafeMarkdown, StatusBadge } from "@/components/primitives";
describe("admin primitives", () => {
  it("renders status with text, not color only", () => {
    render(<StatusBadge value="FAILED" />);
    expect(screen.getByLabelText("Status: FAILED")).toHaveTextContent("FAILED");
  });
  it("renders malicious markup as text", () => {
    render(<SafeMarkdown>{"<img src=x onerror=alert(1)>unsafe"}</SafeMarkdown>);
    expect(document.querySelector("img")).toBeNull();
    expect(screen.getByText(/unsafe/)).toBeVisible();
  });
});
