from sqlalchemy import create_engine, text


# Database connection details
DB_USER = "myuserdb"
DB_PASSWORD = "mypassdb"
DB_HOST = "postgres-db"
DB_PORT = "5432"
DB_NAME = "mydbname"


# Create database connection
engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


# Connect and run SQL
try:
    with engine.begin() as connection:
        print("Connected successfully")

        # 1. Finding the product with the highest total sales amount.
        result = connection.execute(
            text("""
                WITH customer_sales AS (
                 SELECT c.country_code AS country_name, s.total_amount::numeric AS sales_amount
                 FROM dwh.customers_dim c
                 INNER JOIN dwh.sales_transactions_fact s
                     ON c.customer_id = s.customer_id
                )
                SELECT country_name AS "CountryName", SUM(sales_amount) AS "Total Sales"
                FROM customer_sales
                GROUP BY country_name
                ORDER BY "Total Sales" DESC;
            """)
        )

        rows = result.fetchall()
        for row in rows:
            print("---------------------------")
            print(f"{row[0]:<15} {float(row[1]):>10.2f}")

except Exception as error:
    print("Database connection failed:")
    print(error)