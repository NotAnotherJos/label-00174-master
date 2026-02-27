"""批阅服务模块 - 整合所有功能模块"""
import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

from .models import ReviewResult, MessageContent, MessageHeader
from .ocr_processor import create_ocr_processor
from .message_parser import create_parser, create_parser_v2
from .comparator import create_comparator
from .scorer import create_scorer
from .report_generator import create_report_generator
from .config import UPLOAD_DIR, USE_GPU

logger = logging.getLogger(__name__)


class ReviewService:
    """报文批阅服务"""
    
    def __init__(self):
        self.ocr_processor = create_ocr_processor(use_gpu=USE_GPU)
        self.parser = create_parser()
        self.parser_v2 = create_parser_v2()
        self.comparator = create_comparator()
        self.scorer = create_scorer()
        self.report_generator = create_report_generator()
        
        # 结果存储（生产环境应使用数据库）
        self.results = {}
    
    def process_pdf(self, pdf_path: str) -> MessageContent:
        """
        处理PDF文件
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            解析后的报文内容
        """
        logger.info(f"开始处理PDF: {pdf_path}")
        
        # OCR识别
        lines, _ = self.ocr_processor.process_pdf(pdf_path)
        
        # 解析报文
        content = self.parser.parse_message(lines)
        
        logger.info(f"PDF处理完成，识别到 {len(content.groups)} 组数字")
        return content
    
    def process_txt(self, txt_path: str) -> MessageContent:
        """
        处理TXT参照文件
        
        Args:
            txt_path: TXT文件路径
            
        Returns:
            解析后的报文内容
        """
        logger.info(f"开始处理TXT: {txt_path}")
        
        content = self.parser_v2.parse_txt_file(txt_path)
        
        logger.info(f"TXT处理完成，包含 {len(content.groups)} 组数字")
        return content
    
    def review(
        self,
        pdf_path: str,
        txt_path: str,
        pdf_filename: str = "",
        txt_filename: str = ""
    ) -> ReviewResult:
        """
        执行完整的批阅流程
        
        Args:
            pdf_path: PDF文件路径
            txt_path: TXT参照文件路径
            pdf_filename: PDF原始文件名
            txt_filename: TXT原始文件名
            
        Returns:
            批阅结果
        """
        review_id = str(uuid.uuid4())[:8]
        
        try:
            logger.info(f"开始批阅任务 {review_id}")
            
            # 处理PDF
            submitted_content = self.process_pdf(pdf_path)
            
            # 处理TXT
            reference_content = self.process_txt(txt_path)
            
            # 比对
            errors, total_groups, error_count = self.comparator.compare_with_tolerance(
                submitted_content,
                reference_content,
                allow_ocr_correction=True
            )
            
            # 评分
            score = self.scorer.calculate_score(errors, total_groups)
            
            # 构建结果
            result = ReviewResult(
                id=review_id,
                created_at=datetime.now(),
                pdf_filename=pdf_filename or Path(pdf_path).name,
                txt_filename=txt_filename or Path(txt_path).name,
                total_groups=total_groups,
                error_count=error_count,
                score=score,
                errors=errors,
                header_info=submitted_content.header,
                status="completed",
                message=self.scorer.get_feedback(score, error_count)
            )
            
            # 存储结果
            self.results[review_id] = result
            
            logger.info(
                f"批阅完成 {review_id}: "
                f"得分 {score:.1f}, 错误 {error_count}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"批阅失败 {review_id}: {str(e)}")
            
            result = ReviewResult(
                id=review_id,
                created_at=datetime.now(),
                pdf_filename=pdf_filename or Path(pdf_path).name,
                txt_filename=txt_filename or Path(txt_path).name,
                total_groups=0,
                error_count=0,
                score=0,
                errors=[],
                header_info=MessageHeader(),
                status="failed",
                message=f"批阅失败: {str(e)}"
            )
            
            self.results[review_id] = result
            return result
    
    def get_result(self, review_id: str) -> Optional[ReviewResult]:
        """获取批阅结果"""
        return self.results.get(review_id)
    
    def list_results(self) -> list:
        """获取所有批阅结果"""
        return list(self.results.values())
    
    def generate_report(
        self,
        review_id: str,
        format: str = 'text'
    ) -> Tuple[str, str]:
        """
        生成报告
        
        Args:
            review_id: 批阅ID
            format: 报告格式
            
        Returns:
            (报告内容或路径, MIME类型)
        """
        result = self.get_result(review_id)
        if result is None:
            raise ValueError(f"未找到批阅结果: {review_id}")
        
        if format == 'text':
            content = self.report_generator.generate_text_report(result)
            return content, 'text/plain'
        
        elif format == 'json':
            content = self.report_generator.generate_json_report(result)
            return content, 'application/json'
        
        elif format == 'pdf':
            file_path = self.report_generator.generate_pdf_report(result)
            return file_path, 'application/pdf'
        
        else:
            raise ValueError(f"不支持的报告格式: {format}")


# 全局服务实例
_service_instance: Optional[ReviewService] = None


def get_review_service() -> ReviewService:
    """获取批阅服务单例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ReviewService()
    return _service_instance
