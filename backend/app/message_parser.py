"""报文解析模块 - 解析报文结构"""
import re
import logging
from typing import List, Tuple, Optional
from .models import MessageHeader, MessageGroup, MessageContent
from .config import (
    DIGITS_PER_GROUP, GROUPS_PER_LINE, LINES_PER_SEGMENT, SEGMENTS_COUNT
)

logger = logging.getLogger(__name__)


class MessageParser:
    """报文解析器"""
    
    def __init__(self):
        # 数字提取正则表达式
        self.digit_pattern = re.compile(r'\d+')
        # 头部关键词
        self.header_keywords = ['组', '时间', '日期', '报文', '号', '第']
    
    def parse_header(self, lines: List[str]) -> Tuple[MessageHeader, int]:
        """
        解析报文头部（前三行）
        
        Args:
            lines: 所有行
            
        Returns:
            (头部信息, 头部结束行索引)
        """
        header = MessageHeader()
        header_lines = []
        header_end_idx = 0
        
        # 检查前几行是否为头部
        for i, line in enumerate(lines[:5]):  # 最多检查前5行
            line = line.strip()
            if not line:
                continue
            
            # 检测是否为头部行
            is_header = False
            for keyword in self.header_keywords:
                if keyword in line:
                    is_header = True
                    break
            
            # 如果该行主要包含数字组（4位数字连续），则不是头部
            digit_groups = self._extract_digit_groups(line)
            if len(digit_groups) >= 5:  # 超过5组数字，认为是数据行
                is_header = False
            
            if is_header or i < 3:
                header_lines.append(line)
                header_end_idx = i + 1
                
                # 尝试提取组数
                if '组' in line:
                    match = re.search(r'(\d+)\s*组', line)
                    if match:
                        header.group_count = match.group(1)
                
                # 尝试提取时间
                time_match = re.search(
                    r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?|\d{1,2}:\d{2}(:\d{2})?)',
                    line
                )
                if time_match:
                    header.timestamp = time_match.group(0)
            else:
                break
        
        header.raw_lines = header_lines
        logger.info(f"解析头部完成，共 {len(header_lines)} 行，头部结束于行 {header_end_idx}")
        
        return header, header_end_idx
    
    def _extract_digit_groups(self, text: str) -> List[str]:
        """
        从文本中提取数字组
        
        Args:
            text: 输入文本
            
        Returns:
            数字组列表
        """
        groups = []
        
        # 移除非数字字符（保留空格）
        cleaned = re.sub(r'[^\d\s]', ' ', text)
        
        # 提取所有数字
        all_digits = ''.join(cleaned.split())
        
        # 按4位分组
        for i in range(0, len(all_digits), DIGITS_PER_GROUP):
            group = all_digits[i:i + DIGITS_PER_GROUP]
            if len(group) == DIGITS_PER_GROUP:
                groups.append(group)
            elif len(group) > 0:
                # 补零或记录不完整组
                groups.append(group.ljust(DIGITS_PER_GROUP, '?'))
        
        return groups
    
    def parse_body(self, lines: List[str], start_idx: int = 0) -> List[MessageGroup]:
        """
        解析报文主体
        
        Args:
            lines: 所有行
            start_idx: 开始解析的行索引
            
        Returns:
            数字组列表
        """
        groups = []
        global_idx = 0
        segment = 1
        line_in_segment = 1
        
        for line_idx, line in enumerate(lines[start_idx:]):
            line = line.strip()
            if not line:
                continue
            
            # 提取该行的数字组
            line_groups = self._extract_digit_groups(line)
            
            # 跳过非数据行（数字组太少）
            if len(line_groups) < 3:
                continue
            
            # 处理每个数字组
            for pos_idx, value in enumerate(line_groups[:GROUPS_PER_LINE]):
                group = MessageGroup(
                    segment=segment,
                    line=line_in_segment,
                    position=pos_idx + 1,
                    value=value,
                    global_index=global_idx
                )
                groups.append(group)
                global_idx += 1
            
            # 更新段和行计数
            line_in_segment += 1
            if line_in_segment > LINES_PER_SEGMENT:
                line_in_segment = 1
                segment += 1
        
        logger.info(f"解析主体完成，共 {len(groups)} 组数字")
        return groups
    
    def parse_message(self, lines: List[str]) -> MessageContent:
        """
        解析完整报文
        
        Args:
            lines: OCR识别的行列表
            
        Returns:
            报文内容对象
        """
        content = MessageContent()
        content.raw_text = "\n".join(lines)
        
        # 解析头部
        header, body_start = self.parse_header(lines)
        content.header = header
        
        # 解析主体
        content.groups = self.parse_body(lines, body_start)
        
        return content
    
    def parse_reference_txt(self, txt_path: str) -> MessageContent:
        """
        解析参照标准报文TXT文件
        
        Args:
            txt_path: TXT文件路径
            
        Returns:
            报文内容对象
        """
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 清理行
        lines = [line.strip() for line in lines if line.strip()]
        
        return self.parse_message(lines)


class MessageParserV2:
    """
    增强版报文解析器
    针对标准格式进行优化：每行10组，每组4个数字
    """
    
    def __init__(self):
        self.digit_pattern = re.compile(r'\d{4}')
    
    def parse_txt_file(self, txt_path: str) -> MessageContent:
        """
        解析标准TXT参照文件
        格式: 每行包含10组4位数字，可能有空格分隔
        """
        content = MessageContent()
        groups = []
        
        with open(txt_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        
        content.raw_text = raw_text
        lines = raw_text.strip().split('\n')
        
        # 解析头部
        header = MessageHeader()
        body_start = 0
        
        for i, line in enumerate(lines[:5]):
            # 检查是否为数据行
            digits_in_line = re.findall(r'\d', line)
            if len(digits_in_line) >= 30:  # 至少有30个数字认为是数据行
                body_start = i
                break
            header.raw_lines.append(line)
            
            # 提取头部信息
            if '组' in line:
                match = re.search(r'(\d+)\s*组', line)
                if match:
                    header.group_count = match.group(1)
        
        content.header = header
        
        # 解析主体
        global_idx = 0
        segment = 1
        line_in_segment = 1
        
        for line in lines[body_start:]:
            line = line.strip()
            if not line:
                continue
            
            # 提取所有数字
            all_digits = re.sub(r'\D', '', line)
            
            # 按4位分组
            for i in range(0, len(all_digits), DIGITS_PER_GROUP):
                if i + DIGITS_PER_GROUP <= len(all_digits):
                    value = all_digits[i:i + DIGITS_PER_GROUP]
                    position = (global_idx % GROUPS_PER_LINE) + 1
                    
                    group = MessageGroup(
                        segment=segment,
                        line=line_in_segment,
                        position=position,
                        value=value,
                        global_index=global_idx
                    )
                    groups.append(group)
                    global_idx += 1
                    
                    # 更新段和行计数
                    if position == GROUPS_PER_LINE:
                        line_in_segment += 1
                        if line_in_segment > LINES_PER_SEGMENT:
                            line_in_segment = 1
                            segment += 1
        
        content.groups = groups
        logger.info(f"TXT解析完成，共 {len(groups)} 组数字")
        
        return content


def create_parser() -> MessageParser:
    """创建报文解析器"""
    return MessageParser()


def create_parser_v2() -> MessageParserV2:
    """创建增强版报文解析器"""
    return MessageParserV2()
