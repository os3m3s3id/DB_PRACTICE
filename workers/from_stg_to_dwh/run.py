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


        # 3. Adding the country table with the new surrogate key column
        connection.execute(
            text("""
                DROP TABLE IF EXISTS dwh.countries_dim;
                CREATE TABLE dwh.countries_dim AS
                SELECT * FROM staging.country;
                ALTER TABLE dwh.countries_dim
                ADD COLUMN country_key SERIAL PRIMARY KEY;
            """)
        )



        # 3. Adding the product table with the new surrogate key column
        connection.execute(
            text("""
                DROP TABLE IF EXISTS dwh.products_dim;
                CREATE TABLE dwh.products_dim AS
                SELECT * FROM staging.product;
                ALTER TABLE dwh.products_dim
                ADD COLUMN product_key SERIAL PRIMARY KEY;
            """)
        )




        # 4. Adding the sales_transactions fact table
        connection.execute(
            text("""
                DROP TABLE IF EXISTS dwh.sales_transactions_fact;
                CREATE TABLE dwh.sales_transactions_fact AS
                SELECT
                    st.*,
                    cu.customer_key,
                    pr.product_key,
                    co.country_key
                FROM staging.sales_transactions st
                LEFT JOIN dwh.customers_dim cu ON st.customer_id = cu.customer_id
                LEFT JOIN dwh.products_dim pr ON st.product_id = pr.product_id
                LEFT JOIN dwh.countries_dim co ON cu.country_code = co.country_code;

                ALTER TABLE dwh.sales_transactions_fact
                ADD COLUMN sales_trans_key SERIAL PRIMARY KEY;

                ALTER TABLE dwh.sales_transactions_fact
                ADD CONSTRAINT fk_customer FOREIGN KEY (customer_key) REFERENCES dwh.customers_dim (customer_key);

                ALTER TABLE dwh.sales_transactions_fact
                ADD CONSTRAINT fk_product FOREIGN KEY (product_key) REFERENCES dwh.products_dim (product_key);

                ALTER TABLE dwh.sales_transactions_fact
                ADD CONSTRAINT fk_country FOREIGN KEY (country_key) REFERENCES dwh.countries_dim (country_key);
            """)
        )

        
except Exception as error:
    print("Database connection failed:")
    print(error)