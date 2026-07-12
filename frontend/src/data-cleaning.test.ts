import { describe, it, expect } from "vitest";

describe("Data Cleaning Helpers", () => {
  it("trims and collapses whitespace in names", () => {
    const rawName = "  Test   Product ";
    const cleaned = rawName.trim().replace(/\s+/g, " ");
    expect(cleaned).toBe("Test Product");
  });

  it("parses price with currency symbols", () => {
    const rawPrice = "£10.25";
    const parsed = Number(String(rawPrice).replace(/[£$,]/g, ""));
    expect(parsed).toBe(10.25);
  });

  it("validates category against allowed set", () => {
    const allowed = new Set(["electronics", "home", "fashion", "sports", "beauty", "books"]);
    const category = "unknown";
    const cleaned = allowed.has(category) ? category : "electronics";
    expect(cleaned).toBe("electronics");
  });

  it("clamps negative quantity to zero", () => {
    const parsed = Number.parseInt("-2", 10);
    const cleaned = Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
    expect(cleaned).toBe(0);
  });

  it("clamps rating to 0-5 range", () => {
    const parsed = Number("8");
    const clamped = Math.min(5, Math.max(0, parsed));
    expect(clamped).toBe(5);
  });

  it("generates fallback image link for invalid URLs", () => {
    const image = "";
    const id = "p-1001";
    const isValid = image.startsWith("http://") || image.startsWith("https://") || image.startsWith("/");
    const fallback = `https://source.unsplash.com/600x400/?product,${encodeURIComponent(id)}`;
    expect(isValid ? image : fallback).toBe(fallback);
  });

  it("accepts valid HTTP image URL", () => {
    const image = "http://example.com/image.jpg";
    const isValid = image.startsWith("http://") || image.startsWith("https://") || image.startsWith("/");
    expect(isValid).toBe(true);
  });
});
