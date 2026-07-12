import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { CheckCircle2, Minus, Plus, Search, ShoppingBasket } from "lucide-react";
import "./styles.css";

type Product = {
  id: string;
  name: string;
  price: number;
  category: string;
  type: string;
  quantity: number;
  rating: number;
  image_link: string;
};

type BasketItem = {
  product: Product;
  quantity: number;
};

type WarehouseBid = {
  warehouse_id: string;
  bid: number;
  workload: number;
  distance: number;
  stock_level: number;
  processing_speed: number;
  suitability_score: number;
  reason: string;
};

type CourseMapping = {
  module: string;
  concept: string;
  implementation: string;
  evidence: string[];
};

type ModelEvaluation = {
  model_name: string;
  course_topic: string;
  metric: string;
  score: number;
  interpretation: string;
  training_mode: string;
  online_mode: string;
};

type OrderResponse = {
  order_id: string;
  order_status: string;
  order_total: number;
  selected_warehouse: string | null;
  risk_score: number;
  fraud_status: string;
  predicted_demand_next_7_days: number;
  restock_recommendation: string;
  bids: WarehouseBid[];
  decision_log: { agent: string; message: string }[];
  course_trace: { agent: string; message: string }[];
  model_evaluations: ModelEvaluation[];
};

// Use environment-aware API base; falls back to localhost for direct dev usage
const API_BASE = (import.meta.env.VITE_API_BASE as string) || "";

function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [basket, setBasket] = useState<BasketItem[]>([]);
  const [query, setQuery] = useState("");
  const [sortBy, setSortBy] = useState<"name" | "price" | "rating">("rating");
  const [inStockOnly, setInStockOnly] = useState(true);
  const [order, setOrder] = useState<OrderResponse | null>(null);
  const [courseMap, setCourseMap] = useState<CourseMapping[]>([]);
  const [modelEvaluations, setModelEvaluations] = useState<ModelEvaluation[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/products`)
      .then((response) => response.json())
      .then(setProducts)
      .catch(() => setProducts([]));
    fetch(`${API_BASE}/agents/course-map`)
      .then((response) => response.json())
      .then(setCourseMap)
      .catch(() => setCourseMap([]));
    fetch(`${API_BASE}/agents/model-evaluations`)
      .then((response) => response.json())
      .then(setModelEvaluations)
      .catch(() => setModelEvaluations([]));
  }, []);

  const visibleProducts = useMemo(() => {
    return products
      .filter((product) => product.name.toLowerCase().includes(query.toLowerCase()))
      .filter((product) => !inStockOnly || product.quantity > 0)
      .sort((a, b) => {
        if (sortBy === "name") return a.name.localeCompare(b.name);
        return sortBy === "price" ? a.price - b.price : b.rating - a.rating;
      });
  }, [products, query, sortBy, inStockOnly]);

  const basketTotal = basket.reduce((total, item) => total + item.product.price * item.quantity, 0);

  function addToBasket(product: Product) {
    setBasket((current) => {
      const existing = current.find((item) => item.product.id === product.id);
      if (existing) {
        return current.map((item) =>
          item.product.id === product.id ? { ...item, quantity: item.quantity + 1 } : item,
        );
      }
      return [...current, { product, quantity: 1 }];
    });
  }

  function removeFromBasket(productId: string) {
    setBasket((current) =>
      current
        .map((item) => (item.product.id === productId ? { ...item, quantity: item.quantity - 1 } : item))
        .filter((item) => item.quantity > 0),
    );
  }

  async function checkout() {
    const response = await fetch(`${API_BASE}/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: "demo-user",
        shipping_distance: 18,
        is_new_user: true,
        items: basket.map((item) => ({ product_id: item.product.id, quantity: item.quantity })),
      }),
    });
    const result = await response.json();
    setOrder(result);
  }

  return (
    <main className="app-shell">
      <section className="top-band">
        <div>
          <p className="eyebrow">COMP315 + COMP310 + ELEC320</p>
          <h1>Cloud Multi-Agent E-Commerce Intelligence System</h1>
        </div>
        <div className="metric-strip">
          <span>{visibleProducts.length} results</span>
          <span>{basket.length} basket lines</span>
          <span>{courseMap.length || 3} modules</span>
          <span>£{basketTotal.toFixed(2)}</span>
        </div>
      </section>

      <section className="control-row">
        <label className="search-box">
          <Search size={18} />
        <input value={query} onChange={(event: any) => setQuery(event.target.value)} placeholder="Search products" />
      </label>
        <select value={sortBy} onChange={(event: any) => setSortBy(event.target.value as "name" | "price" | "rating")}>
          <option value="rating">Sort by rating</option>
          <option value="price">Sort by price</option>
          <option value="name">Sort by name</option>
        </select>
        <label className="toggle">
          <input type="checkbox" checked={inStockOnly} onChange={(event: any) => setInStockOnly(event.target.checked)} />
          In stock
        </label>
      </section>

      <section className="course-dashboard">
        <div className="dashboard-heading">
          <p className="eyebrow">Course Intelligence Dashboard</p>
          <h2>How the system maps university theory into a working checkout flow</h2>
        </div>
        <div className="course-grid">
          {courseMap.map((item) => (
            <article className="course-card" key={item.module}>
              <p className="tag">{item.module}</p>
              <h3>{item.concept}</h3>
              <p>{item.implementation}</p>
              <ul>
                {item.evidence.map((evidence) => (
                  <li key={evidence}>{evidence}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
        <div className="model-strip">
          {modelEvaluations.map((model) => (
            <article className="model-tile" key={model.model_name}>
              <span>{model.course_topic}</span>
              <strong>{model.model_name}</strong>
              <p>{model.metric}: {model.score}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="workspace">
        <div className="product-grid">
          {visibleProducts.map((product) => (
            <article className="product-card" key={product.id}>
              <img src={`${product.image_link}?auto=format&fit=crop&w=600&q=80`} alt={product.name} />
              <div className="product-body">
                <div>
                  <p className="tag">{product.category} / {product.type}</p>
                  <h2>{product.name}</h2>
                </div>
                <div className="product-meta">
                  <strong>£{product.price.toFixed(2)}</strong>
                  <span>{product.rating.toFixed(1)} rating</span>
                  <span>{product.quantity} left</span>
                </div>
                <button disabled={product.quantity === 0} onClick={() => addToBasket(product)}>
                  <Plus size={17} />
                  Add
                </button>
              </div>
            </article>
          ))}
        </div>

        <aside className="basket-panel">
          <div className="panel-title">
            <ShoppingBasket size={20} />
            <h2>Basket</h2>
          </div>
          {basket.length === 0 ? <p className="muted">No items selected.</p> : null}
          {basket.map((item) => (
            <div className="basket-line" key={item.product.id}>
              <div>
                <strong>{item.product.name}</strong>
                <span>£{(item.product.price * item.quantity).toFixed(2)}</span>
              </div>
              <div className="quantity-tools">
                <button aria-label="Remove item" onClick={() => removeFromBasket(item.product.id)}>
                  <Minus size={15} />
                </button>
                <span>{item.quantity}</span>
                <button aria-label="Add item" onClick={() => addToBasket(item.product)}>
                  <Plus size={15} />
                </button>
              </div>
            </div>
          ))}
          <button className="checkout" disabled={basket.length === 0} onClick={checkout}>
            <CheckCircle2 size={18} />
            Checkout
          </button>
        </aside>
      </section>

      {order ? (
        <section className="order-band">
          <div className="order-summary">
            <h2>Order {order.order_status}</h2>
            <span>Warehouse: {order.selected_warehouse || "none"}</span>
            <span>Risk: {order.risk_score.toFixed(2)} / {order.fraud_status}</span>
            <span>Demand: {order.predicted_demand_next_7_days} units</span>
            <span>{order.restock_recommendation}</span>
          </div>
          <ol className="decision-log">
            {order.decision_log.map((entry, index) => (
              <li key={`${entry.agent}-${index}`}>
                <strong>{entry.agent}</strong>
                <span>{entry.message}</span>
              </li>
            ))}
          </ol>
          <div className="bid-board">
            <h2>Warehouse Bids</h2>
            {order.bids.map((bid) => (
              <article key={bid.warehouse_id}>
                <strong>{bid.warehouse_id}</strong>
                <span>Bid {bid.bid} / suitability {bid.suitability_score}</span>
                <p>{bid.reason}</p>
              </article>
            ))}
          </div>
          <div className="model-evidence">
            <h2>Model Evidence</h2>
            {order.model_evaluations.map((model) => (
              <article key={model.model_name}>
                <strong>{model.model_name}</strong>
                <span>{model.metric}: {model.score}</span>
                <p>{model.interpretation}</p>
              </article>
            ))}
          </div>
          <ol className="decision-log course-trace">
            {order.course_trace.map((entry, index) => (
              <li key={`${entry.agent}-${index}`}>
                <strong>{entry.agent}</strong>
                <span>{entry.message}</span>
              </li>
            ))}
          </ol>
        </section>
      ) : null}
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
