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

        # 1.  Create Execution Control & Audit Logging table.
        connection.execute(
            text(
                """
                CREATE SCHEMA IF NOT EXISTS audit;
                DROP TABLE IF EXISTS audit.execution_log;
                CREATE TABLE audit.execution_log (
                    log_id          SERIAL PRIMARY KEY,
                    procedure_name  TEXT NOT NULL,
                    start_time      TIMESTAMP NOT NULL DEFAULT clock_timestamp(),
                    end_time        TIMESTAMP,
                    duration_ms     NUMERIC,
                    rows_affected   INTEGER,
                    status          TEXT,
                    run_date        DATE NOT NULL DEFAULT CURRENT_DATE
                );
                """
            
            )
        )
        print("Execution Control & Audit Logging table created successfully.")



        # 2. Update fullload.LOAD_COUNTRY_DIM with execution logging.
        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE fullload.LOAD_COUNTRY_DIM()
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_start TIMESTAMP := clock_timestamp();
                BEGIN
                    TRUNCATE TABLE dwh.countries_dim;

                    INSERT INTO dwh.countries_dim (country_code, country_name, region, _dlt_load_id, _dlt_id)
                    SELECT country_code, country_name, region, _dlt_load_id, _dlt_id
                    FROM staging.country;

                    INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                    VALUES ('fullload.LOAD_COUNTRY_DIM', v_start, clock_timestamp(), 'SUCCESS');

                EXCEPTION
                    WHEN OTHERS THEN
                        INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                        VALUES ('fullload.LOAD_COUNTRY_DIM', v_start, clock_timestamp(), 'FAILED');

                        CALL public.LOG_ERROR('fullload.LOAD_COUNTRY_DIM', SQLSTATE, SQLERRM);
                END;
                $$;
            """)
        )
        print("fullload.LOAD_COUNTRY_DIM updated with execution logging.")



        # 3. Update fullload.LOAD_CUSTOMER_DIM with execution logging.
        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE fullload.LOAD_CUSTOMER_DIM()
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_start TIMESTAMP := clock_timestamp();
                BEGIN
                    TRUNCATE TABLE dwh.customers_dim;

                    INSERT INTO dwh.customers_dim (customer_id, customer_name, country_code, customer_type, _dlt_load_id, _dlt_id)
                    SELECT customer_id, customer_name, country_code, customer_type, _dlt_load_id, _dlt_id
                    FROM staging.customer;

                    INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                    VALUES ('fullload.LOAD_CUSTOMER_DIM', v_start, clock_timestamp(), 'SUCCESS');

                EXCEPTION
                    WHEN OTHERS THEN
                        INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                        VALUES ('fullload.LOAD_CUSTOMER_DIM', v_start, clock_timestamp(), 'FAILED');

                        CALL public.LOG_ERROR('fullload.LOAD_CUSTOMER_DIM', SQLSTATE, SQLERRM);
                END;
                $$;
            """)
        )
        print("fullload.LOAD_CUSTOMER_DIM updated with execution logging.")




        # 4. Update fullload.LOAD_PRODUCT_DIM with execution logging.
        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE fullload.LOAD_PRODUCT_DIM()
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_start TIMESTAMP := clock_timestamp();
                BEGIN
                    TRUNCATE TABLE dwh.products_dim;

                    INSERT INTO dwh.products_dim (product_id, product_name, category, standard_price, _dlt_load_id, _dlt_id)
                    SELECT product_id, product_name, category, standard_price, _dlt_load_id, _dlt_id
                    FROM staging.product;

                    INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                    VALUES ('fullload.LOAD_PRODUCT_DIM', v_start, clock_timestamp(), 'SUCCESS');

                EXCEPTION
                    WHEN OTHERS THEN
                        INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                        VALUES ('fullload.LOAD_PRODUCT_DIM', v_start, clock_timestamp(), 'FAILED');

                        CALL public.LOG_ERROR('fullload.LOAD_PRODUCT_DIM', SQLSTATE, SQLERRM);
                END;
                $$;
            """)
        )
        print("fullload.LOAD_PRODUCT_DIM updated with execution logging.")


        # 5. Update fullload.LOAD_SALES_TRANSACTIONS_FACT with execution logging.
        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE fullload.LOAD_SALES_TRANSACTIONS_FACT()
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_start TIMESTAMP := clock_timestamp();
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

                    INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                    VALUES ('fullload.LOAD_SALES_TRANSACTIONS_FACT', v_start, clock_timestamp(), 'SUCCESS');

                EXCEPTION
                    WHEN OTHERS THEN
                        INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                        VALUES ('fullload.LOAD_SALES_TRANSACTIONS_FACT', v_start, clock_timestamp(), 'FAILED');

                        CALL public.LOG_ERROR('fullload.LOAD_SALES_TRANSACTIONS_FACT', SQLSTATE, SQLERRM);
                END;
                $$;
            """)
        )
        print("fullload.LOAD_SALES_TRANSACTIONS_FACT updated with execution logging.")


        # 6. Update merge_load.MERGE_COUNTRY_DIM with execution logging.
        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE merge_load.MERGE_COUNTRY_DIM()
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_start TIMESTAMP := clock_timestamp();
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

                    INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                    VALUES ('merge_load.MERGE_COUNTRY_DIM', v_start, clock_timestamp(), 'SUCCESS');

                EXCEPTION
                    WHEN OTHERS THEN
                        INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                        VALUES ('merge_load.MERGE_COUNTRY_DIM', v_start, clock_timestamp(), 'FAILED');

                        CALL public.LOG_ERROR('merge_load.MERGE_COUNTRY_DIM', SQLSTATE, SQLERRM);
                END;
                $$;
            """)
        )
        print("merge_load.MERGE_COUNTRY_DIM updated with execution logging.")


        # 7. Update merge_load.MERGE_CUSTOMER_DIM with execution logging.
        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE merge_load.MERGE_CUSTOMER_DIM()
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_start TIMESTAMP := clock_timestamp();
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

                    INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                    VALUES ('merge_load.MERGE_CUSTOMER_DIM', v_start, clock_timestamp(), 'SUCCESS');

                EXCEPTION
                    WHEN OTHERS THEN
                        INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                        VALUES ('merge_load.MERGE_CUSTOMER_DIM', v_start, clock_timestamp(), 'FAILED');

                        CALL public.LOG_ERROR('merge_load.MERGE_CUSTOMER_DIM', SQLSTATE, SQLERRM);
                END;
                $$;
            """)
        )
        print("merge_load.MERGE_CUSTOMER_DIM updated with execution logging.")


        # 8. Update merge_load.MERGE_PRODUCT_DIM with execution logging.
        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE merge_load.MERGE_PRODUCT_DIM()
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_start TIMESTAMP := clock_timestamp();
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

                    INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                    VALUES ('merge_load.MERGE_PRODUCT_DIM', v_start, clock_timestamp(), 'SUCCESS');

                EXCEPTION
                    WHEN OTHERS THEN
                        INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                        VALUES ('merge_load.MERGE_PRODUCT_DIM', v_start, clock_timestamp(), 'FAILED');

                        CALL public.LOG_ERROR('merge_load.MERGE_PRODUCT_DIM', SQLSTATE, SQLERRM);
                END;
                $$;
            """)
        )
        print("merge_load.MERGE_PRODUCT_DIM updated with execution logging.")


        # 9. Update merge_load.MERGE_SALES_TRANSACTIONS_FACT with execution logging.
        connection.execute(
            text("""
                CREATE OR REPLACE PROCEDURE merge_load.MERGE_SALES_TRANSACTIONS_FACT()
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_start TIMESTAMP := clock_timestamp();
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

                    INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                    VALUES ('merge_load.MERGE_SALES_TRANSACTIONS_FACT', v_start, clock_timestamp(), 'SUCCESS');

                EXCEPTION
                    WHEN OTHERS THEN
                        INSERT INTO audit.execution_log (procedure_name, start_time, end_time, status)
                        VALUES ('merge_load.MERGE_SALES_TRANSACTIONS_FACT', v_start, clock_timestamp(), 'FAILED');

                        CALL public.LOG_ERROR('merge_load.MERGE_SALES_TRANSACTIONS_FACT', SQLSTATE, SQLERRM);
                END;
                $$;
            """)
        )
        print("merge_load.MERGE_SALES_TRANSACTIONS_FACT updated with execution logging.")



       # 10. Query: Total sales per country using an analytic function (no GROUP BY).
        result = connection.execute(
            text("""
                SELECT DISTINCT c.country_name, SUM(f.total_amount::numeric) OVER (PARTITION BY c.country_name) AS total_sales
                FROM dwh.sales_transactions_fact f
                JOIN dwh.countries_dim c ON f.country_key = c.country_key
                ORDER BY total_sales DESC;
            """)
        )

        for row in result:
            print(row)
        print("------------------------")



        # 11. Query: Rank countries based on total sales.
        result = connection.execute(
            text("""
                SELECT country_name, total_sales, RANK() OVER (ORDER BY total_sales DESC) AS sales_rank
                FROM (SELECT DISTINCT c.country_name, SUM(f.total_amount::numeric) OVER (PARTITION BY c.country_name) AS total_sales
                    FROM dwh.sales_transactions_fact f
                    JOIN dwh.countries_dim c ON f.country_key = c.country_key
                ) t
                ORDER BY sales_rank;
            """)
        )

        for row in result:
            print(row)
        print("------------------------")



        # 12. Query: Highest sale transaction in each country.
        result = connection.execute(
            text("""
                SELECT country_name, total_amount, transaction_id
                FROM (SELECT c.country_name, f.total_amount::numeric AS total_amount, f.transaction_id, RANK() OVER (PARTITION BY c.country_name ORDER BY f.total_amount::numeric DESC) AS rnk
                    FROM dwh.sales_transactions_fact f
                    JOIN dwh.countries_dim c ON f.country_key = c.country_key
                ) t
                WHERE rnk = 1;
            """)
        )
        for row in result:
            print(row)
        print("------------------------")



        # 13. Query: Top 2 customers per country.
        result = connection.execute(
            text("""
                SELECT country_name, customer_name, total_spent
                FROM (SELECT c.country_name, cu.customer_name, SUM(f.total_amount::numeric) AS total_spent, DENSE_RANK() OVER (PARTITION BY c.country_name ORDER BY SUM(f.total_amount::numeric) DESC) AS rnk
                    FROM dwh.sales_transactions_fact f
                    JOIN dwh.countries_dim c ON f.country_key = c.country_key
                    JOIN dwh.customers_dim cu ON f.customer_key = cu.customer_key
                    GROUP BY c.country_name, cu.customer_name
                ) t
                WHERE rnk <= 2;
            """)
        )

        for row in result:
            print(row)  
        print("------------------------")



        # 14. Query: Total sales per product.
        result = connection.execute(
            text("""
                SELECT p.product_name, SUM(f.total_amount::numeric) AS total_sales
                FROM dwh.sales_transactions_fact f
                JOIN dwh.products_dim p ON f.product_key = p.product_key
                GROUP BY p.product_name
                ORDER BY total_sales DESC;
            """)
        )
        for row in result:
            print(row)
        print("------------------------")
        


        # 15. Query: Most sold product in each country (by quantity).
        result = connection.execute(
            text("""
                SELECT country_name, product_name, total_qty
                FROM (SELECT c.country_name, p.product_name, SUM(f.quantity::numeric) AS total_qty, RANK() OVER (PARTITION BY c.country_name ORDER BY SUM(f.quantity::numeric) DESC) AS rnk
                    FROM dwh.sales_transactions_fact f
                    JOIN dwh.countries_dim c ON f.country_key = c.country_key
                    JOIN dwh.products_dim p ON f.product_key = p.product_key
                    GROUP BY c.country_name, p.product_name
                ) t
                WHERE rnk = 1;
            """)
        )
        for row in result:
            print(row)
        print("------------------------")

except Exception as error:
    print("Database connection failed:")
    print(error)