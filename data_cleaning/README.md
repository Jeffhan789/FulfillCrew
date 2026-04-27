# Data Cleaning Pipeline

This folder represents the COMP315 CA1 foundation. It cleans noisy product JSON records before they are used by the frontend, backend, agent system and ML modules.

Handled fields:

- `id`
- `name`
- `price`
- `category`
- `type`
- `quantity`
- `rating`
- `image_link`

Run:

```bash
node data_processing.js raw_products/products.json cleaned_products/products.json
```

