"""
Azure Function App - Calculadora con Historial y Autenticacion
Implementa 4 endpoints: calculate, history, register, login
"""

import azure.functions as func
import logging
import json
import uuid
from datetime import datetime, timezone

# Importar modulos compartidos
from shared.azure_storage import get_storage_manager
from shared.auth_utils import (
    hash_password, verify_password, generate_user_id, 
    validate_username, validate_password, validate_email, 
    get_current_timestamp
)
from shared.validators import (
    CalculateRequest, RegisterRequest, LoginRequest,
    validate_json_request, perform_calculation, 
    validate_history_params, create_error_response, 
    create_success_response
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = func.FunctionApp()

@app.function_name(name="calculate")
@app.route(route="calculate", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def calculate_function(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para realizar calculos matematicos y guardar en historial
    POST /api/calculate
    """
    logger.info('Calculate function triggered')
    
    try:
        # Validar y parsear request
        is_valid, data = validate_json_request(req.get_body().decode(), CalculateRequest)
        if not is_valid:
            return func.HttpResponse(
                json.dumps(data), 
                status_code=400, 
                mimetype="application/json"
            )
        
        # Realizar calculo
        success, result = perform_calculation(
            data.operation, 
            data.operand1, 
            data.operand2
        )
        
        if not success:
            error_response = create_error_response(result, "CALCULATION_ERROR")
            return func.HttpResponse(
                json.dumps(error_response),
                status_code=400,
                mimetype="application/json"
            )
        
        # Preparar datos de respuesta
        operation_id = str(uuid.uuid4())
        timestamp = get_current_timestamp()
        
        operation_data = {
            "operation_id": operation_id,
            "operation": data.operation,
            "operand1": data.operand1,
            "operand2": data.operand2,
            "result": result,
            "timestamp": timestamp,
            "user_id": data.user_id,
            "status": "success"
        }
        
        # Guardar en historial
        try:
            storage_manager = get_storage_manager()
            storage_manager.add_operation_to_history(operation_data)
            logger.info(f"Operation {operation_id} saved to history")
        except Exception as e:
            logger.error(f"Failed to save to history: {e}")
            # Continuar aunque falle el guardado en historial
        
        # Crear respuesta
        response_data = create_success_response(operation_data)
        
        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in calculate function: {e}")
        error_response = create_error_response(
            "Internal server error", 
            "INTERNAL_ERROR"
        )
        return func.HttpResponse(
            json.dumps(error_response),
            status_code=500,
            mimetype="application/json"
        )


@app.function_name(name="history")
@app.route(route="history", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def history_function(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para consultar historial de operaciones
    GET /api/history?user_id=&limit=&operation_type=
    """
    logger.info('History function triggered')
    
    try:
        # Obtener parametros de query
        user_id = req.params.get('user_id')
        limit = req.params.get('limit')
        operation_type = req.params.get('operation_type')
        
        # Validar parametros
        is_valid, validated_params = validate_history_params(user_id, limit, operation_type)
        if not is_valid:
            return func.HttpResponse(
                json.dumps(validated_params),
                status_code=400,
                mimetype="application/json"
            )
        
        # Obtener historial desde storage
        try:
            storage_manager = get_storage_manager()
            history_data = storage_manager.get_operation_history(
                user_id=validated_params.get('user_id'),
                limit=validated_params['limit'],
                operation_type=validated_params.get('operation_type')
            )
            
            logger.info(f"Retrieved {history_data['total_operations']} operations from history")
            
            response_data = create_success_response(history_data)
            
            return func.HttpResponse(
                json.dumps(response_data),
                status_code=200,
                mimetype="application/json"
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve history: {e}")
            error_response = create_error_response(
                "Failed to retrieve operation history", 
                "STORAGE_ERROR"
            )
            return func.HttpResponse(
                json.dumps(error_response),
                status_code=500,
                mimetype="application/json"
            )
        
    except Exception as e:
        logger.error(f"Unexpected error in history function: {e}")
        error_response = create_error_response(
            "Internal server error", 
            "INTERNAL_ERROR"
        )
        return func.HttpResponse(
            json.dumps(error_response),
            status_code=500,
            mimetype="application/json"
        )


@app.function_name(name="register")
@app.route(route="register", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def register_function(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para registrar nuevos usuarios
    POST /api/register
    """
    logger.info('Register function triggered')
    
    try:
        # Validar y parsear request
        is_valid, data = validate_json_request(req.get_body().decode(), RegisterRequest)
        if not is_valid:
            return func.HttpResponse(
                json.dumps(data),
                status_code=400,
                mimetype="application/json"
            )
        
        # Validaciones adicionales
        username_valid, username_error = validate_username(data.username)
        if not username_valid:
            error_response = create_error_response(username_error, "INVALID_USERNAME")
            return func.HttpResponse(
                json.dumps(error_response),
                status_code=400,
                mimetype="application/json"
            )
        
        password_valid, password_error = validate_password(data.password)
        if not password_valid:
            error_response = create_error_response(password_error, "INVALID_PASSWORD")
            return func.HttpResponse(
                json.dumps(error_response),
                status_code=400,
                mimetype="application/json"
            )
        
        if data.email:
            email_valid, email_error = validate_email(data.email)
            if not email_valid:
                error_response = create_error_response(email_error, "INVALID_EMAIL")
                return func.HttpResponse(
                    json.dumps(error_response),
                    status_code=400,
                    mimetype="application/json"
                )
        
        try:
            storage_manager = get_storage_manager()
            
            # Verificar si el usuario ya existe
            existing_user = storage_manager.get_user_by_username(data.username)
            if existing_user:
                error_response = create_error_response(
                    "El usuario ya existe", 
                    "USER_EXISTS"
                )
                return func.HttpResponse(
                    json.dumps(error_response),
                    status_code=409,
                    mimetype="application/json"
                )
            
            # Crear nuevo usuario
            user_id = generate_user_id()
            password_hash = hash_password(data.password)
            created_at = get_current_timestamp()
            
            user_data = {
                "user_id": user_id,
                "username": data.username,
                "password_hash": password_hash,
                "email": data.email or "",
                "created_at": created_at
            }
            
            # Guardar usuario
            success = storage_manager.create_user(user_data)
            
            if success:
                response_data = create_success_response({
                    "message": "Usuario registrado exitosamente",
                    "user_id": user_id,
                    "username": data.username,
                    "created_at": created_at
                })
                
                logger.info(f"User {data.username} registered successfully with ID {user_id}")
                
                return func.HttpResponse(
                    json.dumps(response_data),
                    status_code=201,
                    mimetype="application/json"
                )
            else:
                error_response = create_error_response(
                    "El usuario ya existe", 
                    "USER_EXISTS"
                )
                return func.HttpResponse(
                    json.dumps(error_response),
                    status_code=409,
                    mimetype="application/json"
                )
                
        except Exception as e:
            logger.error(f"Failed to register user: {e}")
            error_response = create_error_response(
                "Failed to register user", 
                "STORAGE_ERROR"
            )
            return func.HttpResponse(
                json.dumps(error_response),
                status_code=500,
                mimetype="application/json"
            )
        
    except Exception as e:
        logger.error(f"Unexpected error in register function: {e}")
        error_response = create_error_response(
            "Internal server error", 
            "INTERNAL_ERROR"
        )
        return func.HttpResponse(
            json.dumps(error_response),
            status_code=500,
            mimetype="application/json"
        )


@app.function_name(name="login")
@app.route(route="login", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def login_function(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para verificar credenciales de usuario
    POST /api/login
    """
    logger.info('Login function triggered')
    
    try:
        # Validar y parsear request
        is_valid, data = validate_json_request(req.get_body().decode(), LoginRequest)
        if not is_valid:
            return func.HttpResponse(
                json.dumps(data),
                status_code=400,
                mimetype="application/json"
            )
        
        try:
            storage_manager = get_storage_manager()
            
            # Buscar usuario
            user = storage_manager.get_user_by_username(data.username)
            if not user:
                error_response = create_error_response(
                    "Usuario no encontrado o credenciales incorrectas",
                    "AUTHENTICATION_FAILED"
                )
                return func.HttpResponse(
                    json.dumps(error_response),
                    status_code=401,
                    mimetype="application/json"
                )
            
            # Verificar contrasena
            if not verify_password(data.password, user['password_hash']):
                error_response = create_error_response(
                    "Usuario no encontrado o credenciales incorrectas",
                    "AUTHENTICATION_FAILED"
                )
                return func.HttpResponse(
                    json.dumps(error_response),
                    status_code=401,
                    mimetype="application/json"
                )
            
            # Actualizar ultimo login
            try:
                storage_manager.update_user_last_login(user['user_id'])
            except Exception as e:
                logger.warning(f"Failed to update last login: {e}")
            
            # Respuesta exitosa
            response_data = create_success_response({
                "message": "Usuario encontrado",
                "user_id": user['user_id'],
                "username": user['username'],
                "last_login": get_current_timestamp(),
                "status": "authenticated"
            })
            
            logger.info(f"User {data.username} logged in successfully")
            
            return func.HttpResponse(
                json.dumps(response_data),
                status_code=200,
                mimetype="application/json"
            )
            
        except Exception as e:
            logger.error(f"Failed to authenticate user: {e}")
            error_response = create_error_response(
                "Authentication service error", 
                "STORAGE_ERROR"
            )
            return func.HttpResponse(
                json.dumps(error_response),
                status_code=500,
                mimetype="application/json"
            )
        
    except Exception as e:
        logger.error(f"Unexpected error in login function: {e}")
        error_response = create_error_response(
            "Internal server error", 
            "INTERNAL_ERROR"
        )
        return func.HttpResponse(
            json.dumps(error_response),
            status_code=500,
            mimetype="application/json"
        )

# Endpoint adicional para informacion de la API
@app.function_name(name="info")
@app.route(route="info", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def info_function(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para informacion de la API
    GET /api/info
    """
    info_data = {
        "api_name": "Azure Calculator API",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/calculate": "Realizar calculos matematicos",
            "GET /api/history": "Consultar historial de operaciones",
            "POST /api/register": "Registrar nuevo usuario",
            "POST /api/login": "Verificar credenciales de usuario",
            "GET /api/info": "Informacion de la API"
        },
        "supported_operations": ["suma", "resta", "multiplicacion", "division", "potencia", "raiz"],
        "timestamp": get_current_timestamp()
    }
    
    return func.HttpResponse(
        json.dumps(info_data),
        status_code=200,
        mimetype="application/json"
    )