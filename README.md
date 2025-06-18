# 📊 Análisis y Pipeline ETL de Datos de E-commerce
Este proyecto presenta una solución completa para el análisis y procesamiento de un gran volumen de datos de eventos de un sitio de comercio electrónico. Incluye un **Análisis Exploratorio de Datos (EDA)** para extraer insights iniciales y un **pipeline ETL** automatizado con **Airflow** y **Spark** que implementa una **arquitectura Medallion** (Bronze, Silver, Gold) para transformar los datos crudos en métricas de negocio agregadas y listas para el análisis.

## 🧱 Arquitectura del Proyecto
El pipeline de datos sigue la Arquitectura Medallion para asegurar la calidad, gobernanza y escalabilidad de los datos a través de diferentes capas de procesamiento.

1. **Capa Bronze (Datos Crudos)**
    - **Fuente:** Los datos crudos en formato CSV (2020-Apr.csv) se ingieren en esta capa sin ninguna modificación.
    - **Propósito:** Almacenar los datos originales como una fuente de verdad histórica, permitiendo reprocesar el pipeline desde el inicio si es necesario.
2. **Capa Silver (Datos Limpios y Estructurados)**
    - **Proceso:** El job de Spark bronze_to_silver.py se encarga de la transformación.
    - **Transformaciones Clave:**
        - **Lectura de datos:** Ingesta del fichero CSV.
        - **Limpieza:** Se eliminan filas con valores nulos en columnas críticas como event_time y user_id.
        - **Normalización:** La columna event_time se convierte a un formato timestamp estándar para facilitar los análisis de series temporales.
    - **Formato de Salida:** Los datos limpios se almacenan en formato Parquet, que es altamente eficiente para consultas analíticas.
3. **Capa Gold (Datos Agregados y de Negocio)**
    - **Proceso:** El job de Spark silver_to_gold.py consume los datos de la capa Silver.
    - **Transformaciones Clave:**
        - **Filtrado**: Procesa los eventos correspondientes a una fecha específica (processing_date).
        - **Agregación:** Agrupa los datos por product_id, category_id y brand para calcular métricas diarias de negocio.
        - **Métricas Calculadas:**
            - **Vistas totales (total_views).**
            - **Añadidos al carrito (total_carts).**
            - **Compras totales (total_purchases).**
            - **Ingresos totales (total_revenue).**
            - **Conteo de usuarios únicos (unique_users).**
    - **Formato de Salida:** Los datos agregados se guardan en formato Parquet y se particionan por fecha (processing_date) para optimizar las consultas.
## 🔎 Análisis Exploratorio de Datos (EDA)
El notebook notebooks/data_analysis.ipynb revela varios insights clave sobre el comportamiento de los usuarios en abril de 2020:

- **Distribución de Eventos:** La gran mayoría de los eventos son de tipo view (93.1%), seguido por cart (5.2%) y purchase (1.7%).
- **Marcas y Categorías Populares:**
    - Las marcas Samsung y Apple dominan en términos de interacciones de los usuarios.
    - Las categorías principales con más eventos son electronics, appliances y computers.
- **Actividad por Hora:** La actividad de los usuarios alcanza su punto máximo durante las horas de la tarde, entre las 12:00 y las 16:00 (UTC).
- **Funnel de Conversión:**
    - La tasa de conversión de vista a carrito es del 5.57%.
    - La tasa de conversión de carrito a compra es notablemente alta, con un 33.07%.
    - La tasa de conversión general (de vista a compra) es del 1.84%. Esto sugiere que el mayor desafío es incentivar a los usuarios para que añadan productos al carrito.

## 📁 Estructura del Repositorio
```plaintext
.
├── notebooks/
│   └── data_analysis.ipynb      # EDA y análisis de datos en profundidad.
├── pipelines/
│   ├── config/
│   │   └── pipeline_config.yaml   # (Opcional) Configuración de rutas.
│   ├── dags/
│   │   └── ecommerce_etl_dag.py   # Definición del DAG de Airflow.
│   └── spark_jobs/
│       ├── bronze_to_silver.py  # Script de Spark para la capa Silver.
│       └── silver_to_gold.py    # Script de Spark para la capa Gold.
├── scripts/
│   └── check_data.py            # Script para verificar los datos en las capas Silver y Gold.
├── .gitignore
└── pyproject.toml               # Dependencias y configuración del proyecto.
```

## 🚩 Requisitos Previos
Python >= 3.11
Apache Airflow
Apache Spark
Una cuenta de Kaggle con el fichero kaggle.json configurado (para descargar el dataset).

## ⚙️ Instalación y Configuración
1. Clonar el repositorio:
```sh
git clone <URL-DEL-REPOSITORIO>
cd bdsys-ec
```
2. Crear un entorno virtual e instalar dependencias:
> Se recomienda usar un entorno virtual para gestionar las dependencias del proyecto.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -e .
```
Esto instalará todos los paquetes listados en pyproject.toml.

3. Configurar el dataset:
> El pipeline espera el dataset en el directorio data/. Como este directorio está excluido por .gitignore, debes crearlo y descargar los datos.
```sh
mkdir data
# Descarga el dataset de e-commerce de Kaggle
# (Asegúrate de tener tu API token de Kaggle configurado)
kaggle datasets download -d mkechinov/ecommerce-events-history-in-cosmetics-shop -f 2020-Apr.csv -p data/
```

4. Configurar Airflow:
   
- Asegúrate de que tu instancia de Airflow esté en funcionamiento.
- Copia el DAG *pipelines/dags/ecommerce_etl_dag.py* a tu carpeta de DAGs de Airflow.
- En la UI de Airflow, configura las conexiones necesarias:
    - **fs_default:** Una conexión de tipo "File Path" que apunte al directorio raíz del proyecto (/home/arturo/BDSyS-eC).
    - **spark_default:** Una conexión de tipo "Spark" que apunte a tu clúster de Spark.


## 🚀 Cómo Ejecutar el Pipeline
1. **Activa el DAG:** En la UI de Airflow, busca el DAG ecommerce_etl_pipeline_v1 y actívalo.
2. **Dispara el Pipeline:** Puedes disparar el DAG manualmente. Por defecto, procesará la fecha 2020-01-01, pero puedes modificarla en los parámetros de configuración al ejecutarlo ("processing_date": "YYYY-MM-DD").
3. **Monitorea la Ejecución:** Sigue el progreso de las tareas en la vista de grafo de Airflow.
    - wait_for_input: Espera a que el fichero 2020-Apr.csv esté disponible.
    - bronze_to_silver: Procesa los datos crudos a la capa Silver.
    - silver_to_gold: Procesa los datos de Silver a la capa Gold.

## ✅ Cómo Verificar los Datos
Una vez que el pipeline se haya ejecutado correctamente, puedes usar el script de verificación para inspeccionar los datos en las capas Silver y Gold.

```sh
spark-submit scripts/check_data.py
```

El script mostrará el conteo de filas, el esquema y las primeras 5 filas de cada tabla, confirmando que los datos se han procesado y almacenado correctamente.

## Próximos Pasos
Este proyecto sienta las bases para análisis más avanzados. Los próximos pasos sugeridos incluyen:

1. **Análisis de Cohortes:** Para entender el comportamiento del usuario a lo largo del tiempo y calcular el LTV.
2. **Market Basket Analysis:** Para identificar qué productos se compran juntos con frecuencia.
3. **Segmentación de Clientes (RFM):** Para personalizar campañas de marketing.
4. **Sistemas de Recomendación:** Para sugerir productos a los usuarios.
5. **Análisis de Elasticidad de Precios:** Para entender cómo el precio afecta la probabilidad de compra.