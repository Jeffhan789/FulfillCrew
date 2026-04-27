# Agent Design

The order workflow follows a simplified Contract Net Protocol:

1. Order Agent receives a checkout request.
2. Inventory Agent checks stock availability.
3. Fraud Detection Agent scores order risk.
4. Coordinator Agent announces the task to Warehouse Agents.
5. Warehouse Agents submit bids.
6. Coordinator Agent selects the lowest bid.
7. Inventory Agent reserves stock if the order is approved.

