"""报告生成模块 - 生成批阅结果报告"""
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import json

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .models import ReviewResult, ErrorDetail, MessageHeader
from .config import UPLOAD_DIR

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, output_dir: Path = UPLOAD_DIR):
        self.output_dir = output_dir
        self._register_fonts()
    
    def _register_fonts(self):
        """注册中文字体"""
        try:
            # 尝试注册系统中文字体
            font_paths = [
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',  # Linux
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                '/System/Library/Fonts/PingFang.ttc',  # macOS
                'C:/Windows/Fonts/simhei.ttf',  # Windows
            ]
            
            for font_path in font_paths:
                if Path(font_path).exists():
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    logger.info(f"注册中文字体: {font_path}")
                    return
            
            logger.warning("未找到中文字体，PDF报告可能显示异常")
        except Exception as e:
            logger.warning(f"注册字体失败: {e}")
    
    def generate_text_report(self, result: ReviewResult) -> str:
        """
        生成文本格式报告
        
        Args:
            result: 批阅结果
            
        Returns:
            报告文本内容
        """
        lines = []
        lines.append("=" * 60)
        lines.append("             报文批阅结果报告")
        lines.append("=" * 60)
        lines.append("")
        
        # 基本信息
        lines.append("【基本信息】")
        lines.append(f"  批阅时间: {result.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"  PDF文件: {result.pdf_filename}")
        lines.append(f"  参照文件: {result.txt_filename}")
        lines.append("")
        
        # 头部信息
        if result.header_info:
            lines.append("【报文头部】")
            if result.header_info.group_count:
                lines.append(f"  报文组数: {result.header_info.group_count}")
            if result.header_info.timestamp:
                lines.append(f"  时间: {result.header_info.timestamp}")
            for raw_line in result.header_info.raw_lines:
                lines.append(f"  {raw_line}")
            lines.append("")
        
        # 评分结果
        lines.append("【评分结果】")
        lines.append(f"  总组数: {result.total_groups}")
        lines.append(f"  错误数: {result.error_count}")
        lines.append(f"  得  分: {result.score:.1f} 分")
        lines.append("")
        
        # 错误详情
        if result.errors:
            lines.append("【错误详情】")
            lines.append("-" * 60)
            lines.append(f"{'序号':<6}{'位置':<15}{'提交值':<12}{'正确值':<12}{'类型'}")
            lines.append("-" * 60)
            
            for i, error in enumerate(result.errors, 1):
                position = f"第{error.segment}段-第{error.line}行-第{error.position}组"
                error_type_map = {
                    'mismatch': '内容错误',
                    'missing': '内容缺失',
                    'extra': '多余内容'
                }
                error_type = error_type_map.get(error.error_type, error.error_type)
                
                lines.append(
                    f"{i:<6}{position:<15}{error.submitted_value:<12}"
                    f"{error.correct_value:<12}{error_type}"
                )
            
            lines.append("-" * 60)
        else:
            lines.append("【恭喜！没有发现任何错误！】")
        
        lines.append("")
        lines.append("=" * 60)
        lines.append("                 报告生成完毕")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def generate_json_report(self, result: ReviewResult) -> str:
        """
        生成JSON格式报告
        
        Args:
            result: 批阅结果
            
        Returns:
            JSON字符串
        """
        report_data = {
            'id': result.id,
            'created_at': result.created_at.isoformat(),
            'pdf_filename': result.pdf_filename,
            'txt_filename': result.txt_filename,
            'total_groups': result.total_groups,
            'error_count': result.error_count,
            'score': result.score,
            'status': result.status,
            'header_info': {
                'group_count': result.header_info.group_count,
                'timestamp': result.header_info.timestamp,
                'raw_lines': result.header_info.raw_lines
            } if result.header_info else None,
            'errors': [
                {
                    'segment': e.segment,
                    'line': e.line,
                    'position': e.position,
                    'global_index': e.global_index,
                    'submitted_value': e.submitted_value,
                    'correct_value': e.correct_value,
                    'error_type': e.error_type
                }
                for e in result.errors
            ]
        }
        
        return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    def generate_pdf_report(
        self,
        result: ReviewResult,
        output_path: Optional[str] = None
    ) -> str:
        """
        生成PDF格式报告
        
        Args:
            result: 批阅结果
            output_path: 输出路径
            
        Returns:
            PDF文件路径
        """
        if output_path is None:
            output_path = str(
                self.output_dir / f"report_{result.id}.pdf"
            )
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # 样式
        styles = getSampleStyleSheet()
        
        try:
            title_style = ParagraphStyle(
                'ChineseTitle',
                parent=styles['Title'],
                fontName='ChineseFont',
                fontSize=18,
                spaceAfter=20
            )
            normal_style = ParagraphStyle(
                'ChineseNormal',
                parent=styles['Normal'],
                fontName='ChineseFont',
                fontSize=10
            )
        except:
            title_style = styles['Title']
            normal_style = styles['Normal']
        
        story = []
        
        # 标题
        story.append(Paragraph("报文批阅结果报告", title_style))
        story.append(Spacer(1, 20))
        
        # 基本信息表格
        info_data = [
            ['批阅时间', result.created_at.strftime('%Y-%m-%d %H:%M:%S')],
            ['PDF文件', result.pdf_filename],
            ['参照文件', result.txt_filename],
            ['总组数', str(result.total_groups)],
            ['错误数', str(result.error_count)],
            ['得分', f'{result.score:.1f} 分'],
        ]
        
        info_table = Table(info_data, colWidths=[4*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # 错误详情
        if result.errors:
            story.append(Paragraph("错误详情", title_style))
            story.append(Spacer(1, 10))
            
            error_data = [['序号', '位置', '提交值', '正确值', '类型']]
            
            for i, error in enumerate(result.errors[:50], 1):  # 最多显示50条
                position = f"{error.segment}-{error.line}-{error.position}"
                error_type_map = {
                    'mismatch': '错误',
                    'missing': '缺失',
                    'extra': '多余'
                }
                error_data.append([
                    str(i),
                    position,
                    error.submitted_value,
                    error.correct_value,
                    error_type_map.get(error.error_type, '')
                ])
            
            error_table = Table(
                error_data,
                colWidths=[1.5*cm, 3*cm, 3*cm, 3*cm, 2*cm]
            )
            error_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(error_table)
            
            if len(result.errors) > 50:
                story.append(Spacer(1, 10))
                story.append(Paragraph(
                    f"（仅显示前50条错误，共 {len(result.errors)} 条）",
                    normal_style
                ))
        
        doc.build(story)
        logger.info(f"PDF报告生成完成: {output_path}")
        
        return output_path
    
    def save_report(
        self,
        result: ReviewResult,
        format: str = 'text'
    ) -> str:
        """
        保存报告到文件
        
        Args:
            result: 批阅结果
            format: 格式 ('text', 'json', 'pdf')
            
        Returns:
            文件路径
        """
        if format == 'text':
            content = self.generate_text_report(result)
            file_path = self.output_dir / f"report_{result.id}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return str(file_path)
        
        elif format == 'json':
            content = self.generate_json_report(result)
            file_path = self.output_dir / f"report_{result.id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return str(file_path)
        
        elif format == 'pdf':
            return self.generate_pdf_report(result)
        
        else:
            raise ValueError(f"不支持的报告格式: {format}")


def create_report_generator(output_dir: Optional[Path] = None) -> ReportGenerator:
    """创建报告生成器"""
    if output_dir is None:
        output_dir = UPLOAD_DIR
    return ReportGenerator(output_dir)
