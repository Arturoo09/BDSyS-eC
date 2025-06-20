# CÓDIGO MODIFICADO: silver_to_gold.py

import os
import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as spark_sum, countDistinct, lit, to_date, when

def process_silver_to_gold(spark, input_path, output_path, processing_date):
    """
    Procesa datos de la capa Silver a la capa Gold.

    - Lee datos Parquet de la capa Silver de un día específico.
    - Agrega los datos para obtener métricas de negocio por producto.
    - Escribe el resultado agregado en la capa Gold, particionado por fecha.
    """
    print(f"Iniciando el procesamiento de Silver a Gold para la fecha: {processing_date}")

    pg_host = os.getenv("POSTGRES_HOST", "postgres")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db   = os.getenv("POSTGRES_DB", "ecommerce_gold")
    pg_user = os.getenv("POSTGRES_USER", "admin")
    pg_pwd  = os.getenv("POSTGRES_PASSWORD", "admin")

    db_url = f"jdbc:postgresql://{pg_host}:{pg_port}/{pg_db}"
    db_props = {
        "user": pg_user,
        "password": pg_pwd,
        "driver": "org.postgresql.Driver",
    }

    table_name = "daily_product_metrics"
    
    silver_input_path = f"{input_path}"
    print(f"Leyendo datos de la capa Silver desde: {silver_input_path}")

    df_silver = spark.read.parquet(silver_input_path)
    
    df_today = df_silver.filter(to_date(col("event_time")) == lit(processing_date))
    
    print(f"Número de eventos a procesar para la fecha {processing_date}: {df_today.count()}")

    df_gold = df_today.groupBy("product_id", "category_id", "brand").agg(
        spark_sum(when(col("event_type") == "view", 1).otherwise(0)).alias("total_views"),
        spark_sum(when(col("event_type") == "cart", 1).otherwise(0)).alias("total_carts"),
        spark_sum(when(col("event_type") == "purchase", 1).otherwise(0)).alias("total_purchases"),
        spark_sum(when(col("event_type") == "purchase", col("price")).otherwise(0)).alias("total_revenue"),
        countDistinct("user_id").alias("unique_users")
    )

    df_gold = df_gold.withColumn("processing_date", lit(processing_date))

    print("Cacheando el DataFrame Gold para escritura.")
    df_gold.cache()

    print("Esquema del DataFrame final (Gold):")
    df_gold.printSchema()

    print(f"Guardando datos agregados en la capa Gold en: {output_path}")
    df_gold.write.mode("overwrite").partitionBy("processing_date").parquet(output_path)
    
    df_gold_for_db = df_gold.drop("processing_date")
    
    print(f"Guardando datos agregados en PostgreSQL.")
    df_gold_for_db.write \
        .mode("overwrite") \
        .jdbc(url=db_url, table=table_name, properties=db_props)
    
    print(f"Datos cargados exitosamente en la tabla '{table_name}' de PostgreSQL.")

    df_gold.unpersist()

    print("Proceso de Silver a Gold completado con éxito.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-path", required=True, help="Ruta de entrada de la capa Silver.")
    parser.add_argument("--output-path", required=True, help="Ruta de salida para la capa Gold.")
    parser.add_argument("--processing-date", required=True, help="Fecha de procesamiento (YYYY-MM-DD).")
    args = parser.parse_args()

    spark = SparkSession.builder \
        .appName("SilverToGold") \
        .getOrCreate()

    process_silver_to_gold(spark, args.input_path, args.output_path, args.processing_date)

    spark.stop()