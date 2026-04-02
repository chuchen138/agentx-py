from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio

from app.domain.llm.high_availability import HighAvailabilityDomainService, HighAvailabilityResult
from app.domain.llm.circuit_breaker import CircuitBreakerService
from app.domain.llm.health_check import HealthCheckScheduler
from app.domain.llm.fallback import FallbackChainManager, FallbackChain
from app.domain.llm.enums import ModelType

app = FastAPI(title="High Availability Gateway", version="1.0.0")

# 服务实例
ha_service = HighAvailabilityDomainService()
circuit_breaker_service = CircuitBreakerService()
health_check_scheduler = HealthCheckScheduler()
fallback_chain_manager = FallbackChainManager()


class SelectInstanceRequest(BaseModel):
    """选择实例请求"""
    user_id: str
    model_type: str
    session_id: Optional[str] = None
    fallback_chain: Optional[List[str]] = None


class ReportResultRequest(BaseModel):
    """上报结果请求"""
    model_id: str
    success: bool
    latency_ms: float
    error_message: Optional[str] = None


class ApiInstanceDTO(BaseModel):
    """API实例DTO"""
    provider: str
    model: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    instance_id: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: str
    services: Dict[str, str]


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    # 启动健康检查调度器
    await health_check_scheduler.start()
    print("High Availability Gateway started")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    # 停止健康检查调度器
    await health_check_scheduler.stop()
    print("High Availability Gateway stopped")


@app.post("/api/v1/select", response_model=ApiInstanceDTO)
async def select_instance(request: SelectInstanceRequest) -> ApiInstanceDTO:
    """选择最佳实例"""
    try:
        # 转换模型类型
        model_type = ModelType(request.model_type)
        
        # 检查熔断器状态
        if request.fallback_chain:
            for model_id in request.fallback_chain:
                should_allow = await circuit_breaker_service.should_allow_request(model_id)
                if not should_allow:
                    print(f"Circuit breaker open for model {model_id}")
        
        # 选择最佳实例
        result = await ha_service.select_best_provider(
            model_type=model_type,
            session_id=request.session_id,
            fallback_chain=request.fallback_chain
        )
        
        # 构建响应
        return ApiInstanceDTO(
            provider=result.provider_id,
            model=result.model_id,
            base_url=getattr(result.model_instance, 'base_url', None),
            api_key=getattr(result.model_instance, 'api_key', None),
            instance_id=result.instance_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to select instance: {str(e)}")


@app.post("/api/v1/report")
async def report_result(request: ReportResultRequest):
    """上报调用结果"""
    try:
        # 上报结果到高可用服务
        await ha_service.report_call_result(
            model_id=request.model_id,
            success=request.success,
            latency_ms=request.latency_ms,
            error_message=request.error_message
        )
        
        # 记录到熔断器
        await circuit_breaker_service.record_call_result(
            model_id=request.model_id,
            success=request.success,
            response_time=request.latency_ms
        )
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to report result: {str(e)}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    import datetime
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.datetime.now().isoformat(),
        services={
            "high_availability": "healthy",
            "circuit_breaker": "healthy",
            "health_check": "healthy",
            "fallback": "healthy"
        }
    )


@app.post("/api/v1/instances")
async def register_instance(instance: Dict):
    """注册实例"""
    try:
        # 这里应该实现实例注册逻辑
        print(f"Registered instance: {instance}")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register instance: {str(e)}")


@app.delete("/api/v1/instances/{instance_id}")
async def deregister_instance(instance_id: str):
    """注销实例"""
    try:
        # 这里应该实现实例注销逻辑
        print(f"Deregistered instance: {instance_id}")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deregister instance: {str(e)}")


@app.get("/api/v1/instances")
async def list_instances():
    """列出所有实例"""
    try:
        # 这里应该实现实例列表逻辑
        return {"instances": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list instances: {str(e)}")


@app.post("/api/v1/fallback-chains")
async def create_fallback_chain(chain_name: str, chain: FallbackChain):
    """创建降级链"""
    try:
        fallback_chain_manager.add_fallback_chain(chain_name, chain)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create fallback chain: {str(e)}")


@app.get("/api/v1/fallback-chains/{chain_name}/status")
async def get_fallback_chain_status(chain_name: str):
    """获取降级链状态"""
    try:
        status = fallback_chain_manager.get_chain_status(chain_name)
        if not status:
            raise HTTPException(status_code=404, detail=f"Fallback chain {chain_name} not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get fallback chain status: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)