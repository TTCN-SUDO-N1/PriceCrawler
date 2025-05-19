# Product Price Crawler API

This API provides endpoints to manage products, competitor websites (enemies), product crawls, and product crawl logs.

## Setup

1. Ensure you have Python 3.x and pip installed
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python app.py`

## API Endpoints

### Products

- **GET /api/products** - Get all products
- **GET /api/products/:id** - Get a specific product
- **POST /api/products** - Create a new product
  - Required fields: `name`
  - Optional fields: `sku`, `link`, `org_price`, `cur_price`
- **PUT /api/products/:id** - Update a product
- **DELETE /api/products/:id** - Delete a product

### Enemies (Competitors)

- **GET /api/enemies** - Get all enemies
- **GET /api/enemies/:id** - Get a specific enemy
- **POST /api/enemies** - Create a new enemy
  - Required fields: `name`, `domain`
- **PUT /api/enemies/:id** - Update an enemy
- **DELETE /api/enemies/:id** - Delete an enemy

### Product Crawls

- **GET /api/product-crawls** - Get all product crawls
- **GET /api/products/:id/crawls** - Get crawls for a specific product
- **GET /api/enemies/:id/crawls** - Get crawls for a specific enemy
- **GET /api/product-crawls/:id** - Get a specific product crawl
- **POST /api/product-crawls** - Create a new product crawl
  - Required fields: `prod_id`, `enemy_id`, `link`
- **PUT /api/product-crawls/:id** - Update a product crawl
- **DELETE /api/product-crawls/:id** - Delete a product crawl

### Product Crawl Logs

- **GET /api/logs** - Get all logs
- **GET /api/product-crawls/:id/logs** - Get logs for a specific product crawl
- **GET /api/logs/:id** - Get a specific log
- **POST /api/logs** - Create a new log
  - Required fields: `product_crawl_id`, `name`
  - Optional fields: `price`, `other_data`
- **PUT /api/logs/:id** - Update a log
- **DELETE /api/logs/:id** - Delete a log

## Examples

### Create a new product


```
