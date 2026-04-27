# System Design

```text
React Frontend
  -> FastAPI Backend
    -> Multi-Agent System
      -> Demand and Fraud ML Modules
    -> Cleaned Product Data
```

The first implementation keeps data in memory so that the portfolio demo remains easy to run. The next natural upgrade is to replace the in-memory product store with SQLite or PostgreSQL.

