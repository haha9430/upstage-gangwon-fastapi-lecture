from fastapi import FastAPI
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.api.route.user_routers import router as user_router
from app.exceptions import UserNotFoundError, EmailNotAllowedNameExistsError

from enum import Enum
from typing import Optional

app = FastAPI()


@app.exception_handler(EmailNotAllowedNameExistsError)
async def email_not_allowed_handler(request: Request, exc: EmailNotAllowedNameExistsError):
    return JSONResponse(
        status_code=409,
        content={"error": "Email Not Allowed", "message": str(exc)}
    )


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": "User Not Found", "message": str(exc)}
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error": "Bad Request", "message": str(exc)}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP Exception", "message": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "Something went wrong"}
    )


app.include_router(user_router)


@app.get("/hello")
def hello():
    return {"message": "Hello FastAPI!"}


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


@app.get("/hello/{model_name}")
def hello(model_name: ModelName,
          message: str):
    return {"message": f"Hello {model_name} {message}"}


@app.post("/debug")
async def debug_basic_request(request: Request):
    """HTTP 요청 디버깅용 API"""
    headers = dict(request.headers)
    body = await request.body()

    return {
        "method": request.method,
        "url": str(request.url),
        "headers": headers,
        "body": body.decode() if body else None,
        "query_params": dict(request.query_params),
        "path_params": dict(request.path_params),
        "usage_guide": {
            "query_params": "Use like: POST /debug?param1=value1&param2=value2",
            "path_params": "Use like: POST /debug/{item_id}",
            "body": "Send JSON body for testing"
        }
    }


@app.post("/debug/{item_id}")
async def debug_path_request(request: Request, item_id: str, category: Optional[str] = None):
    """HTTP 요청 디버깅용 API"""
    headers = dict(request.headers)
    body = await request.body()

    return {
        "method": request.method,
        "url": {
            "full_url": str(request.url),
            "scheme": request.url.scheme,
            "hostname": request.url.hostname,
            "port": request.url.port,
            "path": request.url.path,
            "query": request.url.query,
            "fragment": request.url.fragment
        },
        "headers": headers,
        "body": {
            "raw": body.decode() if body else None,
            "size": len(body) if body else 0
        },
        "path_params": {
            "item_id": item_id,
            "from_request": dict(request.path_params)
        },
        "query_params": {
            "category": category,
            "all_params": dict(request.query_params)
        },
        "client": {
            "host": request.client.host if request.client else None,
            "port": request.client.port if request.client else None
        },
        "cookies": dict(request.cookies),
        "content_type": request.headers.get("content-type"),
        "user_agent": request.headers.get("user-agent"),
        "auth": request.headers.get("authorization"),
        "usage_examples": {
            "path_param": f"Current item_id: {item_id}",
            "query_param": f"Current category: {category}",
            "example_url": "POST /debug/123?category=test&other=value"
        }
    }
