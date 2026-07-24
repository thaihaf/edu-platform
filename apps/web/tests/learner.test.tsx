import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  Citation,
  Flashcards,
  LessonBlock,
  Practice,
  Progress,
} from "@/components/learner";
import { demoQuestion } from "@/api/learner";

describe("learner safety and interaction", () => {
  it("renders lesson markdown as text rather than HTML", () => {
    render(
      <LessonBlock
        type="MARKDOWN"
        content={'<img src=x onerror="alert(1)">'}
      />,
    );
    expect(screen.getByLabelText("Sanitized text")).toHaveTextContent(
      "onerror",
    );
    expect(document.querySelector("img")).toBeNull();
  });
  it("does not reveal an answer until practice submission", () => {
    render(<Practice session />);
    expect(screen.queryByText("Correct.")).toBeNull();
    fireEvent.click(screen.getByLabelText(/<h1>/));
    fireEvent.click(screen.getByRole("button", { name: "Submit answer" }));
    expect(screen.getByText("Correct.")).toBeVisible();
  });
  it("reveals a flashcard only on request and exposes a labelled progress value", () => {
    const { rerender } = render(<Flashcards deck />);
    expect(screen.queryByText(/primary subject/)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Reveal answer" }));
    expect(screen.getByText(/primary subject/)).toBeVisible();
    rerender(<Progress value={33} />);
    expect(screen.getAllByText("33%")[0]).toBeVisible();
  });
  it("rejects unsafe citation URLs", () => {
    render(
      <Citation
        citation={{ ...demoQuestion.citation, url: "javascript:alert(1)" }}
      />,
    );
    expect(screen.queryByRole("link", { name: /open/i })).toBeNull();
  });
});
