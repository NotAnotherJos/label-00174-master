"""PDF OCR处理模块 - 使用PaddleOCR进行手写数字识别"""
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import cv2
from PIL import Image
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class OCRProcessor:
    """PDF OCR处理器"""
    
    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu
        self._ocr = None
    
    @property
    def ocr(self):
        """延迟加载OCR引擎"""
        if self._ocr is None:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang='ch',
                use_gpu=self.use_gpu,
                show_log=False,
                det_db_thresh=0.3,
                det_db_box_thresh=0.5,
                rec_batch_num=6,
            )
        return self._ocr
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        """
        直接从PDF提取文本（用于数字化PDF，非扫描件）
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            行列表
        """
        lines = []
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                page_lines = text.strip().split('\n')
                lines.extend([line.strip() for line in page_lines if line.strip()])
            doc.close()
            logger.info(f"PDF文本提取完成，共 {len(lines)} 行")
        except Exception as e:
            logger.error(f"PDF文本提取失败: {str(e)}")
            raise
        return lines
    
    def pdf_to_images(self, pdf_path: str, dpi: int = 300) -> List[np.ndarray]:
        """
        将PDF转换为图像列表
        
        Args:
            pdf_path: PDF文件路径
            dpi: 转换分辨率
            
        Returns:
            图像数组列表
        """
        images = []
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # 高分辨率渲染以提高OCR准确率
                mat = fitz.Matrix(dpi / 72, dpi / 72)
                pix = page.get_pixmap(matrix=mat)
                
                # 转换为numpy数组
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                    pix.height, pix.width, pix.n
                )
                
                # 转换为BGR格式（OpenCV标准）
                if pix.n == 4:  # RGBA
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                elif pix.n == 3:  # RGB
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                
                images.append(img)
            doc.close()
            logger.info(f"成功将PDF转换为 {len(images)} 页图像")
        except Exception as e:
            logger.error(f"PDF转换失败: {str(e)}")
            raise
        
        return images
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理以提高OCR准确率
        
        Args:
            image: 原始图像
            
        Returns:
            预处理后的图像
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 自适应二值化处理手写字迹
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # 去噪
        denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
        
        # 转回BGR以供OCR使用
        processed = cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR)
        
        return processed
    
    def detect_table_region(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        检测表格区域
        
        Args:
            image: 输入图像
            
        Returns:
            表格区域图像，如果未检测到返回原图
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 边缘检测
        edges = cv2.Canny(gray, 50, 150)
        
        # 查找轮廓
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        if contours:
            # 找到最大轮廓（假设是表格）
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # 确保区域足够大
            if w > image.shape[1] * 0.3 and h > image.shape[0] * 0.3:
                # 添加边距
                margin = 10
                x = max(0, x - margin)
                y = max(0, y - margin)
                w = min(image.shape[1] - x, w + 2 * margin)
                h = min(image.shape[0] - y, h + 2 * margin)
                
                return image[y:y+h, x:x+w]
        
        return image
    
    def extract_text_from_image(self, image: np.ndarray) -> List[Tuple[str, float, List]]:
        """
        从图像中提取文本
        
        Args:
            image: 输入图像
            
        Returns:
            (文本, 置信度, 位置) 元组列表
        """
        results = []
        
        try:
            # 预处理图像
            processed = self.preprocess_image(image)
            
            # OCR识别
            ocr_result = self.ocr.ocr(processed, cls=True)
            
            if ocr_result and ocr_result[0]:
                for line in ocr_result[0]:
                    box = line[0]  # 文本框位置
                    text = line[1][0]  # 识别的文本
                    confidence = line[1][1]  # 置信度
                    
                    # 计算文本框中心y坐标用于排序
                    center_y = (box[0][1] + box[2][1]) / 2
                    center_x = (box[0][0] + box[2][0]) / 2
                    
                    results.append((text, confidence, [center_x, center_y]))
            
            # 按y坐标排序（从上到下），然后按x坐标排序（从左到右）
            results.sort(key=lambda x: (x[2][1], x[2][0]))
            
            logger.info(f"识别到 {len(results)} 个文本区域")
            
        except Exception as e:
            logger.error(f"OCR识别失败: {str(e)}")
            raise
        
        return results
    
    def process_pdf(self, pdf_path: str, use_ocr: bool = True) -> Tuple[List[str], List[Tuple[str, float]]]:
        """
        处理PDF文件，提取所有文本
        
        Args:
            pdf_path: PDF文件路径
            use_ocr: 是否使用OCR（对于数字化PDF可以设为False）
            
        Returns:
            (行列表, (文本, 置信度)元组列表)
        """
        # 首先尝试直接提取文本
        try:
            lines = self.extract_text_from_pdf(pdf_path)
            # 检查是否提取到足够的数字内容
            total_digits = sum(len([c for c in line if c.isdigit()]) for line in lines)
            if total_digits >= 100:  # 如果有足够多的数字，认为是数字化PDF
                logger.info(f"使用直接文本提取，找到 {total_digits} 个数字")
                return lines, [(line, 1.0) for line in lines]
        except Exception as e:
            logger.warning(f"直接文本提取失败，尝试OCR: {str(e)}")
        
        # 如果直接提取失败或内容不足，使用OCR
        if not use_ocr:
            return lines, [(line, 1.0) for line in lines]
        
        all_lines = []
        all_results = []
        
        # 转换PDF为图像
        images = self.pdf_to_images(pdf_path)
        
        for page_idx, image in enumerate(images):
            logger.info(f"处理第 {page_idx + 1} 页...")
            
            # 检测表格区域
            table_region = self.detect_table_region(image)
            
            # 提取文本
            results = self.extract_text_from_image(table_region)
            
            # 组织成行
            current_line = []
            current_y = -1
            y_threshold = 30  # 同一行的y坐标阈值
            
            for text, confidence, pos in results:
                if current_y < 0:
                    current_y = pos[1]
                
                if abs(pos[1] - current_y) < y_threshold:
                    current_line.append(text)
                else:
                    if current_line:
                        all_lines.append(" ".join(current_line))
                    current_line = [text]
                    current_y = pos[1]
                
                all_results.append((text, confidence))
            
            if current_line:
                all_lines.append(" ".join(current_line))
        
        logger.info(f"PDF处理完成，共提取 {len(all_lines)} 行文本")
        return all_lines, all_results


def create_ocr_processor(use_gpu: bool = False) -> OCRProcessor:
    """创建OCR处理器实例"""
    return OCRProcessor(use_gpu=use_gpu)
