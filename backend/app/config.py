"""配置模块"""
import os
from pathlib import Path

# 基础路径配置
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
TEMPLATE_DIR = BASE_DIR / "templates"

# 确保目录存在
UPLOAD_DIR.mkdir(exist_ok=True)

# OCR配置
OCR_LANG = "ch"  # 中文识别
USE_GPU = False  # Docker环境默认不使用GPU

# 报文格式配置
DIGITS_PER_GROUP = 4      # 每组4个数字
GROUPS_PER_LINE = 10      # 每行10组
LINES_PER_SEGMENT = 10    # 每段10行
SEGMENTS_COUNT = 3        # 通常3段
TOTAL_GROUPS = GROUPS_PER_LINE * LINES_PER_SEGMENT * SEGMENTS_COUNT  # 300组

# 评分配置
TOTAL_SCORE = 100         # 总分100分
DEDUCT_PER_ERROR = 1      # 每错误扣1分

# API配置
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
