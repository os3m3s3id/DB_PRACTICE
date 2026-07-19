import csv
import dlt
from dotenv import load_dotenv

load_dotenv()

# Path defining
customer_file_path = "data/customer.csv"
country_file_path = "data/country.csv"
product_file_path = "data/product.csv"
sales_transactions_file_path = "data/sales_transactions.csv"



# CSV's Reading
def read_customers():
    with open(customer_file_path, mode="r", encoding="utf-8-sig") as file:
        yield from csv.DictReader(file)


def read_country():
    with open(country_file_path, mode="r", encoding="utf-8-sig") as file:
        yield from csv.DictReader(file)


def read_product():
    with open (product_file_path, mode="r", encoding="utf-8-sig") as file:
         yield from csv.DictReader(file)


def read_sales_transactions():
    with open (sales_transactions_file_path, mode='r', encoding="utf-8-sig") as file:
        yield from csv.DictReader(file)


pipeline = dlt.pipeline(
    pipeline_name="csv_to_postgres",
    destination="postgres",
    dataset_name="staging"
)



# Load the tables:
customers_load = pipeline.run(
    read_customers(),
    table_name="customer",
    write_disposition="replace"
)

country_load = pipeline.run(
    read_country(),
    table_name="country",
    write_disposition="replace"
)

product_load = pipeline.run(
    read_product(),
    table_name="product",
    write_disposition="replace"
)

sales_transactions_load = pipeline.run(
    read_sales_transactions(),
    table_name="sales_transactions",
    write_disposition="replace"
)



print(customers_load)
print(country_load)
print(product_load)
print(sales_transactions_load)