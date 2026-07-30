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

        # 1. Command to create the dwh schema if not exists
        connection.execute(
            text("CREATE SCHEMA IF NOT EXISTS dwh;")
        )


        # 2. Adding the customer table with the new surrogate key column
        connection.execute(
            text("""
                DROP TABLE IF EXISTS dwh.customers_dim;
                CREATE TABLE dwh.customers_dim AS
                SELECT * FROM staging.customer;
                ALTER TABLE dwh.customers_dim
                ADD COLUMN customer_key SERIAL PRIMARY KEY;
            """)
        )


        # 2. Adding the country table with the new surrogate key column
        connection.execute(
            text("""
                DROP TABLE IF EXISTS dwh.countries_dim;
                CREATE TABLE dwh.countries_dim AS
                SELECT * FROM staging.country;
                ALTER TABLE dwh.countries_dim
                ADD COLUMN country_key SERIAL PRIMARY KEY;
            """)
        )


except Exception as error:
    print("Database connection failed:")
    print(error)