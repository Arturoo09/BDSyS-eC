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
    
    # Construir la ruta de entrada completa para los datos Silver del día
    # Asumimos que la capa Silver está particionada por fecha de evento
    # Si no es así, ajustaremos la lógica de lectura.
    # Por ahora, leemos toda la tabla Silver y filtramos.
    silver_input_path = f"{input_path}"
    print(f"Leyendo datos de la capa Silver desde: {silver_input_path}")

    df_silver = spark.read.parquet(silver_input_path)
    
    # 1. Filtrar los datos para procesar solo el día correspondiente
    df_today = df_silver.filter(to_date(col("event_time")) == lit(processing_date))
    
    print(f"Número de eventos a procesar para la fecha {processing_date}: {df_today.count()}")

    # 2. Realizar las agregaciones de negocio
    # Agrupamos por producto para obtener las métricas diarias
    df_gold = df_today.groupBy("product_id", "category_id", "brand").agg(
        # Contar vistas: sumar 1 si el tipo de evento es 'view'
        spark_sum(when(col("event_type") == "view", 1).otherwise(0)).alias("total_views"),
        
        # Contar añadidos al carrito
        spark_sum(when(col("event_type") == "cart", 1).otherwise(0)).alias("total_carts"),
        
        # Contar compras
        spark_sum(when(col("event_type") == "purchase", 1).otherwise(0)).alias("total_purchases"),
        
        # Calcular ingresos totales
        spark_sum(when(col("event_type") == "purchase", col("price")).otherwise(0)).alias("total_revenue"),
        
        # Contar usuarios únicos que interactuaron con el producto
        countDistinct("user_id").alias("unique_users")
    )

    # 3. Añadir la columna de fecha de procesamiento para particionar
    df_gold = df_gold.withColumn("processing_date", lit(processing_date))

    print("Esquema del DataFrame final (Gold):")
    df_gold.printSchema()

    # 4. Escribir el resultado en la capa Gold
    # Particionar por 'processing_date' es una práctica clave.
    # Crea una estructura de carpetas como /gold/processing_date=2025-06-18/
    # Esto hace que las consultas futuras sobre fechas específicas sean extremadamente rápidas.
    print(f"Guardando datos agregados en la capa Gold en: {output_path}")
    df_gold.write.mode("overwrite").partitionBy("processing_date").parquet(output_path)

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