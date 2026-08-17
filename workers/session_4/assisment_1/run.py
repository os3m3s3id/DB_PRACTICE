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

        # 1.  Create procedure to load COUNTRY_DIM.
        connection.execute(
            text("""
                CREATE PROCEDURE LOAD_COUNTRY_DIM()
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    -- Step 1: Trancate the table
                    TRUNCATE TABLE dwh.countries_dim;

                    -- Step 2: Trancate the table
                    INSERT INTO dwh.countries_dim (country_code, country_name, region, _dlt_load_id, _dlt_id)
                    SELECT country_code, country_name, region, _dlt_load_id, _dlt_id
                    FROM staging.country;

                    -- Step 3: Commit the transaction
                    COMMIT;
                END;
                $$;   
            """)
        )
        print("Procedure LOAD_COUNTRY_DIM created successfully.")



        # 2.  Create procedure to load CUSTOMER_DIM.
        connection.execute(
            text("""
                CREATE PROCEDURE LOAD_CUSTOMER_DIM()
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    -- Step 1: Trancate the table
                    TRUNCATE TABLE dwh.customers_dim;

                    -- Step 2: Trancate the table
                    INSERT INTO dwh.customers_dim (customer_id, customer_name, country_code, customer_type, _dlt_load_id, _dlt_id)
                    SELECT customer_id, customer_name, country_code, customer_type, _dlt_load_id, _dlt_id
                    FROM staging.customer;

                    -- Step 3: Commit the transaction
                    COMMIT;
                END;
                $$;   
            """)
        )
        print("Procedure LOAD_CUSTOMER_DIM created successfully.")


        # 3. Create procedure to load PRODUCT_DIM.
        connection.execute(
            text("""
                CREATE PROCEDURE LOAD_PRODUCT_DIM()
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    -- Step 1: Trancate the table
                    TRUNCATE TABLE dwh.products_dim;

                    -- Step 2: Trancate the table
                    INSERT INTO dwh.products_dim (product_id, product_name, category, standard_price, _dlt_load_id, _dlt_id)
                    SELECT product_id, product_name, category, standard_price, _dlt_load_id, _dlt_id
                    FROM staging.product;

                    -- Step 3: Commit the transaction
                    COMMIT;
                END;
                $$;   
            """)
        )
        print("Procedure LOAD_PRODUCT_DIM created successfully.")


        # 4. Create procedure to load SALES_TRANSACTIONS_FACT.
        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE LOAD_SALES_TRANSACTIONS_FACT()
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    -- Step 1: Truncate the table
                    TRUNCATE TABLE dwh.sales_transactions_fact;
 
                    -- Step 2: Insert data from staging table (with dimension key lookups)
                    INSERT INTO dwh.sales_transactions_fact (
                        transaction_id, transaction_date, customer_id, product_id,
                        quantity, unit_price, total_amount, payment_mode,
                        _dlt_load_id, _dlt_id, customer_key, product_key, country_key
                    )
                    SELECT
                        st.transaction_id, st.transaction_date, st.customer_id, st.product_id,
                        st.quantity, st.unit_price, st.total_amount, st.payment_mode,
                        st._dlt_load_id, st._dlt_id, cu.customer_key, pr.product_key, co.country_key
                    FROM staging.sales_transactions st
                    LEFT JOIN dwh.customers_dim cu ON st.customer_id = cu.customer_id
                    LEFT JOIN dwh.products_dim pr ON st.product_id = pr.product_id
                    LEFT JOIN dwh.countries_dim co ON cu.country_code = co.country_code;
 
                    -- Step 3: Commit the transaction
                    COMMIT;
                END;
                $$;
            """)
        )
        print("Procedure LOAD_SALES_TRANSACTIONS_FACT created successfully.")

except Exception as error:
    print("Database connection failed:")
    print(error)