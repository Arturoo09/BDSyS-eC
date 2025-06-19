# =============================================================================
# VARIABLES DE CONFIGURACIÓN
# =============================================================================

VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
UV := $(VENV_DIR)/bin/uv
KAGGLE := $(VENV_DIR)/bin/kaggle
DATA_DIR := data
KAGGLE_DATASET_ID := mkechinov/ecommerce-behavior-data-from-multi-category-store

CUR_DIR := $(shell pwd)
ENV_FILE := $(CUR_DIR)/.env 
DOCKER_DIR := docker
DOCKER_FILES := $(wildcard $(DOCKER_DIR)/*.yml)
DOCKER_CMD := docker compose \
				--project-directory $(CUR_DIR) \
                --env-file $(ENV_FILE) \
                $(foreach f,$(DOCKER_FILES),-f $(f))

.DEFAULT_GOAL := help
.PHONY: help setup venv data clean up down restart build

# =============================================================================
# DOCKER COMMANDS
# =============================================================================

up: ## 🐳 Levanta todos los servicios definidos en /docker
	@echo "🚀 Levantando todos los servicios Docker..."
	@$(DOCKER_CMD) up -d
	@echo "✅ Todos los servicios están arriba."

down: ## 🐳 Detiene y elimina todos los servicios definidos en /docker
	@echo "🛑 Deteniendo todos los servicios Docker..."
	@$(DOCKER_CMD) down
	@echo "✅ Todos los servicios han sido detenidos y eliminados."

restart: ## 🐳 Reinicia todos los servicios definidos en /docker
	@echo "🔄 Reiniciando todos los servicios Docker..."
	@$(DOCKER_CMD) down
	@$(DOCKER_CMD) up -d
	@echo "✅ Todos los servicios han sido reiniciados."

build: ## 🐳 Reconstruye todos los servicios definidos en /docker
	@echo "🔨 Reconstruyendo todos los servicios Docker..."
	@$(DOCKER_CMD) up -d --build
	@echo "✅ Todos los servicios han sido reconstruidos."


# =============================================================================
# COMANDOS DEL PROYECTO
# =============================================================================

help: ## 💬 Muestra esta ayuda
	@echo "Comandos disponibles para el proyecto ecommerce_pipeline:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: venv data ## 🚀 Configura el proyecto completo: entorno y datos
	@echo "\n🎉 ¡Setup completado exitosamente!"
	@echo "Para activar el entorno virtual, ejecuta: source $(VENV_DIR)/bin/activate"

venv: $(VENV_DIR)/.synced ## 📦 Crea el entorno virtual y sincroniza las dependencias con uv

$(VENV_DIR)/.synced: pyproject.toml Makefile
	@echo "✅ Creando/actualizando entorno virtual con uv..."
	@uv venv $(VENV_DIR) --seed
	@echo "✅ Sincronizando dependencias..."
	@$(UV) sync
	@touch $@

data: ## 💾 Crea la carpeta de datos y descarga el dataset
	@echo "✅ Preparando directorio de datos..."
	@mkdir -p $(DATA_DIR)
	@echo "\n\033[1;33m⚠️  IMPORTANTE: AUTENTICACIÓN DE KAGGLE REQUERIDA ⚠️\033[0m"
	@echo "Asegúrate de tener tu token 'kaggle.json' en la carpeta ~/.kaggle/"
	@echo "Descargando dataset con la herramienta 'kaggle' del entorno virtual..."
	@$(KAGGLE) datasets download $(KAGGLE_DATASET_ID) -p $(DATA_DIR) --unzip
	@echo "✅ Dataset descargado y descomprimido en la carpeta '$(DATA_DIR)'."

clean: ## 🧹 Limpia el proyecto (elimina el venv y los datos)
	@echo "🔥 Limpiando artefactos del proyecto..."
	@rm -rf $(VENV_DIR) $(DATA_DIR)
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "✅ Limpieza completada."