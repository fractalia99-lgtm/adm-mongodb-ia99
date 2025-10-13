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