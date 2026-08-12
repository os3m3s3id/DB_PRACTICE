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

        # 1. Finding customers whose total sales amount is greater than the average sales amount of all customers.
        result = connection.execute(
            text("""
                WITH customer_totals AS (
                    SELECT c.customer_name AS customer_name, SUM(s.total_amount::numeric) AS total_sales
                    FROM dwh.customers_dim c
                    INNER JOIN dwh.sales_transactions_fact s
                        ON c.customer_id = s.customer_id
                    GROUP BY c.customer_name
                )
                SELECT customer_name AS "Customer Name", total_sales AS "Total Sales"
                FROM customer_totals
                WHERE total_sales > (SELECT AVG(total_sales) FROM customer_totals)
            """)
        )

        rows = result.fetchall()
        for row in rows:
            print("---------------------------")
            print(f"{row[0]:<15} {float(row[1]):>10.2f}")

except Exception as error:
    print("Database connection failed:")
    print(error)