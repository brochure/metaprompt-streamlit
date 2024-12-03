# app/main.py
import time
from typing import Optional, Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field, ConfigDict

from app.config import settings
from app.utils.llm_service import LLMService


# 配置请求模型
class PromptRequest(BaseModel):
    """优化提示词请求模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prompt": "Tell me a story about a robot"
            }
        }
    )

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="原始提示词"
    )


class APIResponse(BaseModel):
    """API 统一响应模型"""
    success: bool
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)

    def to_json(self) -> dict[str, Any]:
        """转换为 JSON 格式"""
        return self.model_dump(exclude_none=True)


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.PROJECT_TITLE,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    debug=settings.DEBUG
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理器"""
    logger.warning(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            success=False,
            error=exc.detail
        ).to_json()
    )


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=APIResponse(
            success=False,
            error="Internal server error" if not settings.DEBUG else str(exc)
        ).to_json()
    )


# API 路由
@app.post(
    f"{settings.API_PREFIX}/optimize-prompt",
    response_model=APIResponse,
    summary="优化提示词",
    description="接收原始提示词并返回优化后的版本"
)
async def optimize_prompt(prompt: str):
    """优化提示词接口"""
    logger.info(f"Optimizing prompt: {prompt}")
    try:
        optimized_prompt = await LLMService.generate_optimized_prompt(prompt)
        return APIResponse(
            success=True,
            data={"optimized_prompt": optimized_prompt}
        ).to_json()
    except Exception as e:
        logger.error(f"Failed to optimize prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize prompt"
        )


@app.post(
    f"{settings.API_PREFIX}/chat",
    response_model=APIResponse,
    summary="聊天对话",
    description="与 AI 助手进行对话"
)
async def chat(request: PromptRequest):
    """聊天对话接口"""
    logger.info(f"Chat request: {request.prompt}")
    try:
        response = await LLMService.chat_completion(request.prompt)
        return APIResponse(
            success=True,
            data={"response": response}
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return APIResponse(success=True, data={"status": "healthy"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG
    )
