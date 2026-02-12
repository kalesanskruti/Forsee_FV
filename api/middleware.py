import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import Request as FastAPIRequest
from jose import jwt, JWTError
from core import context, config
from core.logging import logger
import traceback
from uuid import UUID
from starlette.responses import JSONResponse

class OperationalMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Init base context with request_id
        ctx = context.RequestContext(request_id=request_id)
        context.set_context(ctx)
        
        response = None
        try:
            response = await call_next(request)
            
            # Add trace id to header
            response.headers["X-Request-ID"] = request_id
            
            # Log successful request (or managed error)
            duration = time.time() - start_time
            logger.info(
                f"Request finished",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": duration,
                    "ip": request.client.host
                }
            )
            
        except Exception as exc:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {str(exc)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration": duration,
                    "stack_trace": traceback.format_exc()
                }
            )
            
            # Global Exception Handler formatting
            return JSONResponse(
                status_code=500,
                content={
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal error occurred. Please contact support.",
                    "trace_id": request_id
                }
            )
            
        return response

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Skip paths that don't need tenant isolation (auth, docs, health)
        path = request.url.path
        if not path.startswith(config.settings.API_V1_STR) or path.startswith(f"{config.settings.API_V1_STR}/auth") or path == "/health":
            return await call_next(request)

        # 2. Extract Token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(
                    token, config.settings.SECRET_KEY, algorithms=[config.settings.ALGORITHM]
                )
                user_id = payload.get("sub")
                org_id = payload.get("org_id")
                role = payload.get("role")

                if org_id:
                    # Update existing context with tenant info
                    current_ctx = context.get_context()
                    if current_ctx:
                        current_ctx.org_id = UUID(org_id)
                        current_ctx.user_id = UUID(user_id) if user_id else current_ctx.user_id
                        current_ctx.role = role
                    else:
                        new_ctx = context.RequestContext(
                            user_id=UUID(user_id) if user_id else None,
                            org_id=UUID(org_id),
                            role=role
                        )
                        context.set_context(new_ctx)
                    
                    # logger.debug(f"Tenant Context Injected: {org_id}")

            except (JWTError, Exception) as e:
                # We allow the request to continue; deps.get_current_user will fail it if required.
                logger.warning(f"Tenant extraction failed: {e}")

        return await call_next(request)
