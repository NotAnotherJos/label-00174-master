"""评分模块 - 计算报文批阅得分"""
import logging
from typing import List
from .models import ErrorDetail
from .config import TOTAL_SCORE, DEDUCT_PER_ERROR

logger = logging.getLogger(__name__)


class Scorer:
    """评分器"""
    
    def __init__(
        self,
        total_score: float = TOTAL_SCORE,
        deduct_per_error: float = DEDUCT_PER_ERROR
    ):
        """
        初始化评分器
        
        Args:
            total_score: 总分（默认100分）
            deduct_per_error: 每个错误扣分（默认1分）
        """
        self.total_score = total_score
        self.deduct_per_error = deduct_per_error
    
    def calculate_score(
        self,
        errors: List[ErrorDetail],
        total_groups: int = 0
    ) -> float:
        """
        计算得分
        
        Args:
            errors: 错误列表
            total_groups: 总组数（用于比例计算）
            
        Returns:
            最终得分
        """
        error_count = len(errors)
        deduction = error_count * self.deduct_per_error
        
        # 确保分数不低于0
        score = max(0, self.total_score - deduction)
        
        logger.info(
            f"评分计算: 总分 {self.total_score}, "
            f"错误数 {error_count}, "
            f"扣分 {deduction}, "
            f"最终得分 {score}"
        )
        
        return score
    
    def calculate_score_by_type(
        self,
        errors: List[ErrorDetail]
    ) -> dict:
        """
        按错误类型计算得分详情
        
        Args:
            errors: 错误列表
            
        Returns:
            得分详情字典
        """
        # 按类型统计错误
        type_counts = {
            'mismatch': 0,  # 内容不匹配
            'missing': 0,   # 缺失
            'extra': 0      # 多余
        }
        
        for error in errors:
            if error.error_type in type_counts:
                type_counts[error.error_type] += 1
        
        # 计算各类扣分
        deductions = {
            'mismatch': type_counts['mismatch'] * self.deduct_per_error,
            'missing': type_counts['missing'] * self.deduct_per_error,
            'extra': type_counts['extra'] * 0.5  # 多余内容扣一半
        }
        
        total_deduction = sum(deductions.values())
        final_score = max(0, self.total_score - total_deduction)
        
        return {
            'total_score': self.total_score,
            'error_counts': type_counts,
            'deductions': deductions,
            'total_deduction': total_deduction,
            'final_score': final_score
        }
    
    def get_grade(self, score: float) -> str:
        """
        获取成绩等级
        
        Args:
            score: 分数
            
        Returns:
            等级字符串
        """
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def get_feedback(self, score: float, error_count: int) -> str:
        """
        生成评价反馈
        
        Args:
            score: 分数
            error_count: 错误数
            
        Returns:
            反馈文字
        """
        grade = self.get_grade(score)
        
        feedback_map = {
            'A': "优秀！报文抄写准确度很高，继续保持！",
            'B': "良好！报文抄写基本准确，注意细节即可达到优秀。",
            'C': "中等。报文抄写有一定错误，请仔细核对后重新练习。",
            'D': "及格。报文抄写存在较多错误，建议加强练习。",
            'F': "不及格。报文抄写错误过多，请认真复习后重做。"
        }
        
        base_feedback = feedback_map.get(grade, "")
        
        if error_count == 0:
            return "完美！零错误，报文抄写完全正确！"
        
        return f"{base_feedback}（共发现 {error_count} 处错误）"


def create_scorer(
    total_score: float = TOTAL_SCORE,
    deduct_per_error: float = DEDUCT_PER_ERROR
) -> Scorer:
    """创建评分器"""
    return Scorer(total_score, deduct_per_error)
