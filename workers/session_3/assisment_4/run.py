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
                SELECT c.customer_name AS "Customer Name", COUNT(s.transaction_id) AS "Number Of Purchase"
                FROM dwh.customers_dim c
                INNER JOIN dwh.sales_transactions_fact s
                    ON c.customer_id = s.customer_id
                GROUP BY c.customer_id, c.customer_name
                HAVING COUNT(s.transaction_id) > 5
                ORDER BY "Number Of Purchase" DESC;
            """)
        )

        rows = result.fetchall()
        for row in rows:
            print("---------------------------")
            print(f"{row[0]:<15} {float(row[1]):>10.2f}")

except Exception as error:
    print("Database connection failed:")
    print(error)