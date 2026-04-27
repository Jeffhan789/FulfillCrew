const assert = require("assert");
const { cleanProduct } = require("../data_cleaning/data_processing");

const cleaned = cleanProduct(
  {
    id: "x-1",
    name: "  Test   Product ",
    price: "£10.25",
    category: "unknown",
    quantity: "-2",
    rating: "8",
    image_link: "",
  },
  0,
);

assert.strictEqual(cleaned.name, "Test Product");
assert.strictEqual(cleaned.price, 10.25);
assert.strictEqual(cleaned.category, "electronics");
assert.strictEqual(cleaned.quantity, 0);
assert.strictEqual(cleaned.rating, 5);
