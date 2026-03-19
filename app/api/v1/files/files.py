from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from uuid import UUID
from app.domain.file.file_type import FileType
from app.domain.file.schemas import FileUploadResponse, FileRecordResponse
from app.application.file.service.file_storage_app_service import FileStorageAppService
from app.core.database import SessionLocal
from app.domain.file.file_record import FileRecord

router = APIRouter()
file_service = FileStorageAppService()


@router.post("/upload/avatar", response_model=FileUploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: UUID = Form(...)
):
    """上传头像"""
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 构建元数据
        metadata = {
            "original_filename": file.filename,
            "content_type": file.content_type
        }
        
        # 保存文件
        file_record = file_service.save_file(
            file=file_content,
            file_type=FileType.AVATAR,
            user_id=user_id,
            metadata=metadata
        )
        
        # 返回响应
        return FileUploadResponse(
            file_id=file_record.id,
            file_url=file_record.file_url,
            file_name=file_record.original_filename,
            file_size=file_record.file_size,
            mime_type=file_record.mime_type
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload/general", response_model=FileUploadResponse)
async def upload_general(
    file: UploadFile = File(...),
    user_id: UUID = Form(...)
):
    """上传通用文件"""
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 构建元数据
        metadata = {
            "original_filename": file.filename,
            "content_type": file.content_type
        }
        
        # 保存文件
        file_record = file_service.save_file(
            file=file_content,
            file_type=FileType.GENERAL,
            user_id=user_id,
            metadata=metadata
        )
        
        # 返回响应
        return FileUploadResponse(
            file_id=file_record.id,
            file_url=file_record.file_url,
            file_name=file_record.original_filename,
            file_size=file_record.file_size,
            mime_type=file_record.mime_type
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload/rag", response_model=FileUploadResponse)
async def upload_rag(
    file: UploadFile = File(...),
    user_id: UUID = Form(...),
    dataset_id: UUID = Form(...)
):
    """上传RAG文件"""
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 构建元数据
        metadata = {
            "original_filename": file.filename,
            "content_type": file.content_type,
            "dataset_id": dataset_id
        }
        
        # 保存文件
        file_record = file_service.save_file(
            file=file_content,
            file_type=FileType.RAG,
            user_id=user_id,
            metadata=metadata
        )
        
        # 返回响应
        return FileUploadResponse(
            file_id=file_record.id,
            file_url=file_record.file_url,
            file_name=file_record.original_filename,
            file_size=file_record.file_size,
            mime_type=file_record.mime_type
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{file_id}", response_model=FileRecordResponse)
async def get_file(file_id: UUID):
    """获取文件信息"""
    try:
        file_record = file_service.get_file(file_id=file_id)
        return FileRecordResponse.from_orm(file_record)
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")


@router.put("/{file_id}", response_model=FileRecordResponse)
async def update_file(
    file_id: UUID,
    file: UploadFile = File(...),
    user_id: UUID = Form(...)
):
    """更新文件"""
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 更新文件
        file_record = file_service.update_file(file_id=file_id, file=file_content, user_id=user_id)
        return FileRecordResponse.from_orm(file_record)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{file_id}")
async def delete_file(file_id: UUID, user_id: UUID = Form(...)):
    """删除文件"""
    try:
        success = file_service.delete_file(file_id=file_id, user_id=user_id)
        if success:
            return JSONResponse(content={"message": "File deleted successfully"})
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{file_id}/download")
async def download_file(file_id: str):
    """下载文件"""
    try:
        from fastapi.responses import StreamingResponse
        import io
        import uuid
        
        # 打印调试信息
        print(f"Downloading file with ID: {file_id}")
        
        # 获取文件记录
        try:
            # 尝试直接使用字符串ID查询
            db = SessionLocal()
            file_record = db.query(FileRecord).filter(
                FileRecord.id == file_id,
                FileRecord.deleted_at.is_(None)
            ).first()
            db.close()
            
            if not file_record:
                print(f"File not found in database: {file_id}")
                raise ValueError("File not found")
            
            print(f"Found file: {file_record.original_filename}")
        except Exception as db_error:
            print(f"Database error: {db_error}")
            raise
        
        # 从存储后端加载文件内容
        # 这里需要根据存储后端类型加载文件
        # 暂时使用本地存储的方式读取
        import os
        from pathlib import Path
        
        # 尝试从本地存储加载
        file_path = Path("./uploads/general") / file_record.file_path
        print(f"Trying to load from local path: {file_path}")
        
        if file_path.exists():
            print("File found in local storage")
            with open(file_path, "rb") as f:
                file_content = f.read()
        else:
            # 尝试从Minio加载
            print("File not found in local storage, trying Minio")
            from app.infrastructure.storage.backend.minio_storage import MinioStorageBackend
            minio_backend = MinioStorageBackend(bucket="agentx-files")
            try:
                file_content = minio_backend.load(file_record.file_url)
                print("File loaded from Minio")
            except Exception as minio_error:
                print(f"Minio error: {minio_error}")
                # 如果Minio加载失败，返回一个默认的错误文件
                file_content = b"File not found in storage backend"
        
        # 创建文件流
        file_stream = io.BytesIO(file_content)
        
        # 返回流式响应，使用原始文件名
        return StreamingResponse(
            file_stream,
            media_type=file_record.mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={file_record.original_filename}"
            }
        )
    except Exception as e:
        print(f"Download error: {e}")
        raise HTTPException(status_code=404, detail="File not found")


@router.get("/{file_id}/url")
async def get_file_url(file_id: UUID, expires_in: int = 3600):
    """获取临时访问URL"""
    try:
        # 这里需要实现获取临时访问URL的逻辑
        # 实际实现需要调用存储后端的get_url方法
        raise NotImplementedError("get_file_url not implemented")
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")


@router.get("/my/list")
async def get_my_files(
    user_id: UUID,
    page: int = 1,
    page_size: int = 10,
    file_type: Optional[str] = None
):
    """获取我的文件列表"""
    try:
        # 获取文件列表
        file_records = file_service.get_files_by_user_id(user_id, file_type)
        
        # 转换为响应格式
        files = []
        for record in file_records:
            files.append({
                "id": str(record.id),
                "user_id": str(record.user_id),
                "file_type": record.file_type,
                "original_filename": record.original_filename,
                "stored_filename": record.stored_filename,
                "file_path": record.file_path,
                "file_url": record.file_url,
                "file_size": record.file_size,
                "mime_type": record.mime_type,
                "storage_backend": record.storage_backend,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat()
            })
        
        # 计算分页
        total = len(files)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_files = files[start:end]
        
        # 返回结果
        return {
            "items": paginated_files,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch-delete")
async def batch_delete_files(file_ids: List[UUID], user_id: UUID = Form(...)):
    """批量删除文件"""
    try:
        # 这里需要实现批量删除文件的逻辑
        # 实际实现需要遍历文件ID并删除
        raise NotImplementedError("batch_delete_files not implemented")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
