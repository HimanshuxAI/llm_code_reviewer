import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import ErrorBoundary from "./ErrorBoundary";

function Boom(): React.ReactElement {
  throw new Error("kaboom from a broken component");
}

describe("ErrorBoundary", () => {
  it("shows a readable message instead of a blank page when a child throws", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>
    );

    expect(screen.getByText("Something broke on this screen")).toBeInTheDocument();
    expect(screen.getByText(/kaboom from a broken component/)).toBeInTheDocument();
    expect(screen.getByText("Reload page")).toBeInTheDocument();

    spy.mockRestore();
  });

  it("renders its children when nothing throws", () => {
    render(
      <ErrorBoundary>
        <p>all good</p>
      </ErrorBoundary>
    );

    expect(screen.getByText("all good")).toBeInTheDocument();
  });
});
