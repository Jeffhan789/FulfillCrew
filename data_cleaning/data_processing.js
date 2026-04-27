const fs = require("fs");
const path = require("path");

function cleanName(value, id) {
  const name = String(value || "").trim().replace(/\s+/g, " ");
  return name || `Product ${id}`;
}

function cleanPrice(value) {
  const parsed = Number(String(value ?? "").replace(/[£$,]/g, ""));
  return Number.isFinite(parsed) && parsed > 0 ? Number(parsed.toFixed(2)) : 9.99;
}

function cleanCategory(value) {
  const category = String(value || "").trim().toLowerCase();
  const allowed = new Set(["electronics", "home", "fashion", "sports", "beauty", "books"]);
  return allowed.has(category) ? category : "electronics";
}

function cleanType(value, category) {
  const type = String(value || "").trim().toLowerCase();
  if (type) return type;
  const defaults = {
    electronics: "device",
    home: "accessory",
    fashion: "wearable",
    sports: "equipment",
    beauty: "personal care",
    books: "paperback",
  };
  return defaults[category] || "general";
}

function cleanQuantity(value) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
}

function cleanRating(value) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return 0;
  return Math.min(5, Math.max(0, Number(parsed.toFixed(1))));
}

function cleanImageLink(value, id) {
  const image = String(value || "").trim();
  if (image.startsWith("http://") || image.startsWith("https://") || image.startsWith("/")) {
    return image;
  }
  return `https://source.unsplash.com/600x400/?product,${encodeURIComponent(id)}`;
}

function cleanProduct(product, index) {
  const id = product.id || `p-${index + 1}`;
  const category = cleanCategory(product.category);
  return {
    id,
    name: cleanName(product.name, id),
    price: cleanPrice(product.price),
    category,
    type: cleanType(product.type, category),
    quantity: cleanQuantity(product.quantity),
    rating: cleanRating(product.rating),
    image_link: cleanImageLink(product.image_link, id),
  };
}

function cleanProducts(products) {
  return products.map(cleanProduct);
}

function runCli() {
  const [, , inputPath, outputPath] = process.argv;
  if (!inputPath || !outputPath) {
    throw new Error("Usage: node data_processing.js <input-json> <output-json>");
  }

  const raw = JSON.parse(fs.readFileSync(inputPath, "utf8"));
  const products = Array.isArray(raw) ? raw : raw.products;
  if (!Array.isArray(products)) {
    throw new Error("Input JSON must be an array or an object with a products array.");
  }

  const cleaned = cleanProducts(products);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, `${JSON.stringify(cleaned, null, 2)}\n`);
}

if (require.main === module) {
  runCli();
}

module.exports = {
  cleanName,
  cleanPrice,
  cleanCategory,
  cleanType,
  cleanQuantity,
  cleanRating,
  cleanImageLink,
  cleanProduct,
  cleanProducts,
};

