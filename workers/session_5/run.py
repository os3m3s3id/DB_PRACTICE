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

        # 1.  Create error log table.
        connection.execute(
            text("""
                DROP TABLE IF EXISTS public.error_log;
                CREATE TABLE IF NOT EXISTS public.error_log (
                    error_log_id    SERIAL PRIMARY KEY,
                    procedure_name  TEXT NOT NULL,
                    error_code      TEXT, -- This is a SQLSTATE error code
                    error_message   TEXT,
                    logged_at       TIMESTAMP DEFAULT NOW()
                );  
            """)
        )
        print("Error log table created successfully.")



        # 2.  Create LOG_ERROR procedure.
        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE public.LOG_ERROR(
                    p_procedure_name  TEXT,
                    p_error_code      TEXT,
                    p_error_message   TEXT
                )
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    INSERT INTO public.error_log (procedure_name, error_code, error_message)
                    VALUES (p_procedure_name, p_error_code, p_error_message);
                END;
                $$;  
            """)
        )
        print("LOG_ERROR procedure created successfully.")



        # 3. Create the two "package" schemas, bcz we do not have packages in postgress.
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS fullload;"))
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS merge_load;"))
        print("Schemas fullload and merge_load created successfully.")


        # 4. Move procedures created in the previous session

        move_statements = [
            "ALTER PROCEDURE LOAD_COUNTRY_DIM() SET SCHEMA fullload;",
            "ALTER PROCEDURE LOAD_CUSTOMER_DIM() SET SCHEMA fullload;",
            "ALTER PROCEDURE LOAD_PRODUCT_DIM() SET SCHEMA fullload;",
            "ALTER PROCEDURE LOAD_SALES_TRANSACTIONS_FACT() SET SCHEMA fullload;",
            "ALTER PROCEDURE MERGE_COUNTRY_DIM() SET SCHEMA merge_load;",
            "ALTER PROCEDURE MERGE_CUSTOMER_DIM() SET SCHEMA merge_load;",
            "ALTER PROCEDURE MERGE_PRODUCT_DIM() SET SCHEMA merge_load;",
            "ALTER PROCEDURE MERGE_SALES_TRANSACTIONS_FACT() SET SCHEMA merge_load;",
        ]
        for stmt in move_statements:
            connection.execute(text(stmt))
        print("All 8 procedures moved into fullload / merge_load.")


        # 5. Add exception handling (WHEN OTHERS -> LOG_ERROR) to each procedure.

        # -- Full Load procedures --

        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE fullload.LOAD_COUNTRY_DIM()
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    TRUNCATE TABLE dwh.countries_dim;

                    INSERT INTO dwh.countries_dim (country_code, country_name, region, _dlt_load_id, _dlt_id)
                    SELECT country_code, country_name, region, _dlt_load_id, _dlt_id
                    FROM staging.country;

                EXCEPTION
                    WHEN OTHERS THEN
                        CALL public.LOG_ERROR('fullload.LOAD_COUNTRY_DIM', SQLSTATE, SQLERRM);
                        RAISE;
                END;
                $$;
            """)
        )
        print("fullload.LOAD_COUNTRY_DIM updated with exception handling.")

        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE fullload.LOAD_CUSTOMER_DIM()
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    TRUNCATE TABLE dwh.customers_dim;

                    INSERT INTO dwh.customers_dim (customer_id, customer_name, country_code, customer_type, _dlt_load_id, _dlt_id)
                    SELECT customer_id, customer_name, country_code, customer_type, _dlt_load_id, _dlt_id
                    FROM staging.customer;

                EXCEPTION
                    WHEN OTHERS THEN
                        CALL public.LOG_ERROR('fullload.LOAD_CUSTOMER_DIM', SQLSTATE, SQLERRM);
                        RAISE;
                END;
                $$;
            """)
        )
        print("fullload.LOAD_CUSTOMER_DIM updated with exception handling.")

        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE fullload.LOAD_PRODUCT_DIM()
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    TRUNCATE TABLE dwh.products_dim;

                    INSERT INTO dwh.products_dim (product_id, product_name, category, standard_price, _dlt_load_id, _dlt_id)
                    SELECT product_id, product_name, category, standard_price, _dlt_load_id, _dlt_id
                    FROM staging.product;

                EXCEPTION
                    WHEN OTHERS THEN
                        CALL public.LOG_ERROR('fullload.LOAD_PRODUCT_DIM', SQLSTATE, SQLERRM);
                        RAISE;
                END;
                $$;
            """)
        )
        print("fullload.LOAD_PRODUCT_DIM updated with exception handling.")

        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE fullload.LOAD_SALES_TRANSACTIONS_FACT()
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    TRUNCATE TABLE dwh.sales_transactions_fact;

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

                EXCEPTION
                    WHEN OTHERS THEN
                        CALL public.LOG_ERROR('fullload.LOAD_SALES_TRANSACTIONS_FACT', SQLSTATE, SQLERRM);
                        RAISE;
                END;
                $$;
            """)
        )
        print("fullload.LOAD_SALES_TRANSACTIONS_FACT updated with exception handling.")

        # -- Merge procedures --

        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE merge_load.MERGE_COUNTRY_DIM()
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

                EXCEPTION
                    WHEN OTHERS THEN
                        CALL public.LOG_ERROR('merge_load.MERGE_COUNTRY_DIM', SQLSTATE, SQLERRM);
                        RAISE;
                END;
                $$;
            """)
        )
        print("merge_load.MERGE_COUNTRY_DIM updated with exception handling.")

        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE merge_load.MERGE_CUSTOMER_DIM()
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

                EXCEPTION
                    WHEN OTHERS THEN
                        CALL public.LOG_ERROR('merge_load.MERGE_CUSTOMER_DIM', SQLSTATE, SQLERRM);
                        RAISE;
                END;
                $$;
            """)
        )
        print("merge_load.MERGE_CUSTOMER_DIM updated with exception handling.")

        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE merge_load.MERGE_PRODUCT_DIM()
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

                EXCEPTION
                    WHEN OTHERS THEN
                        CALL public.LOG_ERROR('merge_load.MERGE_PRODUCT_DIM', SQLSTATE, SQLERRM);
                        RAISE;
                END;
                $$;
            """)
        )
        print("merge_load.MERGE_PRODUCT_DIM updated with exception handling.")

        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE merge_load.MERGE_SALES_TRANSACTIONS_FACT()
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

                EXCEPTION
                    WHEN OTHERS THEN
                        CALL public.LOG_ERROR('merge_load.MERGE_SALES_TRANSACTIONS_FACT', SQLSTATE, SQLERRM);
                        RAISE;
                END;
                $$;
            """)
        )
        print("merge_load.MERGE_SALES_TRANSACTIONS_FACT updated with exception handling.")

        print("\nAll 4 assignment parts complete.")

except Exception as error:
    print("Database connection failed:")
    print(error)