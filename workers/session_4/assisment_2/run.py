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

        # 1. Create MERGE procedure for COUNTRY_DIM
        # Business key: country_code
        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE MERGE_COUNTRY_DIM()
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    MERGE INTO dwh.countries_dim AS target
                    USING staging.country AS source
                    ON target.country_code = source.country_code

                    WHEN MATCHED THEN
                        UPDATE SET
                            country_name = source.country_name,
                            region = source.region,
                            _dlt_load_id = source._dlt_load_id,
                            _dlt_id = source._dlt_id

                    WHEN NOT MATCHED THEN
                        INSERT (country_code, country_name, region, _dlt_load_id, _dlt_id)
                        VALUES (source.country_code, source.country_name, source.region, source._dlt_load_id, source._dlt_id);

                    COMMIT;
                END;
                $$;
            """)
        )
        print("Procedure MERGE_COUNTRY_DIM created successfully.")

        # 2. Create MERGE procedure for CUSTOMER_DIM
        # Business key: customer_id
        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE MERGE_CUSTOMER_DIM()
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    MERGE INTO dwh.customers_dim AS target
                    USING staging.customer AS source
                    ON target.customer_id = source.customer_id

                    WHEN MATCHED THEN
                        UPDATE SET
                            customer_name = source.customer_name,
                            country_code = source.country_code,
                            customer_type = source.customer_type,
                            _dlt_load_id = source._dlt_load_id,
                            _dlt_id = source._dlt_id

                    WHEN NOT MATCHED THEN
                        INSERT (customer_id, customer_name, country_code, customer_type, _dlt_load_id, _dlt_id)
                        VALUES (source.customer_id, source.customer_name, source.country_code, source.customer_type, source._dlt_load_id, source._dlt_id);

                    COMMIT;
                END;
                $$;
            """)
        )
        print("Procedure MERGE_CUSTOMER_DIM created successfully.")

        # 3. Create MERGE procedure for PRODUCT_DIM
        # Business key: product_id
        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE MERGE_PRODUCT_DIM()
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    MERGE INTO dwh.products_dim AS target
                    USING staging.product AS source
                    ON target.product_id = source.product_id

                    WHEN MATCHED THEN
                        UPDATE SET
                            product_name = source.product_name,
                            category = source.category,
                            standard_price = source.standard_price,
                            _dlt_load_id = source._dlt_load_id,
                            _dlt_id = source._dlt_id

                    WHEN NOT MATCHED THEN
                        INSERT (product_id, product_name, category, standard_price, _dlt_load_id, _dlt_id)
                        VALUES (source.product_id, source.product_name, source.category, source.standard_price, source._dlt_load_id, source._dlt_id);

                    COMMIT;
                END;
                $$;
            """)
        )
        print("Procedure MERGE_PRODUCT_DIM created successfully.")

        # 4. Create MERGE procedure for SALES_TRANSACTIONS_FACT
        # Business key: transaction_id
        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE MERGE_SALES_TRANSACTIONS_FACT()
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    MERGE INTO dwh.sales_transactions_fact AS target
                    USING (
                        SELECT
                            st.transaction_id, st.transaction_date, st.customer_id, st.product_id,
                            st.quantity, st.unit_price, st.total_amount, st.payment_mode,
                            st._dlt_load_id, st._dlt_id, cu.customer_key, pr.product_key, co.country_key
                        FROM staging.sales_transactions st
                        LEFT JOIN dwh.customers_dim cu ON st.customer_id = cu.customer_id
                        LEFT JOIN dwh.products_dim pr ON st.product_id = pr.product_id
                        LEFT JOIN dwh.countries_dim co ON cu.country_code = co.country_code
                    ) AS source
                    ON target.transaction_id = source.transaction_id

                    WHEN MATCHED THEN
                        UPDATE SET
                            transaction_date = source.transaction_date,
                            customer_id = source.customer_id,
                            product_id = source.product_id,
                            quantity = source.quantity,
                            unit_price = source.unit_price,
                            total_amount = source.total_amount,
                            payment_mode = source.payment_mode,
                            _dlt_load_id = source._dlt_load_id,
                            _dlt_id = source._dlt_id,
                            customer_key = source.customer_key,
                            product_key = source.product_key,
                            country_key = source.country_key

                    WHEN NOT MATCHED THEN
                        INSERT (
                            transaction_id, transaction_date, customer_id, product_id,
                            quantity, unit_price, total_amount, payment_mode,
                            _dlt_load_id, _dlt_id, customer_key, product_key, country_key
                        )
                        VALUES (
                            source.transaction_id, source.transaction_date, source.customer_id, source.product_id,
                            source.quantity, source.unit_price, source.total_amount, source.payment_mode,
                            source._dlt_load_id, source._dlt_id, source.customer_key, source.product_key, source.country_key
                        );

                    COMMIT;
                END;
                $$;
            """)
        )
        print("Procedure MERGE_SALES_TRANSACTIONS_FACT created successfully.")

except Exception as error:
    print("Database connection failed:")
    print(error)