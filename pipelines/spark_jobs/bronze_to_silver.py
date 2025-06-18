import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp

def process_bronze_to_silver(spark, input_file, output_path):
    """
    Procesa los datos de la capa Bronze a la capa Silver.

    - Lee datos de un fichero CSV.
    - Convierte la columna 'event_time' a formato timestamp.
    - Elimina filas donde 'event_time' o 'user_id' sean nulos.
    - Escribe el resultado en formato Parquet.
    """
    print(f"Iniciando el procesamiento de Bronze a Silver para el archivo: {input_file}")

    # 1. Leer el archivo CSV de la capa Bronze
    # inferSchema intenta adivinar los tipos de datos, header=True usa la primera fila como nombres de columna
    df_bronze = spark.read.csv(input_file, header=True, inferSchema=True)

    print("Esquema del DataFrame leído (Bronze):")
    df_bronze.printSchema()

    # 2. Transformación de los datos
    
    # Convertir la columna 'event_time' de String a Timestamp
    # Asumimos que el formato es como '2020-04-01 00:00:00 UTC'
    df_transformed = df_bronze.withColumn("event_time", to_timestamp(col("event_time")))

    # Filtrar filas con valores nulos en columnas clave
    df_cleaned = df_transformed.dropna(subset=["event_time", "user_id"])

    print(f"Número de filas antes de la limpieza: {df_bronze.count()}")
    print(f"Número de filas después de la limpieza: {df_cleaned.count()}")

    # 3. Escribir el DataFrame limpio en la capa Silver en formato Parquet
    # El modo 'overwrite' reemplazará los datos si ya existen
    print(f"Guardando los datos procesados en la capa Silver en: {output_path}")
    df_cleaned.write.mode("overwrite").parquet(output_path)
    
    print("Proceso de Bronze a Silver completado con éxito.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", required=True, help="Ruta del fichero de entrada en la capa Bronze.")
    parser.add_argument("--output-path", required=True, help="Ruta de salida para los datos en la capa Silver.")
    args = parser.parse_args()

    # Creación de la sesión de Spark
    spark = SparkSession.builder \
        .appName("BronzeToSilver") \
        .getOrCreate()

    # Llamada a la función principal de procesamiento
    process_bronze_to_silver(spark, args.input_file, args.output_path)

    # Detener la sesión de Spark
    spark.stop()