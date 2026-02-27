"""报文比对模块 - 比对提交内容与标准参照"""
import logging
from typing import List, Tuple
from .models import MessageContent, MessageGroup, ErrorDetail

logger = logging.getLogger(__name__)


class MessageComparator:
    """报文比对器"""
    
    def __init__(self):
        pass
    
    def compare(
        self,
        submitted: MessageContent,
        reference: MessageContent
    ) -> Tuple[List[ErrorDetail], int, int]:
        """
        比对提交内容与参照标准
        
        Args:
            submitted: 提交的报文内容
            reference: 参照标准内容
            
        Returns:
            (错误列表, 总组数, 错误数)
        """
        errors = []
        total_groups = len(reference.groups)
        
        # 创建参照内容索引映射
        ref_map = {g.global_index: g for g in reference.groups}
        sub_map = {g.global_index: g for g in submitted.groups}
        
        # 遍历参照内容进行比对
        for idx in range(total_groups):
            ref_group = ref_map.get(idx)
            sub_group = sub_map.get(idx)
            
            if ref_group is None:
                continue
            
            if sub_group is None:
                # 提交内容缺失
                error = ErrorDetail(
                    segment=ref_group.segment,
                    line=ref_group.line,
                    position=ref_group.position,
                    global_index=ref_group.global_index,
                    submitted_value="(缺失)",
                    correct_value=ref_group.value,
                    error_type="missing"
                )
                errors.append(error)
                logger.debug(f"缺失: 位置 {ref_group.segment}-{ref_group.line}-{ref_group.position}")
            
            elif self._normalize_value(sub_group.value) != self._normalize_value(ref_group.value):
                # 内容不匹配
                error = ErrorDetail(
                    segment=ref_group.segment,
                    line=ref_group.line,
                    position=ref_group.position,
                    global_index=ref_group.global_index,
                    submitted_value=sub_group.value,
                    correct_value=ref_group.value,
                    error_type="mismatch"
                )
                errors.append(error)
                logger.debug(
                    f"错误: 位置 {ref_group.segment}-{ref_group.line}-{ref_group.position}, "
                    f"提交:{sub_group.value}, 正确:{ref_group.value}"
                )
        
        # 检查多余内容
        for idx in sub_map:
            if idx >= total_groups:
                sub_group = sub_map[idx]
                error = ErrorDetail(
                    segment=sub_group.segment,
                    line=sub_group.line,
                    position=sub_group.position,
                    global_index=sub_group.global_index,
                    submitted_value=sub_group.value,
                    correct_value="(多余)",
                    error_type="extra"
                )
                errors.append(error)
        
        # 按位置排序错误
        errors.sort(key=lambda e: e.global_index)
        
        error_count = len(errors)
        logger.info(f"比对完成: 总组数 {total_groups}, 错误数 {error_count}")
        
        return errors, total_groups, error_count
    
    def _normalize_value(self, value: str) -> str:
        """
        标准化值以进行比较
        处理OCR可能的识别误差
        """
        # 移除空格
        normalized = value.strip().replace(' ', '')
        
        # 常见OCR错误修正映射
        ocr_corrections = {
            'O': '0',  # 字母O -> 数字0
            'o': '0',
            'l': '1',  # 小写L -> 数字1
            'I': '1',  # 大写I -> 数字1
            'Z': '2',  # 有时Z被误认为2
            'S': '5',  # S -> 5
            's': '5',
            'B': '8',  # B -> 8
            'G': '6',  # G -> 6
            'g': '9',  # g -> 9
            'q': '9',  # q -> 9
        }
        
        result = ''
        for char in normalized:
            if char in ocr_corrections:
                result += ocr_corrections[char]
            else:
                result += char
        
        return result
    
    def compare_with_tolerance(
        self,
        submitted: MessageContent,
        reference: MessageContent,
        allow_ocr_correction: bool = True
    ) -> Tuple[List[ErrorDetail], int, int]:
        """
        带容错的比对
        
        Args:
            submitted: 提交的报文内容
            reference: 参照标准内容
            allow_ocr_correction: 是否允许OCR错误自动修正
            
        Returns:
            (错误列表, 总组数, 错误数)
        """
        if allow_ocr_correction:
            # 先尝试OCR修正
            corrected_groups = []
            for group in submitted.groups:
                corrected_value = self._normalize_value(group.value)
                corrected_group = MessageGroup(
                    segment=group.segment,
                    line=group.line,
                    position=group.position,
                    value=corrected_value,
                    global_index=group.global_index
                )
                corrected_groups.append(corrected_group)
            
            corrected_submitted = MessageContent(
                header=submitted.header,
                groups=corrected_groups,
                raw_text=submitted.raw_text
            )
            
            return self.compare(corrected_submitted, reference)
        
        return self.compare(submitted, reference)


def create_comparator() -> MessageComparator:
    """创建比对器"""
    return MessageComparator()
