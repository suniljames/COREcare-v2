import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import Home from "../page";

describe("Home page", () => {
  it("renders the COREcare v2 heading", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: /corecare v2/i })).toBeInTheDocument();
  });

  it("renders the platform description", () => {
    render(<Home />);
    expect(screen.getByText(/multi-tenant/i)).toBeInTheDocument();
  });
});
