#!/usr/bin/env python3
"""
生成测试用 PDF 文件
此脚本生成一个包含报文内容的 PDF，其中故意包含一些错误用于测试批阅功能
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def generate_test_pdf(output_path="test_message.pdf"):
    """生成测试PDF文件，包含一些故意的错误"""
    
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # 标题
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, height - 2*cm, "Message Review Test")
    
    # 头部信息
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height - 3*cm, "Group Count: 300")
    c.drawString(2*cm, height - 3.5*cm, "Time: 2026-01-29 09:00:00")
    
    # 报文内容 - 包含故意的错误用于测试
    # 正确值参照 standard_reference.txt
    # 错误位置标记: [错误]
    
    message_lines = [
        # 第1段 (10行)
        "1234 5678 9012 3456 7890 1234 5678 9012 3456 7890",  # 正确
        "2345 6789 0123 4567 8901 2345 6789 0123 4567 8901",  # 正确
        "3456 7890 1234 5678 9012 3456 7890 1234 5678 9012",  # 正确
        "4567 8901 2345 6789 0123 4567 8901 2345 6789 0123",  # 正确
        "5678 9012 3456 7891 1234 5678 9012 3456 7890 1234",  # [错误] 7890->7891
        "6789 0123 4567 8901 2345 6789 0123 4567 8901 2345",  # 正确
        "7890 1234 5678 9012 3456 7890 1234 5678 9012 3456",  # 正确
        "8901 2345 6789 0123 4567 8901 2345 6789 0123 4567",  # 正确
        "9012 3456 7890 1234 5678 9012 3456 7890 1234 5678",  # 正确
        "0123 4567 8901 2345 6789 0123 4567 8901 2345 6789",  # 正确
        
        # 第2段 (10行)
        "1111 2222 3333 4444 5555 6666 7777 8888 9999 0000",  # 正确
        "1122 3344 5566 7788 9900 1122 3344 5566 7788 9900",  # 正确
        "2233 4455 6677 8899 0011 2233 4455 6677 8899 0011",  # 正确
        "3344 5566 7788 9900 1122 3344 5566 7788 9900 1122",  # 正确
        "4455 6677 8899 0011 2233 4455 6677 8899 0011 2233",  # 正确
        "5566 7788 9900 1122 3344 5566 7788 9900 1122 3344",  # 正确
        "6677 8899 0011 2233 4455 6677 8899 0012 2233 4455",  # [错误] 0011->0012
        "7788 9900 1122 3344 5566 7788 9900 1122 3344 5566",  # 正确
        "8899 0011 2233 4455 6677 8899 0011 2233 4455 6677",  # 正确
        "9900 1122 3344 5566 7788 9900 1122 3344 5566 7788",  # 正确
        
        # 第3段 (10行)
        "1357 2468 1357 2468 1357 2468 1357 2468 1357 2468",  # 正确
        "2468 1357 2468 1357 2468 1357 2468 1357 2468 1357",  # 正确
        "1234 4321 1234 4321 1234 4321 1234 4321 1234 4321",  # 正确
        "5678 8765 5679 8765 5678 8765 5678 8765 5678 8765",  # [错误] 5678->5679
        "9012 2109 9012 2109 9012 2109 9012 2109 9012 2109",  # 正确
        "3456 6543 3456 6543 3456 6543 3456 6543 3456 6543",  # 正确
        "7890 0987 7890 0987 7890 0987 7890 0987 7890 0987",  # 正确
        "1111 1111 2222 2222 3333 3333 4444 4444 5555 5555",  # 正确
        "6666 6666 7777 7777 8888 8888 9999 9999 0000 0000",  # 正确
        "1234 5678 9012 3456 7890 1234 5678 9012 3456 7890",  # 正确
    ]
    
    # 绘制报文内容
    c.setFont("Courier", 11)
    y_position = height - 5*cm
    line_height = 0.6*cm
    
    for i, line in enumerate(message_lines):
        if y_position < 2*cm:
            c.showPage()
            c.setFont("Courier", 11)
            y_position = height - 2*cm
        
        # 每10行加一个分隔
        if i > 0 and i % 10 == 0:
            y_position -= 0.5*cm
            c.drawString(2*cm, y_position, "-" * 60)
            y_position -= line_height
        
        c.drawString(2*cm, y_position, line)
        y_position -= line_height
    
    c.save()
    print(f"测试 PDF 已生成: {output_path}")
    print("包含 3 处故意错误:")
    print("  1. 第1段第5行第4组: 7890 -> 7891")
    print("  2. 第2段第7行第8组: 0011 -> 0012")
    print("  3. 第3段第4行第3组: 5678 -> 5679")
    print("预期得分: 97 分")

if __name__ == "__main__":
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "test_message.pdf")
    generate_test_pdf(output_path)
