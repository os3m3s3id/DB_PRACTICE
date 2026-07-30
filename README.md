# Data Warehouse Project

A simple Data Warehouse (DWH) pipeline built with PostgreSQL, Airflow, and dlt. The project loads source data into a `staging` schema, then transforms it into a star schema in the `dwh` schema (`country_dim`, `customers_dim`, `product_dim`, `sales_transactions_fact`).

## Architecture

- **postgres-db** — main PostgreSQL database, hosts `staging` and `dwh` schemas
- **airflow-db** — metadata database for Airflow
- **airflow-webserver / airflow-scheduler** — orchestrates the pipeline (LocalExecutor)
- **dlt_loading** — loads raw source data into the `staging` schema
- **from-stg-to-dwh** — transforms `staging` tables into the `dwh` star schema
- **dbt** — (future) transformation/testing layer on top of `dwh`

The `dlt_loading`, `from-stg-to-dwh`, and `dbt` services are run as on-demand jobs (triggered via Airflow's DockerOperator), not long-running containers.

## Prerequisites

- Docker
- Docker Compose

## Getting Started

### 1. Clone the repository

```bash
git clone <repo-url>
cd <repo-folder>
```

### 2. Start the core services

```bash
docker-compose up -d
```

This starts:
- `postgres-db` (port `5432`)
- `airflow-db`
- `airflow-webserver` (port `8080`)
- `airflow-scheduler`

Airflow images are built automatically from `./airflow/Dockerfile` on first run — no manual build step needed.

### 3. Build the job images

The job containers (`dlt_loading`, `dbt`, `from-stg-to-dwh`) use Compose profiles and are **not** started by `up -d`. Build them separately so Airflow's DockerOperator can run them:

```bash
docker-compose --profile jobs build
```

### 4. Access Airflow

- URL: [http://localhost:8080](http://localhost:8080)
- Username: `admin`
- Password: `admin`

### 5. Run the pipeline

Trigger the relevant DAG(s) from the Airflow UI to run, in order:
1. `dlt_loading` — loads source data into `staging`
2. `from-stg-to-dwh` — builds the `dwh` star schema from `staging`

## Database Schema

### Staging (`staging` schema)
Raw source tables loaded as-is: `country`, `customer`, `product`, `sales_transactions`.

### Data Warehouse (`dwh` schema)

**Dimension tables** (each with a surrogate key as Primary Key):
- `country_dim` (`country_key` PK)
- `customers_dim` (`customer_key` PK)
- `product_dim` (`product_key` PK)

**Fact table:**
- `sales_transactions_fact` (`sales_trans_key` PK)
  - Contains all columns from `staging.sales_transactions`
  - Foreign keys: `customer_key`, `product_key`, `country_key`, referencing their respective dimension tables

## Manually Running a Single Job (optional)

```bash
docker-compose --profile jobs run from-stg-to-dwh
```

## Stopping the Project

```bash
docker-compose down
```

To also remove volumes (Postgres data):

```bash
docker-compose down -v
```
