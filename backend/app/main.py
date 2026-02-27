"""
报文自动批阅工具 - FastAPI后端服务

功能:
1. 接收PDF手抄报文和TXT标准报文
2. OCR识别PDF内容
3. 比对并评分
4. 生成批阅报告
"""
import os
import uuid
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel

from .config import UPLOAD_DIR, API_HOST, API_PORT
from .models import ReviewResult, ReviewSummary
from .review_service import get_review_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="报文自动批阅工具",
    description="基于OCR的手抄报文自动批阅系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UploadResponse(BaseModel):
    """上传响应"""
    file_id: str
    filename: str
    size: int
    message: str


class ReviewRequest(BaseModel):
    """批阅请求"""
    pdf_file_id: str
    txt_file_id: str


class ReviewResponse(BaseModel):
    """批阅响应"""
    review_id: str
    status: str
    message: str


# 文件存储映射
file_storage = {}


@app.get("/")
async def root():
    """根路径 - 服务状态检查"""
    return {
        "service": "报文自动批阅工具",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.post("/api/upload/pdf", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    上传PDF文件
    
    接收扫描后的PDF格式手抄报文文件
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="请上传PDF格式文件")
    
    try:
        # 生成文件ID
        file_id = str(uuid.uuid4())[:8]
        
        # 保存文件
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
        content = await file.read()
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # 存储映射
        file_storage[file_id] = {
            'path': str(file_path),
            'filename': file.filename,
            'type': 'pdf',
            'size': len(content)
        }
        
        logger.info(f"PDF文件上传成功: {file_id} - {file.filename}")
        
        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            size=len(content),
            message="PDF文件上传成功"
        )
        
    except Exception as e:
        logger.error(f"PDF上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@app.post("/api/upload/txt", response_model=UploadResponse)
async def upload_txt(file: UploadFile = File(...)):
    """
    上传TXT参照文件
    
    接收TXT格式的参照标准报文文件
    """
    if not file.filename.lower().endswith('.txt'):
        raise HTTPException(status_code=400, detail="请上传TXT格式文件")
    
    try:
        # 生成文件ID
        file_id = str(uuid.uuid4())[:8]
        
        # 保存文件
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
        content = await file.read()
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # 存储映射
        file_storage[file_id] = {
            'path': str(file_path),
            'filename': file.filename,
            'type': 'txt',
            'size': len(content)
        }
        
        logger.info(f"TXT文件上传成功: {file_id} - {file.filename}")
        
        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            size=len(content),
            message="TXT文件上传成功"
        )
        
    except Exception as e:
        logger.error(f"TXT上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@app.post("/api/review", response_model=ReviewResponse)
async def start_review(request: ReviewRequest):
    """
    开始批阅
    
    将PDF提取的报文内容与TXT参照报文进行逐组比对
    """
    # 验证文件
    pdf_info = file_storage.get(request.pdf_file_id)
    txt_info = file_storage.get(request.txt_file_id)
    
    if not pdf_info:
        raise HTTPException(status_code=404, detail="PDF文件未找到")
    if not txt_info:
        raise HTTPException(status_code=404, detail="TXT文件未找到")
    
    try:
        service = get_review_service()
        
        # 执行批阅
        result = service.review(
            pdf_path=pdf_info['path'],
            txt_path=txt_info['path'],
            pdf_filename=pdf_info['filename'],
            txt_filename=txt_info['filename']
        )
        
        return ReviewResponse(
            review_id=result.id,
            status=result.status,
            message=result.message
        )
        
    except Exception as e:
        logger.error(f"批阅失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批阅处理失败: {str(e)}")


@app.get("/api/review/{review_id}")
async def get_review_result(review_id: str):
    """
    获取批阅结果
    
    返回详细的错误信息报告，包含错误位置、原文内容与参照内容对比
    """
    service = get_review_service()
    result = service.get_result(review_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="批阅结果未找到")
    
    return {
        "id": result.id,
        "created_at": result.created_at.isoformat(),
        "pdf_filename": result.pdf_filename,
        "txt_filename": result.txt_filename,
        "total_groups": result.total_groups,
        "error_count": result.error_count,
        "score": result.score,
        "status": result.status,
        "message": result.message,
        "header_info": {
            "group_count": result.header_info.group_count,
            "timestamp": result.header_info.timestamp,
            "raw_lines": result.header_info.raw_lines
        } if result.header_info else None,
        "errors": [
            {
                "segment": e.segment,
                "line": e.line,
                "position": e.position,
                "global_index": e.global_index,
                "submitted_value": e.submitted_value,
                "correct_value": e.correct_value,
                "error_type": e.error_type
            }
            for e in result.errors
        ]
    }


@app.get("/api/reviews")
async def list_reviews():
    """
    获取所有批阅记录
    """
    service = get_review_service()
    results = service.list_results()
    
    return {
        "total": len(results),
        "items": [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "pdf_filename": r.pdf_filename,
                "score": r.score,
                "error_count": r.error_count,
                "status": r.status
            }
            for r in results
        ]
    }


@app.get("/api/review/{review_id}/report")
async def get_report(
    review_id: str,
    format: str = Query("text", description="报告格式: text, json, pdf")
):
    """
    获取批阅报告
    
    支持将批阅结果以清晰易读的格式输出（文本报告或生成PDF）
    """
    service = get_review_service()
    
    try:
        content, mime_type = service.generate_report(review_id, format)
        
        if format == 'pdf':
            return FileResponse(
                content,
                media_type=mime_type,
                filename=f"report_{review_id}.pdf"
            )
        elif format == 'json':
            return JSONResponse(content=eval(content))
        else:
            return PlainTextResponse(content=content)
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"报告生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")


@app.post("/api/review/quick")
async def quick_review(
    pdf_file: UploadFile = File(..., description="PDF手抄报文文件"),
    txt_file: UploadFile = File(..., description="TXT参照标准文件")
):
    """
    快速批阅（一键上传并批阅）
    
    同时上传PDF和TXT文件，直接返回批阅结果
    """
    # 验证文件类型
    if not pdf_file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="请上传PDF格式的手抄报文文件")
    if not txt_file.filename.lower().endswith('.txt'):
        raise HTTPException(status_code=400, detail="请上传TXT格式的参照文件")
    
    try:
        # 保存PDF
        pdf_id = str(uuid.uuid4())[:8]
        pdf_path = UPLOAD_DIR / f"{pdf_id}_{pdf_file.filename}"
        pdf_content = await pdf_file.read()
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        
        # 保存TXT
        txt_id = str(uuid.uuid4())[:8]
        txt_path = UPLOAD_DIR / f"{txt_id}_{txt_file.filename}"
        txt_content = await txt_file.read()
        with open(txt_path, 'wb') as f:
            f.write(txt_content)
        
        # 执行批阅
        service = get_review_service()
        result = service.review(
            pdf_path=str(pdf_path),
            txt_path=str(txt_path),
            pdf_filename=pdf_file.filename,
            txt_filename=txt_file.filename
        )
        
        # 返回完整结果
        return {
            "id": result.id,
            "created_at": result.created_at.isoformat(),
            "pdf_filename": result.pdf_filename,
            "txt_filename": result.txt_filename,
            "total_groups": result.total_groups,
            "error_count": result.error_count,
            "score": result.score,
            "status": result.status,
            "message": result.message,
            "errors": [
                {
                    "segment": e.segment,
                    "line": e.line,
                    "position": e.position,
                    "submitted_value": e.submitted_value,
                    "correct_value": e.correct_value,
                    "error_type": e.error_type
                }
                for e in result.errors[:20]  # 只返回前20个错误
            ],
            "errors_truncated": len(result.errors) > 20
        }
        
    except Exception as e:
        logger.error(f"快速批阅失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批阅处理失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )
