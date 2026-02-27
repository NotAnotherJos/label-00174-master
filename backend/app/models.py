"""数据模型定义"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class MessageHeader(BaseModel):
    """报文头部信息"""
    group_count: Optional[str] = None      # 报文组数
    timestamp: Optional[str] = None        # 时间
    raw_lines: List[str] = Field(default_factory=list)  # 原始头部行


class MessageGroup(BaseModel):
    """单组数字"""
    segment: int           # 段号 (1-3)
    line: int              # 行号 (1-10)
    position: int          # 组位置 (1-10)
    value: str             # 4位数字值
    global_index: int      # 全局索引 (0-299)


class MessageContent(BaseModel):
    """报文内容"""
    header: MessageHeader = Field(default_factory=MessageHeader)
    groups: List[MessageGroup] = Field(default_factory=list)
    raw_text: str = ""


class ErrorDetail(BaseModel):
    """错误详情"""
    segment: int           # 段号
    line: int              # 行号
    position: int          # 组位置
    global_index: int      # 全局索引
    submitted_value: str   # 提交的值
    correct_value: str     # 正确的值
    error_type: str        # 错误类型: mismatch, missing, extra


class ReviewResult(BaseModel):
    """批阅结果"""
    id: str
    created_at: datetime
    pdf_filename: str
    txt_filename: str
    total_groups: int          # 总组数
    error_count: int           # 错误数
    score: float               # 得分
    errors: List[ErrorDetail]  # 错误详情列表
    header_info: MessageHeader # 头部信息
    status: str = "completed"  # 状态: processing, completed, failed
    message: str = ""          # 状态信息


class ReviewRequest(BaseModel):
    """批阅请求"""
    pdf_file_id: str
    txt_file_id: str


class ReviewSummary(BaseModel):
    """批阅摘要（用于列表显示）"""
    id: str
    created_at: datetime
    pdf_filename: str
    score: float
    error_count: int
    status: str
