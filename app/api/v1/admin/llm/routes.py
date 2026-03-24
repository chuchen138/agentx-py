from fastapi import APIRouter, Depends, BackgroundTasks
from typing import List
from app.application.llm.service import AdminLLMAppService
from app.domain.llm.dto import ProviderDTO, ModelDTO, ProviderCreateDTO, ProviderUpdateDTO, ModelCreateDTO, ModelUpdateDTO

router = APIRouter(prefix="/admin/llm", tags=["Admin LLM"])
admin_app_service = AdminLLMAppService()


@router.post("/providers", response_model=ProviderDTO)
async def create_official_provider(
    dto: ProviderCreateDTO
    # 这里应该添加管理员认证依赖
):
    """创建官方服务商"""
    return await admin_app_service.create_provider(dto)


@router.put("/providers/{provider_id}", response_model=ProviderDTO)
async def update_official_provider(
    provider_id: str,
    dto: ProviderUpdateDTO
    # 这里应该添加管理员认证依赖
):
    """更新官方服务商"""
    return await admin_app_service.update_provider(provider_id, dto)


@router.delete("/providers/{provider_id}")
async def delete_official_provider(
    provider_id: str
    # 这里应该添加管理员认证依赖
):
    """删除官方服务商"""
    await admin_app_service.delete_provider(provider_id)
    return {"message": "Provider deleted successfully"}


@router.post("/models", response_model=ModelDTO)
async def create_official_model(
    dto: ModelCreateDTO,
    background_tasks: BackgroundTasks
    # 这里应该添加管理员认证依赖
):
    """创建官方模型"""
    return await admin_app_service.create_model(dto, background_tasks)


@router.put("/models/{model_id}", response_model=ModelDTO)
async def update_official_model(
    model_id: str,
    dto: ModelUpdateDTO,
    background_tasks: BackgroundTasks
    # 这里应该添加管理员认证依赖
):
    """更新官方模型"""
    return await admin_app_service.update_model(model_id, dto, background_tasks)


@router.delete("/models/{model_id}")
async def delete_official_model(
    model_id: str,
    background_tasks: BackgroundTasks
    # 这里应该添加管理员认证依赖
):
    """删除官方模型"""
    await admin_app_service.delete_model(model_id, background_tasks)
    return {"message": "Model deleted successfully"}
