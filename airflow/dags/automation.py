from datetime import datetime

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator


with DAG(
    dag_id="data_pipeline_dag",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
) as dag:

    # Task 1: Load CSV files into the staging schema
    run_dlt_loading = DockerOperator(
        task_id="run_dlt_loading",
        image="dlt_loading:latest",
        docker_url="unix://var/run/docker.sock",
        network_mode="db_practice_default",
        auto_remove="success",
        mount_tmp_dir=False,
        environment={
            "DESTINATION__POSTGRES__CREDENTIALS__HOST": "postgres-db",
            "DESTINATION__POSTGRES__CREDENTIALS__PORT": "5432",
            "DESTINATION__POSTGRES__CREDENTIALS__DATABASE": "mydbname",
            "DESTINATION__POSTGRES__CREDENTIALS__USERNAME": "myuserdb",
            "DESTINATION__POSTGRES__CREDENTIALS__PASSWORD": "mypassdb",
        },
    )

    # Task 2: Transform staging tables into DWH dimension tables
    run_from_stg_to_dwh = DockerOperator(
        task_id="run_from_stg_to_dwh",
        image="from_stg_to_dwh:latest",
        docker_url="unix://var/run/docker.sock",
        network_mode="db_practice_default",
        auto_remove="success",
        mount_tmp_dir=False,
        environment={
            "POSTGRES_HOST": "postgres-db",
            "POSTGRES_PORT": "5432",
            "POSTGRES_USER": "myuserdb",
            "POSTGRES_PASSWORD": "mypassdb",
            "POSTGRES_DB": "mydbname",
        },
    )

    # DLT must finish successfully before DWH transformation starts
    run_dlt_loading >> run_from_stg_to_dwh