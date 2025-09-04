# Azure Calculator API - Documentación

## Descripción
API REST para calculadora con historial de operaciones y sistema de autenticación básico, usando Azure Storage Services.

## Configuración

### Azure Storage
- **Queue Storage**: Historial de operaciones
- **Table Storage**: Usuarios registrados

### Variables de Entorno (local.settings.json)
```json
{
    "IsEncrypted": false,
    "Values": {
        "AzureWebJobsStorage": "UseDevelopmentStorage=true",
        "FUNCTIONS_WORKER_RUNTIME": "python",
        "AZURE_STORAGE_CONNECTION_STRING": "UseDevelopmentStorage=true",
        "QUEUE_NAME": "calculator-history",
        "TABLE_NAME": "users"
    }
}
```

## Endpoints

### 1. POST /api/calculate
Realizar cálculos matemáticos y guardar en historial.

**Request Body:**
```json
{
    "operation": "suma|resta|multiplicacion|division|potencia|raiz",
    "operand1": 10,
    "operand2": 5,
    "user_id": "optional-user-id"
}
```

**Response:**
```json
{
    "operation_id": "uuid",
    "operation": "suma",
    "operand1": 10,
    "operand2": 5,
    "result": 15,
    "timestamp": "2025-09-03T14:30:00.000000+00:00",
    "user_id": "user-id",
    "status": "success"
}
```

**Ejemplos con curl:**
```bash
# Suma
curl -X POST http://localhost:7071/api/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "suma",
    "operand1": 10,
    "operand2": 5,
    "user_id": "user123"
  }'

# Raíz cuadrada
curl -X POST http://localhost:7071/api/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "raiz",
    "operand1": 16
  }'

# División
curl -X POST http://localhost:7071/api/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "division",
    "operand1": 20,
    "operand2": 4
  }'
```

### 2. GET /api/history
Consultar historial de operaciones.

**Query Parameters:**
- `user_id` (opcional): Filtrar por usuario
- `limit` (opcional): Máximo de operaciones (default: 50, max: 1000)
- `operation_type` (opcional): Filtrar por tipo de operación

**Response:**
```json
{
    "total_operations": 3,
    "operations": [
        {
            "operation_id": "uuid",
            "operation": "suma",
            "operand1": 10,
            "operand2": 5,
            "result": 15,
            "timestamp": "2025-09-03T14:30:00.000000+00:00",
            "user_id": "user123"
        }
    ],
    "retrieved_at": "2025-09-03T14:35:00.000000+00:00",
    "status": "success"
}
```

**Ejemplos con curl:**
```bash
# Obtener todo el historial
curl http://localhost:7071/api/history

# Filtrar por usuario
curl "http://localhost:7071/api/history?user_id=user123"

# Limitar resultados
curl "http://localhost:7071/api/history?limit=10"

# Filtrar por tipo de operación
curl "http://localhost:7071/api/history?operation_type=suma"
```

### 3. POST /api/register
Registrar nuevo usuario.

**Request Body:**
```json
{
    "username": "usuario123",
    "password": "password123",
    "email": "user@example.com"
}
```

**Response Éxito:**
```json
{
    "message": "Usuario registrado exitosamente",
    "user_id": "generated-uuid",
    "username": "usuario123",
    "created_at": "2025-09-03T14:30:00.000000+00:00",
    "status": "success"
}
```

**Response Error:**
```json
{
    "error": "El usuario ya existe",
    "status": "error",
    "error_code": "USER_EXISTS"
}
```

**Ejemplo con curl:**
```bash
curl -X POST http://localhost:7071/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123",
    "email": "test@example.com"
  }'
```

### 4. POST /api/login
Verificar credenciales de usuario.

**Request Body:**
```json
{
    "username": "usuario123",
    "password": "password123"
}
```

**Response Éxito:**
```json
{
    "message": "Usuario encontrado",
    "user_id": "uuid",
    "username": "usuario123",
    "last_login": "2025-09-03T14:30:00.000000+00:00",
    "status": "authenticated"
}
```

**Response Error:**
```json
{
    "error": "Usuario no encontrado o credenciales incorrectas",
    "status": "error",
    "error_code": "AUTHENTICATION_FAILED"
}
```

**Ejemplo con curl:**
```bash
curl -X POST http://localhost:7071/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### 5. GET /api/info
Información de la API.

**Response:**
```json
{
    "api_name": "Azure Calculator API",
    "version": "1.0.0",
    "endpoints": {
        "POST /api/calculate": "Realizar cálculos matemáticos",
        "GET /api/history": "Consultar historial de operaciones",
        "POST /api/register": "Registrar nuevo usuario",
        "POST /api/login": "Verificar credenciales de usuario",
        "GET /api/info": "Información de la API"
    },
    "supported_operations": ["suma", "resta", "multiplicacion", "division", "potencia", "raiz"],
    "timestamp": "2025-09-03T14:30:00.000000+00:00"
}
```

## Validaciones

### Operaciones Matemáticas
- **suma, resta, multiplicacion, potencia**: Requieren operand1 y operand2
- **division**: Valida división por cero
- **raiz**: Solo requiere operand1, valida números negativos

### Usuarios
- **username**: 4-50 caracteres, solo letras, números, guiones y guiones bajos
- **password**: Mínimo 6 caracteres
- **email**: Formato válido (opcional)

### Historial
- **limit**: Entre 1 y 1000
- **operation_type**: Debe ser una operación válida

## Códigos de Error

| Código HTTP | Descripción |
|-------------|-------------|
| 200 | Éxito |
| 201 | Recurso creado |
| 400 | Datos inválidos |
| 401 | No autenticado |
| 409 | Conflicto (usuario ya existe) |
| 500 | Error del servidor |

## Instalación y Ejecución

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Configurar Azure Storage Emulator:**
```bash
# Instalar Azurite (emulador de Azure Storage)
npm install -g azurite

# Ejecutar Azurite
azurite --silent --location c:\azurite --debug c:\azurite\debug.log
```

3. **Ejecutar Azure Functions:**
```bash
func start
```

4. **Probar endpoints:**
```bash
curl http://localhost:7071/api/info
```

## Estructura del Proyecto
```
azure-calculator-app/
??? shared/
?   ??? __init__.py
?   ??? azure_storage.py      # Gestión de Azure Storage
?   ??? auth_utils.py         # Utilidades de autenticación
?   ??? validators.py         # Validaciones y esquemas
??? function_app.py           # Endpoints principales
??? requirements.txt          # Dependencias Python
??? host.json                 # Configuración Azure Functions
??? local.settings.json       # Variables de entorno
??? README.md                 # Esta documentación
```

## Notas de Seguridad

- Las contraseñas se hashean con bcrypt
- Se validan todos los inputs
- Se implementa logging detallado
- Se manejan errores de forma segura
- No se exponen datos sensibles en las respuestas de error