from __future__ import annotations

import pendulum
from pathlib import Path

from airflow.models import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

# =============================================================================
# CONSTANTES Y PARÁMETROS
# =============================================================================
SPARK_CONN_ID = "spark_default"
BASE_PATH = Path("/home/arturo/BDSyS-eC") 
SPARK_JOBS_PATH = BASE_PATH / "pipelines" / "spark_jobs"
DATA_ZONE = BASE_PATH / "data" 
FILE_TO_PROCESS = "2020-Apr.csv"

# =============================================================================
# DEFAULT_ARGS
# =============================================================================
default_args = {
    "owner": "data_team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}

# =============================================================================
# DEFINICIÓN DEL DAG
# =============================================================================
with DAG(
    dag_id="ecommerce_etl_pipeline_v1",
    default_args=default_args,
    description="ETL de eventos de e-commerce con Spark",
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="Europe/Madrid"),
    catchup=False,
    tags=["ecommerce", "spark"],
) as dag:

    # 1) Sensor de fichero
    wait_for_input = FileSensor(
        task_id="wait_for_input",
        fs_conn_id="fs_default",
        filepath=str(DATA_ZONE / FILE_TO_PROCESS),
        poke_interval=30,
        timeout=30 * 60,
        mode="poke",
    )

    # 2) Spark: Bronze → Silver
    bronze_to_silver = SparkSubmitOperator(
        task_id="bronze_to_silver",
        conn_id=SPARK_CONN_ID,
        application=str(SPARK_JOBS_PATH / "bronze_to_silver.py"),
        name="bronze_to_silver",
        conf={
            "spark.executor.memory": "2g"
        },
        application_args=[
            "--input-file", str(DATA_ZONE / FILE_TO_PROCESS),
            "--output-path", str(BASE_PATH / "data" / "silver"),
        ],
    )

    # 3) Spark: Silver → Gold
    silver_to_gold = SparkSubmitOperator(
        task_id="silver_to_gold",
        conn_id=SPARK_CONN_ID,
        application=str(SPARK_JOBS_PATH / "silver_to_gold.py"),
        name="silver_to_gold",
        conf={
            "spark.executor.memory": "2g"
        },
        application_args=[
            "--input-path", str(BASE_PATH / "data" / "silver"),
            "--output-path", str(BASE_PATH / "data" / "gold"),
            "--processing-date", "{{ ds }}",
        ],
    )

    # Dependencias
    wait_for_input >> bronze_to_silver >> silver_to_gold
