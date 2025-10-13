#!/bin/bash

# ==============================================================================
# Script de Automatización para Mongo Explorer
# Autor: Gemini (Google)
#
# Uso: ./iniciar_explorer.sh /ruta/a/tu/kubeconfig/archivo.yaml
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. VERIFICAR PARÁMETROS DE ENTRADA
# ------------------------------------------------------------------------------

# Verificar si se proporcionó un argumento (la ruta del kubeconfig)
if [ -z "$1" ]; then
    echo "ERROR: Debe proporcionar la ruta COMPLETA al archivo kubeconfig."
    echo "Uso: $0 /ruta/al/archivo/kubeconfig.yaml"
    exit 1
fi

KUBECONFIG_PATH="$1"
PYTHON_SCRIPT="mongoexplorer.py"
MONGO_URI="mongodb://127.0.0.1:27018/" # URI que utiliza el port-forward local

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
sudo apt install -y python3-pip python3-tk python3.12-venv || { echo "ERROR: Falló la instalación de paquetes. Deteniendo." ; exit 1; }

# ------------------------------------------------------------------------------
# 3. CONFIGURACIÓN DEL ENTORNO VIRTUAL
# ------------------------------------------------------------------------------

VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "--- 3. Creando entorno virtual Python: $VENV_DIR ---"
    python3 -m venv "$VENV_DIR"
fi

echo "--- 4. Activando entorno virtual e instalando pymongo ---"
source "$VENV_DIR/bin/activate"

# Instalar la dependencia de pymongo. Se usa ==3.12.1 como pediste, aunque versiones más nuevas son comunes.
pip install pymongo==3.12.1 || { echo "ERROR: Falló la instalación de pymongo. Deteniendo." ; deactivate; exit 1; }

# ------------------------------------------------------------------------------
# 4. CONFIGURACIÓN KUBECTL Y PORT-FORWARD
# ------------------------------------------------------------------------------

echo "--- 5. Configurando KUBECONFIG y ejecutando Port-Forward ---"

# Exportar KUBECONFIG. Solo afecta a este script y a los procesos hijos.
export KUBECONFIG="$KUBECONFIG_PATH"

# Comando kubectl port-forward
# Se ejecuta en segundo plano (&) para no bloquear la terminal.
# Si el puerto local 27018 ya está en uso, esto fallará.
# 'sleep 2' da tiempo a que el reenvío de puertos se establezca antes de ejecutar la app Python.
kubectl port-forward svc/mongo-svc 27018:27017 -n ccoc &
PORT_FORWARD_PID=$!
echo "Port-Forward (PID: $PORT_FORWARD_PID) iniciado. Esperando 2 segundos..."
sleep 2

# ------------------------------------------------------------------------------
# 5. EJECUCIÓN DE LA APLICACIÓN PYTHON
# ------------------------------------------------------------------------------

echo "--- 6. Ejecutando Mongo Explorer ---"

# Ejecutar el script Python y pasar la URI como primer argumento ($MONGO_URI)
# La aplicación Python se ejecutará y usará la URI pasada
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