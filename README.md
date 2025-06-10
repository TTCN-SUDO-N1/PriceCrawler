# Product Price Crawler API

This API provides endpoints to manage products, competitor websites (enemies), product crawls, and product crawl logs.

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/TTCN-SUDO-N1/PriceCrawler
   cd PriceCrawler
   ```
2. Create a python virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```
3. Set up .env file:
   - Create a `.env` file in the root directory or use the provided `.env_example` as a template(delete the `_example` suffix).
   - Fill in the required environment variables such as database configuration, API keys, and model configuration.
   - Get [chrome](https://storage.googleapis.com/chrome-for-testing-public/137.0.7151.68/win64/chromedriver-win64.zip) or [firefox](https://github.com/mozilla/geckodriver/releases) driver, extract an copy the path of the executable and set the path in the `.env` file. Uncomment the `CHROME_DRIVER_PATH` or `FIREFOX_DRIVER_PATH` line as needed.
   - Create a [Google Gemini API key](https://aistudio.google.com/app/apikey) and set it in the `.env` file.
4. Database setup:
    - Ensure you have a MySQL database running.
    - Create a database and user as specified in the `.env` file.
    - Run the migrations to set up the database schema:
      ```bash
      flask db init
      flask db migrate -m "Initial migration"
      flask db upgrade
      ```
5. Run the application:
    ```python
    python app.py
    ```
6. Access the API at `http://localhost:5000/index`.

## API Endpoints

Access the API documentation at `http://localhost:5000/api` to explore available endpoints and their details.

### Products

- **GET /api/product/** - Get all products with search and pagination
  - Query parameters:
    - `search` - Search products by name or SKU
    - `page` - Page number (default: 1)
    - `per_page` - Items per page (default: 10, max: 100)
- **GET /api/product/{id}** - Get a specific product by ID
- **POST /api/product/** - Create a new product
  - Required fields: `name`
  - Optional fields: `sku`, `link`, `org_price`, `cur_price`
- **PUT /api/product/{id}** - Update a product by ID
- **DELETE /api/product/{id}** - Delete a product by ID
- **POST /api/product/extract-info** - Extract product information from a link
  - Required fields: `link`
- **POST /api/product/{id}/crawl** - Crawl and update product information by ID

### Enemies (Competitors)

- **GET /api/enemy/** - Get all enemies
- **GET /api/enemy/{id}** - Get a specific enemy by ID
- **POST /api/enemy/** - Create a new enemy
  - Required fields: `name`, `domain`
- **PUT /api/enemy/{id}** - Update an enemy by ID
- **DELETE /api/enemy/{id}** - Delete an enemy by ID
- **GET /api/enemy/by-domain** - Find enemy by domain with auto-creation option
  - Query parameters:
    - `domain` - Domain to search for (required)
    - `auto_create` - Automatically create if not found (boolean, default: false)

### Product Crawls

- **GET /api/product_crawl/** - Get all product crawls
  - Query parameters:
    - `prod_id` - Filter by product ID
- **GET /api/product_crawl/{id}** - Get a specific product crawl by ID
- **POST /api/product_crawl/** - Create a new product crawl
  - Required fields: `prod_id`, `enemy_id`, `link`
- **PUT /api/product_crawl/{id}** - Update a product crawl by ID
- **DELETE /api/product_crawl/{id}** - Delete a product crawl by ID
- **GET /api/product_crawl/by-link** - Get product crawl by link
  - Query parameters:
    - `link` - Crawl link (required)
- **POST /api/product_crawl/crawl-link** - Crawl a product by link and save log
  - Request body: `link` (string) or `crawl_id` (integer)

### Product Crawl Logs

- **GET /api/product_crawl_log/** - Get all product crawl logs
  - Query parameters:
    - `product_crawl_id` - Filter logs by product crawl ID
- **GET /api/product_crawl_log/{id}** - Get a specific log by ID
- **POST /api/product_crawl_log/** - Create a new log
  - Required fields: `product_crawl_id`, `name`
  - Optional fields: `price`, `other_data`
- **PUT /api/product_crawl_log/{id}** - Update a log by ID
- **DELETE /api/product_crawl_log/{id}** - Delete a log by ID
- **GET /api/product_crawl_log/price-history/{product_crawl_id}** - Get price history with chart data for a product crawl

## API Features

### Product Management
- **Search and Pagination**: Products can be searched by name or SKU with pagination support
- **Price Tracking**: Original and current prices are tracked with automatic validation
- **Link Extraction**: Automatic product information extraction from competitor links
- **Individual Crawling**: Products can be crawled individually to update their information

### Competitor Management
- **Domain-based Discovery**: Enemies can be found and auto-created based on domain
- **Automatic Creation**: New competitors are automatically created when processing new domains

### Product Crawling
- **Link-based Operations**: Product crawls can be retrieved and executed by link
- **Batch Processing**: Supports concurrent crawling with batch processing (3 items at a time)
- **Filtering**: Product crawls can be filtered by product ID

### Price History and Analytics
- **Historical Tracking**: Complete price history with timestamps
- **Chart Data**: Ready-to-use data for price trend visualization
- **Statistics**: Price trend analysis (increasing/decreasing/stable)
- **Color-coded Analysis**: Smart color coding for price comparisons

## Response Formats

### Pagination Response
```json
{
  "products": [...],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 50,
    "pages": 5,
    "has_prev": false,
    "has_next": true
  }
}
```

### Price History Response
```json
{
  "product_crawl": {
    "id": 1,
    "link": "https://competitor.com/product",
    "product": "Sample Product",
    "enemy": "Competitor Store"
  },
  "price_history": [...],
  "chart_data": {
    "labels": ["2025-06-01 10:00", "2025-06-02 10:00"],
    "prices": [100.0, 95.0],
    "latest_price": 95.0,
    "price_trend": "decreasing",
    "price_change": -5.0,
    "total_records": 2
  }
}
```

## API Usage Examples

### Create a new product
```bash
curl -X POST http://localhost:5000/api/product/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sample Product",
    "sku": "SP001",
    "link": "https://example.com/product",
    "org_price": 100.0,
    "cur_price": 95.0
  }'
```

### Search products with pagination
```bash
curl "http://localhost:5000/api/product/?search=Sample&page=1&per_page=5"
```

### Extract product information from a link
```bash
curl -X POST http://localhost:5000/api/product/extract-info \
  -H "Content-Type: application/json" \
  -d '{"link": "https://example.com/product"}'
```

### Create a new enemy (competitor)
```bash
curl -X POST http://localhost:5000/api/enemy/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Competitor Store",
    "domain": "competitor.com"
  }'
```

### Find enemy by domain with auto-creation
```bash
curl "http://localhost:5000/api/enemy/by-domain?domain=newcompetitor.com&auto_create=true"
```

### Create a product crawl
```bash
curl -X POST http://localhost:5000/api/product_crawl/ \
  -H "Content-Type: application/json" \
  -d '{
    "prod_id": 1,
    "enemy_id": 1,
    "link": "https://competitor.com/product"
  }'
```

### Crawl product by link and save log
```bash
curl -X POST http://localhost:5000/api/product_crawl/crawl-link \
  -H "Content-Type: application/json" \
  -d '{"link": "https://competitor.com/product"}'
```

### Get price history with chart data
```bash
curl "http://localhost:5000/api/product_crawl_log/price-history/1"
```

### Filter product crawls by product ID
```bash
curl "http://localhost:5000/api/product_crawl/?prod_id=1"
```

### Filter crawl logs by product crawl ID
```bash
curl "http://localhost:5000/api/product_crawl_log/?product_crawl_id=1"
```
