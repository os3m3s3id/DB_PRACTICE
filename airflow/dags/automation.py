from datetime import datetime

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

with DAG(
    dag_id="dlt_loading_dag",
    start_date=datetime(2026, 1, 1),
    schedule=None,     
    catchup=False,
) as dag:

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