from fastapi import APIRouter, Depends, BackgroundTasks
from typing import List
from pydantic import BaseModel
from app.application.llm.service import LLMAppService
from app.domain.llm.dto import ProviderDTO, ModelDTO, ProviderCreateDTO, ProviderUpdateDTO, ModelCreateDTO, ModelUpdateDTO
from app.domain.llm.enums import ProviderType, ModelType

router = APIRouter(prefix="/llm", tags=["LLM"])
app_service = LLMAppService()

# 数据模型
class StatusRequest(BaseModel):
    status: bool

class PreferenceRequest(BaseModel):
    provider_id: str
    model_id: str

class ChatRequest(BaseModel):
    model_id: str
    message: str


@router.post("/providers", response_model=ProviderDTO)
async def create_provider(
    dto: ProviderCreateDTO,
    # 这里应该添加用户认证依赖
    user_id: str = "test-user"
):
    """创建服务商"""
    return await app_service.create_provider(dto, user_id)


@router.put("/providers/{provider_id}", response_model=ProviderDTO)
async def update_provider(
    provider_id: str,
    dto: ProviderUpdateDTO,
    # 这里应该添加用户认证依赖
    user_id: str = "test-user"
):
    """更新服务商"""
    return await app_service.update_provider(provider_id, dto, user_id)


@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: str,
    # 这里应该添加用户认证依赖
    user_id: str = "test-user"
):
    """删除服务商"""
    await app_service.delete_provider(provider_id, user_id)
    return {"message": "Provider deleted successfully"}


@router.get("/providers", response_model=List[ProviderDTO])
async def get_all_providers(
    provider_type: ProviderType = ProviderType.ALL,
    # 这里应该添加用户认证依赖
    user_id: str = "test-user"
):
    """获取所有服务商"""
    return await app_service.get_all_providers(user_id, provider_type)


@router.patch("/providers/{provider_id}/status")
async def update_provider_status(
    provider_id: str,
    request: StatusRequest,
    # 这里应该添加用户认证依赖
    user_id: str = "test-user"
):
    """更新服务商状态"""
    await app_service.update_provider_status(provider_id, request.status, user_id)
    return {"message": "Provider status updated successfully"}

@router.post("/providers/{provider_id}/refresh-status")
async def refresh_provider_status(
    provider_id: str,
    # 这里应该添加用户认证依赖
    user_id: str = "test-user"
):
    """刷新服务商状态，测试配置是否可用"""
    result = await app_service.refresh_provider_status(provider_id, user_id)
    return {"message": "Provider status refreshed successfully", "status": result}


@router.post("/models", response_model=ModelDTO)
async def create_model(
    dto: ModelCreateDTO,
    background_tasks: BackgroundTasks,
    # 这里应该添加用户认证依赖
    user_id: str = "test-user"
):
    """创建模型"""
    return await app_service.create_model(dto, user_id, background_tasks)


@router.put("/models/{model_id}", response_model=ModelDTO)
async def update_model(
    model_id: str,
    dto: ModelUpdateDTO,
    background_tasks: BackgroundTasks,
    # 这里应该添加用户认证依赖
    user_id: str = "test-user"
):
    """更新模型"""
    return await app_service.update_model(model_id, dto, user_id, background_tasks)


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    background_tasks: BackgroundTasks,
    # 这里应该添加用户认证依赖
    user_id: str = "test-user"
):
    """删除模型"""
    await app_service.delete_model(model_id, user_id, background_tasks)
    return {"message": "Model deleted successfully"}


@router.patch("/models/{model_id}/status")
async def update_model_status(
    model_id: str,
    request: StatusRequest,
    background_tasks: BackgroundTasks,
    # 这里应该添加用户认证依赖
    user_id: str = "test-user"
):
    """更新模型状态"""
    await app_service.update_model_status(model_id, request.status, user_id, background_tasks)
    return {"message": "Model status updated successfully"}


@router.get("/models/active", response_model=List[ModelDTO])
async def get_active_models(
    provider_type: ProviderType = ProviderType.ALL,
    model_type: ModelType = ModelType.CHAT
):
    """获取激活的模型"""
    return await app_service.get_active_models_by_type(provider_type, model_type)


@router.post("/preference")
def save_preference(
    request: PreferenceRequest,
    # 这里应该添加用户认证依赖
    user_id: str = "test-user"
):
    """保存用户模型偏好设置"""
    app_service.save_user_preference(user_id, request.provider_id, request.model_id)
    return {"message": "Preference saved successfully"}


@router.get("/preference")
def get_preference(
    # 这里应该添加用户认证依赖
    user_id: str = "test-user"
):
    """获取用户模型偏好设置"""
    return app_service.get_user_preference(user_id)


@router.post("/chat")
async def chat(
    request: ChatRequest,
    # 这里应该添加用户认证依赖
    user_id: str = "test-user"
):
    """与模型对话"""
    # 这里应该实现实际的聊天逻辑
    return {"response": f"This is a response from model {request.model_id}: {request.message}"}
