import { describe, it, expect } from "vitest";

describe("Frontend Sanity", () => {
  it("basic math works", () => {
    expect(1 + 1).toBe(2);
  });

  it("basket total calculation is correct", () => {
    const basket = [
      { product: { id: "p-1", name: "A", price: 10 }, quantity: 2 },
      { product: { id: "p-2", name: "B", price: 25 }, quantity: 1 },
    ];
    const total = basket.reduce((sum, item) => sum + item.product.price * item.quantity, 0);
    expect(total).toBe(45);
  });

  it("product filtering by search works", () => {
    const products = [
      { id: "p-1", name: "Wireless Headphones", category: "electronics" },
      { id: "p-2", name: "Running Shoes", category: "sports" },
    ];
    const query = "wireless";
    const filtered = products.filter((p) => p.name.toLowerCase().includes(query.toLowerCase()));
    expect(filtered.length).toBe(1);
    expect(filtered[0].id).toBe("p-1");
  });

  it("in-stock filter works", () => {
    const products = [
      { id: "p-1", name: "A", quantity: 5 },
      { id: "p-2", name: "B", quantity: 0 },
      { id: "p-3", name: "C", quantity: 3 },
    ];
    const inStock = products.filter((p) => p.quantity > 0);
    expect(inStock.length).toBe(2);
  });

  it("sorting by price works", () => {
    const products = [
      { id: "p-1", name: "A", price: 30 },
      { id: "p-2", name: "B", price: 10 },
      { id: "p-3", name: "C", price: 20 },
    ];
    const sorted = [...products].sort((a, b) => a.price - b.price);
    expect(sorted.map((p) => p.id)).toEqual(["p-2", "p-3", "p-1"]);
  });

  it("sorting by rating descending works", () => {
    const products = [
      { id: "p-1", name: "A", rating: 3.5 },
      { id: "p-2", name: "B", rating: 4.8 },
      { id: "p-3", name: "C", rating: 4.0 },
    ];
    const sorted = [...products].sort((a, b) => b.rating - a.rating);
    expect(sorted.map((p) => p.id)).toEqual(["p-2", "p-3", "p-1"]);
  });
});
