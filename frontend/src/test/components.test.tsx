import { render, screen } from "@testing-library/react";
import { MetricCard } from "../components/cards/MetricCard";
import { EmptyState, ErrorState, Loading } from "../components/feedback/States";

describe("components", () => {
  it("MetricCard exposes value with its description", () => {
    render(<MetricCard id="x" label="MAE" value="12.0 MW" hint="Mean absolute error" />);
    expect(screen.getByText("12.0 MW")).toHaveAccessibleDescription("Mean absolute error");
  });
  it("shows loading, error with retry, and empty states", () => {
    const retry = vi.fn();
    render(<><Loading /><ErrorState message="boom" onRetry={retry} /><EmptyState>none</EmptyState></>);
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("boom");
    screen.getByRole("button", { name: "Retry" }).click();
    expect(retry).toHaveBeenCalled();
  });
});
