# Script para montar el entorno e instalar dependencias
```bash
#!/bin/bash

# Script de Automatización para Mongo Explorer
# Uso: ./exec_adm_mongodb.sh /ruta/a/tu/kubeconfig/archivo.yaml

# 1. Verificar parámetros de entrada
if [ -z "$1" ]; then
	echo "ERROR: Debe proporcionar la ruta COMPLETA al archivo kubeconfig."
	echo "Uso: $0 /ruta/al/archivo/kubeconfig.yaml"
	exit 1
fi

KUBECONFIG_PATH="$1"
PYTHON_SCRIPT="mongoexplorer.py"
MONGO_URI="mongodb://127.0.0.1:27018/"

# 2. Instalación de dependencias
sudo apt update
sudo apt install -y python3-pip python3-tk python3.12-venv

# 3. Configuración del entorno virtual
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
	python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install pymongo==3.12.1

# 4. Configuración KUBECONFIG y port-forward
export KUBECONFIG="$KUBECONFIG_PATH"
kubectl port-forward svc/mongo-svc 27018:27017 -n ccoc &
PORT_FORWARD_PID=$!
sleep 2

# 5. Ejecución de la aplicación Python
python3 "$PYTHON_SCRIPT" "$MONGO_URI"

# 6. Limpieza
kill $PORT_FORWARD_PID 2>/dev/null
deactivate
exit 0
```

Este script automatiza la instalación de dependencias, la creación del entorno virtual, la configuración de port-forward con kubectl y la ejecución de la aplicación Python. Es necesario proporcionar la ruta al archivo kubeconfig como argumento.
# Crear un nuevo repositorio desde la línea de comandos
```bash
echo "# adm-mongodb-ia99" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/fractalia99-lgtm/adm-mongodb-ia99.git
git push -u origin main
```

# O subir un repositorio existente desde la línea de comandos
```bash
git remote add origin https://github.com/fractalia99-lgtm/adm-mongodb-ia99.git
git branch -M main
git push -u origin main
```

# Descripción de la aplicación
Esta aplicación de escritorio está pensada para conectar a una instancia de MongoDB residente en un pod de Kubernetes (k8s). Para ello, será necesario disponer del fichero `kubeconfig.yaml` para poder trabajar y autenticar la conexión con k8s.
# adm-mongodb-ia99