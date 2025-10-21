#!/bin/bash

# ==============================================================================
# Script de Automatización para Mongo Explorer
# Autor: Gemini (Google)
#
# Uso: ./run.sh -k <ruta/a/kubeconfig.yaml>
#
# Argumentos:
#   -k <ruta/a/kubeconfig.yaml> : Ruta COMPLETA al archivo kubeconfig (Obligatorio).
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. PARSEAR ARGUMENTOS DE ENTRADA
# ------------------------------------------------------------------------------

KUBECONFIG_PATH=""

# Usar getopts para parsear la bandera -k
while getopts "k:" opt; do
  case $opt in
    k)
      KUBECONFIG_PATH="$OPTARG"
      ;;
    \?)
      echo "Uso: $0 -k /ruta/al/archivo/kubeconfig.yaml" >&2
      exit 1
      ;;
  esac
done

# Verificar si la ruta del kubeconfig es obligatoria y fue proporcionada
if [ -z "$KUBECONFIG_PATH" ]; then
    echo "ERROR: Debe proporcionar la ruta COMPLETA al archivo kubeconfig usando -k."
    echo "Uso: $0 -k /ruta/al/archivo/kubeconfig.yaml"
    exit 1
fi


PYTHON_SCRIPT="mongoexplorer.py"
MONGO_URI="mongodb://127.0.0.1:27018/" # URI que utiliza el port-forward local
VENV_DIR="venv" # Usamos una ruta relativa por defecto

echo "--- 1. Verificando Kubeconfig y permisos ---"

# Verificar si el archivo kubeconfig existe
if [ ! -f "$KUBECONFIG_PATH" ]; then
    echo "ERROR: El archivo kubeconfig no se encontró en la ruta: $KUBECONFIG_PATH"
    exit 1
fi

# Verificar si kubectl está instalado
if ! command -v kubectl &> /dev/null
then
    echo "ERROR: kubectl no está instalado o no se encuentra en el PATH."
    echo "Por favor, instálelo e inténtelo de nuevo."
    exit 1
fi

# ------------------------------------------------------------------------------
# 2. INSTALACIÓN DE DEPENDENCIAS (si es necesario)
# ------------------------------------------------------------------------------

echo "--- 2. Instalando o actualizando dependencias del sistema (se requiere sudo) ---"
# Se asume que el usuario está en una distribución basada en Debian/Ubuntu
sudo apt update
# Aseguramos la instalación de python3-dev para compilaciones nativas si fueran necesarias.
sudo apt install -y python3-pip python3-tk python3.12-venv python3-dev || { echo "ERROR: Falló la instalación de paquetes. Deteniendo." ; exit 1; }

# ------------------------------------------------------------------------------
# 3. CONFIGURACIÓN DEL ENTORNO VIRTUAL
# ------------------------------------------------------------------------------

if [ ! -d "$VENV_DIR" ]; then
    echo "--- 3. Creando entorno virtual Python: $VENV_DIR ---"
    python3 -m venv "$VENV_DIR" || { echo "ERROR: Falló la creación del entorno virtual." ; exit 1; }
fi

echo "--- 4. Activando entorno virtual e instalando pymongo ---"
# Activación del entorno virtual
source "$VENV_DIR/bin/activate" || { echo "ERROR: No se pudo activar el entorno virtual." ; exit 1; }

# Instalar la dependencia de pymongo.
pip install --upgrade pip
pip install pymongo==3.12.1 || { 
    echo "ERROR: Falló la instalación de pymongo. Deteniendo." 
    deactivate
    exit 1 
}

# ------------------------------------------------------------------------------
# 4. CONFIGURACIÓN KUBECTL Y PORT-FORWARD
# ------------------------------------------------------------------------------

echo "--- 5. Configurando KUBECONFIG y ejecutando Port-Forward ---"

# Exportar KUBECONFIG. Solo afecta a este script y a los procesos hijos.
export KUBECONFIG="$KUBECONFIG_PATH"

# Comando kubectl port-forward
kubectl port-forward svc/mongo-svc 27018:27017 -n ccoc &
PORT_FORWARD_PID=$!
echo "Port-Forward (PID: $PORT_FORWARD_PID) iniciado. Esperando 5 segundos..."
sleep 5

# ------------------------------------------------------------------------------
# 5. EJECUCIÓN DE LA APLICACIÓN PYTHON
# ------------------------------------------------------------------------------

echo "--- 6. Ejecutando Mongo Explorer ---"

# Ejecutar el script Python con la URI pasada como argumento
python3 "$PYTHON_SCRIPT" "$MONGO_URI"

# ------------------------------------------------------------------------------
# 6. LIMPIEZA
# ------------------------------------------------------------------------------

echo "--- 7. Terminando Port-Forward y desactivando entorno virtual ---"
# Terminar el proceso de port-forward
kill $PORT_FORWARD_PID 2>/dev/null
deactivate

echo "Proceso finalizado. El entorno virtual está desactivado."
exit 0
