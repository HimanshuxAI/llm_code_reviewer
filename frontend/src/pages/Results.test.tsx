import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Results from "./Results";

const VULNERABLE = 'import os\npassword = "hunter2hunter2"\nos.system("ls " + input())\n';

const PAYLOAD = {
  id: 3,
  language: "python",
  score: 80,
  source_code: VULNERABLE,
  created_at: "2026-11-16T12:53:51.684635",
  findings: [
    {
      rule_id: "SEC003",
      title: "Hardcoded credential",
      severity: "high",
      line: 2,
      explanation: "Secrets committed in source leak through history.",
      suggestion: "Use environment variables.",
      source: "static",
      fixed_snippet: null,
    },
    {
      rule_id: "SEC010",
      title: "OS command execution",
      severity: "high",
      line: 3,
      explanation: "os.system interpolates input straight into a shell.",
      suggestion: "Use subprocess.run with a list.",
      source: "static",
      fixed_snippet: null,
    },
  ],
};

function renderResults(payload: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => payload,
    }))
  );

  return render(
    <MemoryRouter initialEntries={["/results/3"]}>
      <Routes>
        <Route path="/results/:id" element={<Results />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Results page", () => {
  beforeEach(() => {
    localStorage.setItem("code-reviewer.token", "test-token");
  });

  it("renders the submitted source code in the editor", async () => {
    const { container } = renderResults(PAYLOAD);

    await waitFor(() => {
      expect(container.querySelector(".ide-code pre")).toBeInTheDocument();
    });
    const code = container.querySelector(".ide-code pre")?.textContent ?? "";
    expect(code).toContain("hunter2hunter2");
    expect(code).toContain("os.system");
  });

  it("renders every finding in the problems inspector", async () => {
    renderResults(PAYLOAD);

    await waitFor(() => {
      expect(screen.getByText("Hardcoded credential")).toBeInTheDocument();
    });
    expect(screen.getByText("OS command execution")).toBeInTheDocument();
    expect(screen.getByText(/SEC003/)).toBeInTheDocument();
    expect(screen.getByText(/SEC010/)).toBeInTheDocument();
  });

  it("shows the score and the number of problems", async () => {
    renderResults(PAYLOAD);

    await waitFor(() => {
      expect(screen.getByText(/score 80\/100/)).toBeInTheDocument();
    });
    expect(screen.getByText("2 problems")).toBeInTheDocument();
  });

  it("flags the gutter lines that have findings", async () => {
    const { container } = renderResults(PAYLOAD);

    await waitFor(() => {
      expect(container.querySelectorAll(".ide-gutter-line.flagged")).toHaveLength(2);
    });
  });

  it("still renders the findings when the API omits source_code", async () => {
    // An older or malformed backend response must not blank the page.
    const { source_code: _omitted, ...withoutSource } = PAYLOAD;
    renderResults(withoutSource);

    await waitFor(() => {
      expect(screen.getByText("Hardcoded credential")).toBeInTheDocument();
    });
    expect(screen.getByText("OS command execution")).toBeInTheDocument();
  });

  it("shows a not-found state when the request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({ ok: false, status: 404, json: async () => ({}) }))
    );

    render(
      <MemoryRouter initialEntries={["/results/999"]}>
        <Routes>
          <Route path="/results/:id" element={<Results />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Review not found" })
      ).toBeInTheDocument();
    });
  });
});
