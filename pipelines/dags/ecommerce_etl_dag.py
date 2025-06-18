from __future__ import annotations

import pendulum

from airflow.models.dag import DAG

# =============================================================================
# DEFINICIÓN DE CONSTANTES Y PARÁMETROS
# Es una buena práctica definir aquí todas las variables que usaremos.
# =============================================================================
SPARK_CONNECTION_ID = "spark_default"
SPARK_JOBS_BASE_PATH = "/opt/airflow/projects/ecommerce_pipeline/spark_jobs" # Ruta DENTRO del entorno Airflow

# Para este ejemplo, el sensor buscará un fichero específico.
# En un caso real, esto sería dinámico.
LANDING_ZONE_PATH = "/opt/airflow/projects/ecommerce_pipeline/landing_zone"
FILE_TO_PROCESS = "2020-Apr.csv"


# =============================================================================
# ARGUMENTOS POR DEFECTO DEL DAG
# Estos argumentos se aplican a todas las tareas del DAG.
# =============================================================================
default_args = {
    "owner": "data_team",
    "start_date": pendulum.datetime(2024, 1, 1, tz="Europe/Madrid"),
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
    "catchup": False,
    "email_on_failure": False,
    "email_on_retry": False,
}


# =============================================================================
# DEFINICIÓN DEL DAG
# Aquí creamos el "plano" de nuestro pipeline.
# =============================================================================
with DAG(
    dag_id="ecommerce_etl_pipeline_v1",
    default_args=default_args,
    description="Pipeline ETL para procesar datos de eventos de e-commerce.",
    schedule=None,
    tags=["ecommerce", "spark"],
) as dag:

    # =============================================================================
    # TAREA 1: Sensor que espera por el fichero de entrada
    # Esta tarea no hace nada hasta que el fichero existe.
    # =============================================================================
    wait_for_input_file = FileSensor(
        task_id="wait_for_input_file",
        filepath=f"{LANDING_ZONE_PATH}/{FILE_TO_PROCESS}",
        poke_interval=30,  # Revisa la existencia del fichero cada 30 segundos
        timeout=60 * 30,     # Falla si el fichero no aparece en 30 minutos
        mode="poke",
    )

    # =============================================================================
    # TAREA 2: Job de Spark para procesar de Bronce a Plata
    # Esta tarea se ejecuta solo si la Tarea 1 tiene éxito.
    # =============================================================================
    submit_bronze_to_silver_job = SparkSubmitOperator(
        task_id="submit_bronze_to_silver_job",
        conn_id=SPARK_CONNECTION_ID,
        application=f"{SPARK_JOBS_BASE_PATH}/bronze_to_silver.py",
        name="ecommerce_bronze_to_silver", # Nombre que aparecerá en la UI de Spark
        application_args=[
            "--input-file", f"{LANDING_ZONE_PATH}/{FILE_TO_PROCESS}",
        ],
    )

    # =============================================================================
    # TAREA 3: Job de Spark para procesar de Plata a Oro
    # Esta tarea se ejecuta solo si la Tarea 2 tiene éxito.
    # =============================================================================
    submit_silver_to_gold_job = SparkSubmitOperator(
        task_id="submit_silver_to_gold_job",
        conn_id=SPARK_CONNECTION_ID,
        application=f"{SPARK_JOBS_BASE_PATH}/silver_to_gold.py",
        name="ecommerce_silver_to_gold",
        # Este job podría no necesitar argumentos si es capaz de detectar
        # automáticamente los últimos datos procesados en la capa Plata.
        application_args=[
            "--processing-date", "{{ ds }}", # Pasa la fecha de ejecución de Airflow
        ]
    )


    # =============================================================================
    # DEFINICIÓN DE DEPENDENCIAS
    # Aquí definimos el orden de ejecución de las tareas.
    # =============================================================================
    wait_for_input_file >> submit_bronze_to_silver_job >> submit_silver_to_gold_job