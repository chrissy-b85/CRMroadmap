import "@testing-library/jest-dom";
import React from "react";
import { render, screen } from "@testing-library/react";
import Sidebar from "@/components/layout/Sidebar";

// Mock Next.js navigation hooks used inside Sidebar
jest.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
}));

// Mock Next.js Link to a simple <a> tag for testing
jest.mock("next/link", () => {
  const MockLink = ({
    href,
    children,
    ...props
  }: {
    href: string;
    children: React.ReactNode;
    [key: string]: unknown;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
  MockLink.displayName = "MockLink";
  return MockLink;
});

describe("Sidebar", () => {
  test("renders without crashing", () => {
    render(<Sidebar />);
    expect(screen.getByLabelText("Sidebar")).toBeInTheDocument();
  });

  test('renders the "NDIS CRM" branding', () => {
    render(<Sidebar />);
    expect(screen.getByText("NDIS CRM")).toBeInTheDocument();
  });

  test("renders all 5 navigation links", () => {
    render(<Sidebar />);
    const navLabels = [
      "Dashboard",
      "Participants",
      "Invoices",
      "Reports",
      "Settings",
    ];
    navLabels.forEach((label) => {
      expect(screen.getByText(label)).toBeInTheDocument();
    });
  });

  test("marks the active route with aria-current=page", () => {
    render(<Sidebar />);
    const activeLink = screen.getByText("Dashboard").closest("a");
    expect(activeLink).toHaveAttribute("aria-current", "page");
  });

  test("non-active links do not have aria-current", () => {
    render(<Sidebar />);
    const participantsLink = screen.getByText("Participants").closest("a");
    expect(participantsLink).not.toHaveAttribute("aria-current");
  });
});
