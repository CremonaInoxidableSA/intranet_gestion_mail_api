### Inicializar

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Limpieza

```bash
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
```

### Configuración (.env)

- Crea un archivo `.env` en la raíz del proyecto basado en [.env.example](.env.example).
- Variables requeridas:
  - EMAIL_FROM, SMTP_USER, SMTP_PASS, SMTP_HOST, SMTP_PORT
  - FRONTEND_URL, FRONTEND_IP, RESET_PATH
  - RESET_TOKEN_SECRET, RESET_TOKEN_EXP_MINUTES

Genera un secreto fuerte para `RESET_TOKEN_SECRET` (PowerShell en Windows):

```powershell
# 64 bytes aleatorios base64
[Convert]::ToBase64String((New-Object byte[] 64 | % {$_=Get-Random -Maximum 256}))
```

Ejemplo rápido para crear `.env` desde el ejemplo:

```powershell
Copy-Item .env.example .env
# Edita .env y completa tus valores
```

## Dependencias

### Limpiar

## pycache

# linux

```bash
find . -type d -name "__pycache__" -exec rm -r {} +
```

# windows

```bash
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
```

## venv

# linux

```bash
rm -rf venv
```

# windows

```bash
Remove-Item venv -Recurse -Force
```
