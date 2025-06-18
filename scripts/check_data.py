from pyspark.sql import SparkSession
from pyspark.sql.utils import AnalysisException

BASE_PATH = "/home/arturo/BDSyS-eC/data"
SILVER_PATH = f"{BASE_PATH}/silver"
GOLD_PATH = f"{BASE_PATH}/gold"

def check_data():
    """
    Script para leer e inspeccionar los datos de las capas Silver y Gold.
    """
    spark = SparkSession.builder \
        .appName("DataChecker") \
        .master("local[*]") \
        .getOrCreate()

    print("="*50)
    print("INSPECCIONANDO CAPA SILVER...")
    print("="*50)
    try:
        df_silver = spark.read.parquet(SILVER_PATH)
        print(f"La tabla Silver tiene {df_silver.count()} filas.")
        print("Esquema de la tabla Silver:")
        df_silver.printSchema()
        print("Mostrando 5 filas de la tabla Silver:")
        df_silver.show(5)
    except AnalysisException as e:
        print(f"No se pudo leer la capa Silver: {e}")


    print("\n" + "="*50)
    print("INSPECCIONANDO CAPA GOLD...")
    print("="*50)
    try:
        df_gold = spark.read.parquet(GOLD_PATH)
        count = df_gold.count()
        print(f"La tabla Gold tiene {count} filas.")
        if count > 0:
            print("Esquema de la tabla Gold:")
            df_gold.printSchema()
            print("Mostrando 5 filas de la tabla Gold:")
            df_gold.show(5)
    except AnalysisException as e:
        print(f"No se pudo leer la capa Gold: {e}")

    spark.stop()


if __name__ == "__main__":
    check_data()