from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.domain.rule.service import RuleDomainService
from app.domain.rule.schemas import (
    RuleCreate, RuleUpdate, RuleToggle, RuleRollback,
    RuleResponse, RuleListResponse, RuleVersionsResponse,
    RuleExecuteRequest, RuleExecuteResponse
)
from app.domain.rule.exceptions import RuleValidationError, RuleExecutionError, ConcurrencyError
from typing import Optional

router = APIRouter(prefix="/rules", tags=["rules"])
rule_service = RuleDomainService()


@router.post("", response_model=RuleResponse)
async def create_rule(
    request: Request,
    rule_data: RuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建规则"""
    try:
        operator = "admin@example.com"  # 实际应用中从认证信息获取
        ip_address = request.client.host if request.client else None
        
        rule = await rule_service.create_rule(
            name=rule_data.name,
            handler_key=rule_data.handlerKey,
            description=rule_data.description,
            config=rule_data.config,
            priority=rule_data.priority,
            operator=operator,
            ip_address=ip_address,
            session=db
        )
        
        return RuleResponse(
            id=rule.id,
            name=rule.name,
            handlerKey=rule.handler_key,
            description=rule.description,
            config=rule.config,
            enabled=rule.enabled,
            priority=rule.priority,
            version=rule.version,
            createdAt=rule.created_at,
            updatedAt=rule.updated_at,
            updatedBy=rule.updated_by
        )
    except RuleValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    request: Request,
    rule_id: str,
    rule_data: RuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新规则"""
    try:
        operator = "admin@example.com"  # 实际应用中从认证信息获取
        ip_address = request.client.host if request.client else None
        
        rule = await rule_service.update_rule(
            rule_id=rule_id,
            name=rule_data.name,
            description=rule_data.description,
            config=rule_data.config,
            priority=rule_data.priority,
            operator=operator,
            ip_address=ip_address,
            session=db
        )
        
        return RuleResponse(
            id=rule.id,
            name=rule.name,
            handlerKey=rule.handler_key,
            description=rule.description,
            config=rule.config,
            enabled=rule.enabled,
            priority=rule.priority,
            version=rule.version,
            createdAt=rule.created_at,
            updatedAt=rule.updated_at,
            updatedBy=rule.updated_by
        )
    except RuleValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConcurrencyError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=RuleListResponse)
async def list_rules(
    handlerKey: Optional[str] = Query(None, description="规则处理器标识"),
    keyword: Optional[str] = Query(None, description="关键词"),
    enabled: Optional[bool] = Query(None, description="是否启用"),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(15, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """查询规则列表"""
    try:
        result = await rule_service.list_rules(
            handler_key=handlerKey,
            enabled=enabled,
            keyword=keyword,
            page=page,
            page_size=pageSize,
            session=db
        )
        return RuleListResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取规则详情"""
    try:
        rule = await rule_service.get_rule(rule_id, session=db)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        return RuleResponse(
            id=rule.id,
            name=rule.name,
            handlerKey=rule.handler_key,
            description=rule.description,
            config=rule.config,
            enabled=rule.enabled,
            priority=rule.priority,
            version=rule.version,
            createdAt=rule.created_at,
            updatedAt=rule.updated_at,
            updatedBy=rule.updated_by
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-handler-key/{handler_key}", response_model=RuleResponse)
async def get_rule_by_handler_key(
    handler_key: str,
    db: AsyncSession = Depends(get_db)
):
    """根据处理器标识查询规则"""
    try:
        rule = await rule_service.get_rule_by_handler_key(handler_key, session=db)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        return RuleResponse(
            id=rule.id,
            name=rule.name,
            handlerKey=rule.handler_key,
            description=rule.description,
            config=rule.config,
            enabled=rule.enabled,
            priority=rule.priority,
            version=rule.version,
            createdAt=rule.created_at,
            updatedAt=rule.updated_at,
            updatedBy=rule.updated_by
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{rule_id}")
async def delete_rule(
    request: Request,
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除规则"""
    try:
        operator = "admin@example.com"  # 实际应用中从认证信息获取
        ip_address = request.client.host if request.client else None
        
        deleted = await rule_service.delete_rule(
            rule_id=rule_id,
            operator=operator,
            ip_address=ip_address,
            session=db
        )
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        return {"message": "Rule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{rule_id}/versions", response_model=RuleVersionsResponse)
async def get_rule_versions(
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取规则历史版本"""
    try:
        versions = await rule_service.get_rule_versions(rule_id, session=db)
        
        version_list = []
        for version in versions:
            version_list.append({
                "version": version.version,
                "snapshot": version.snapshot,
                "changed_by": version.changed_by,
                "changed_at": version.changed_at,
                "change_reason": version.change_reason
            })
        
        return RuleVersionsResponse(versions=version_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{rule_id}/rollback/{version}", response_model=RuleResponse)
async def rollback_rule(
    request: Request,
    rule_id: str,
    version: int,
    rollback_data: RuleRollback,
    db: AsyncSession = Depends(get_db)
):
    """回滚到指定版本"""
    try:
        operator = "admin@example.com"  # 实际应用中从认证信息获取
        ip_address = request.client.host if request.client else None
        
        rule = await rule_service.rollback_rule(
            rule_id=rule_id,
            version=version,
            reason=rollback_data.reason,
            operator=operator,
            ip_address=ip_address,
            session=db
        )
        
        return RuleResponse(
            id=rule.id,
            name=rule.name,
            handlerKey=rule.handler_key,
            description=rule.description,
            config=rule.config,
            enabled=rule.enabled,
            priority=rule.priority,
            version=rule.version,
            createdAt=rule.created_at,
            updatedAt=rule.updated_at,
            updatedBy=rule.updated_by
        )
    except RuleValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{rule_id}/toggle", response_model=RuleResponse)
async def toggle_rule(
    request: Request,
    rule_id: str,
    toggle_data: RuleToggle,
    db: AsyncSession = Depends(get_db)
):
    """启用/禁用规则"""
    try:
        operator = "admin@example.com"  # 实际应用中从认证信息获取
        ip_address = request.client.host if request.client else None
        
        rule = await rule_service.toggle_rule(
            rule_id=rule_id,
            enabled=toggle_data.enabled,
            reason=toggle_data.reason,
            operator=operator,
            ip_address=ip_address,
            session=db
        )
        
        return RuleResponse(
            id=rule.id,
            name=rule.name,
            handlerKey=rule.handler_key,
            description=rule.description,
            config=rule.config,
            enabled=rule.enabled,
            priority=rule.priority,
            version=rule.version,
            createdAt=rule.created_at,
            updatedAt=rule.updated_at,
            updatedBy=rule.updated_by
        )
    except RuleValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=RuleExecuteResponse)
async def execute_rule(
    request: Request,
    execute_data: RuleExecuteRequest,
    db: AsyncSession = Depends(get_db)
):
    """执行规则"""
    try:
        operator = "admin@example.com"  # 实际应用中从认证信息获取
        ip_address = request.client.host if request.client else None
        
        result = await rule_service.execute_rule(
            rule_id=execute_data.ruleId,
            context_data=execute_data.context,
            operator=operator,
            ip_address=ip_address,
            session=db
        )
        
        return RuleExecuteResponse(
            allowed=result.allowed,
            reason=result.reason,
            data=result.data,
            error_code=result.error_code
        )
    except RuleExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
