from __future__ import annotations

import os
from pathlib import Path
import pendulum

from airflow.models import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

PROJECT_HOME      = Path(os.getenv("PROJECT_HOME", "/opt/airflow"))
SPARK_CONN_ID     = os.getenv("SPARK_CONN_ID", "spark_local")

SPARK_DRIVER_MEM  = os.getenv("SPARK_DRIVER_MEMORY", "4g")
SPARK_EXEC_MEM    = os.getenv("SPARK_WORKER_MEMORY", "4g")

FILE_TO_PROCESS   = os.getenv("FILE_TO_PROCESS", "2020-Apr.csv")

DATA_ZONE         = PROJECT_HOME / "data"
SPARK_JOBS_PATH   = PROJECT_HOME / "pipelines" / "spark_jobs"
POSTGRES_JAR      = PROJECT_HOME / "drivers" / "postgresql-42.7.7.jar"


default_args = {
    "owner": "data_team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}

with DAG(
    dag_id="ecommerce_etl_pipeline_v1",
    default_args=default_args,
    description="ETL de eventos de e-commerce con Spark",
    schedule=None,
    start_date=pendulum.datetime(2020, 1, 1, tz="Europe/Madrid"),
    catchup=False,
    tags=["ecommerce", "spark"],
    params={"processing_date": "2020-04-01"},
) as dag:

    wait_for_input = FileSensor(
        task_id="wait_for_input",
        fs_conn_id=os.getenv("FS_CONN_ID", "fs_default"),
        filepath=str(DATA_ZONE / FILE_TO_PROCESS),
        poke_interval=30,
        timeout=30 * 60,
        mode="poke",
    )

    bronze_to_silver = SparkSubmitOperator(
        task_id="bronze_to_silver",
        conn_id=SPARK_CONN_ID,
        application=str(SPARK_JOBS_PATH / "bronze_to_silver.py"),
        name="bronze_to_silver",
        conf={
            "spark.driver.memory": SPARK_DRIVER_MEM,
            "spark.executor.memory": SPARK_EXEC_MEM,
            "spark.sql.adaptive.enabled": "true",
            "spark.sql.adaptive.coalescePartitions.enabled": "true",
        },
        application_args=[
            "--input-file", str(DATA_ZONE / FILE_TO_PROCESS),
            "--output-path", str(DATA_ZONE / "silver"),
        ],
    )

    silver_to_gold = SparkSubmitOperator(
        task_id="silver_to_gold",
        conn_id=SPARK_CONN_ID,
        application=str(SPARK_JOBS_PATH / "silver_to_gold.py"),
        name="silver_to_gold",
        conf={
            "spark.driver.memory": SPARK_DRIVER_MEM,
            "spark.executor.memory": SPARK_EXEC_MEM,
            "spark.sql.adaptive.enabled": "true",
            "spark.sql.adaptive.coalescePartitions.enabled": "true",
        },
        application_args=[
            "--input-path", str(DATA_ZONE / "silver"),
            "--output-path", str(DATA_ZONE / "gold"),
            "--processing-date", "{{ params.processing_date }}",
        ],
        jars=str(POSTGRES_JAR),
    )

    wait_for_input >> bronze_to_silver >> silver_to_gold
