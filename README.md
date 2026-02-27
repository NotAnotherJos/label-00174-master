# 报文自动批阅工具

基于 Python 和 PaddleOCR 的手抄报文自动批阅系统，支持 PDF 识别、内容比对、评分及报告生成。

## How to Run

### 使用 Docker Compose（推荐）

1. 确保已安装 Docker 和 Docker Compose

2. 克隆项目并进入目录：
```bash
git clone <repository-url>
cd 174
```

3. 构建并启动服务：
```bash
docker-compose up --build -d
```

4. 访问服务：
   - 前端管理界面：http://localhost:8083
   - 后端 API 文档：http://localhost:8000/docs

5. 停止服务：
```bash
docker-compose down
```

### 单独启动服务

**仅启动后端服务：**
```bash
# 构建并启动后端
docker-compose up --build -d backend

# 查看后端日志
docker-compose logs -f backend

# 停止后端
docker-compose stop backend
```

**仅启动前端服务：**
```bash
# 构建并启动前端（依赖后端）
docker-compose up --build -d frontend-admin

# 查看前端日志
docker-compose logs -f frontend-admin

# 停止前端
docker-compose stop frontend-admin
```

**重启单个服务：**
```bash
docker-compose restart backend
docker-compose restart frontend-admin
```

**重新构建单个服务：**
```bash
docker-compose build backend
docker-compose build frontend-admin
```

### 本地开发运行

**后端：**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端：**
```bash
cd frontend-admin
npm install
npm run dev
```

## Services

| 服务 | 端口 | 描述 |
|------|------|------|
| frontend-admin | 8083 | 管理后台前端界面（Vue.js + Nginx） |
| backend | 8000 | 后端 API 服务（FastAPI + PaddleOCR） |

### API 接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 服务状态检查 |
| GET | `/health` | 健康检查 |
| POST | `/api/upload/pdf` | 上传 PDF 手抄报文 |
| POST | `/api/upload/txt` | 上传 TXT 参照文件 |
| POST | `/api/review` | 开始批阅（需先上传文件） |
| POST | `/api/review/quick` | 快速批阅（一键上传并批阅） |
| GET | `/api/review/{id}` | 获取批阅结果详情 |
| GET | `/api/reviews` | 获取所有批阅记录 |
| GET | `/api/review/{id}/report` | 下载批阅报告（支持 text/json/pdf） |

## 测试账号

本系统无需登录认证，直接访问即可使用。

### 测试文件

项目提供了预置的测试文件，位于 `sample/` 目录下：

| 文件 | 说明 |
|------|------|
| `sample/test_message.pdf` | 测试用 PDF 报文文件（包含 3 处故意错误） |
| `sample/standard_reference.txt` | TXT 标准参照文件（300 组数字，3 段） |
| `sample/generate_test_pdf.py` | 测试 PDF 生成脚本 |

### 测试步骤

1. 启动服务后访问：http://localhost:8083

2. 上传测试文件：
   - **PDF 文件**：选择 `sample/test_message.pdf`
   - **TXT 文件**：选择 `sample/standard_reference.txt`

3. 点击"开始批阅"按钮

4. 查看预期结果：
   - **得分**：97 分
   - **错误数**：3 处
   - **错误详情**：
     | 位置 | 提交值 | 正确值 |
     |------|--------|--------|
     | 第1段-第5行-第4组 | 7891 | 7890 |
     | 第2段-第7行-第8组 | 0012 | 0011 |
     | 第3段-第4行-第3组 | 5679 | 5678 |

### 使用 API 测试

```bash
# 快速批阅测试
curl -X POST "http://localhost:8000/api/review/quick" \
  -F "pdf_file=@sample/test_message.pdf" \
  -F "txt_file=@sample/standard_reference.txt"
```

### 生成自定义测试 PDF

可以修改 `sample/generate_test_pdf.py` 生成包含不同错误的测试文件：

```bash
cd sample
pip install reportlab
python generate_test_pdf.py
```

### 报文格式说明

**TXT 参照文件格式：**
- 前 1-3 行为头部信息（可选，包含组数、时间等）
- 主体内容：每组 4 个数字，每行 10 组，共 30 行（3 段 × 10 行）
- 数字之间可用空格分隔

```
报文标准参照
组数：300组
时间：2026-01-29 09:00:00

1234 5678 9012 3456 7890 1234 5678 9012 3456 7890
2345 6789 0123 4567 8901 2345 6789 0123 4567 8901
...
```

## 题目内容
开发一个基于Python的报文自动批阅工具，该工具应具备以下功能和特性：1. 输入处理：- 接收扫描后的PDF格式手抄报文文件，该文件内容为表格形式- 接收TXT格式的参照标准报文文件2. PDF内容提取与解析：- 准确识别并提取PDF中的表格内容- 正确解析报文结构：- 识别并提取前三行的报文头部信息，包括但不限于报文组数、时间等关键信息- 解析报文主体内容，其中数字以4个为一组，每行包含10组数字- 识别报文分段结构，每100组数字（即10行）为1段，通常包含3段3. 比对与错误检测：- 将PDF提取的报文内容与TXT参照报文进行逐组比对- 精确识别并记录所有错误位置及具体内容差异4. 评分系统：- 实现评分机制，总分100分，每处错误扣1分- 确保评分计算准确反映错误数量5. 输出报告：- 生成详细的错误信息报告，包含错误位置、原文内容与参照内容对比- 提供总体评分结果- 支持将批阅结果以清晰易读的格式输出（可考虑文本报告或生成带批注的PDF）6. 技术要求：- 确保PDF文字识别准确率，特别是对手写数字的识别- 处理可能的格式变异和识别误差- 优化算法以处理不同质量的扫描PDF文件- 保证工具运行稳定，处理速度合理工具应具备良好的错误处理机制，能够处理PDF识别失败、格式异常等特殊情况，并提供清晰的错误提示。

### 项目需求

开发一个基于 Python 的报文自动批阅工具，该工具应具备以下功能和特性：

#### 1. 输入处理
- 接收扫描后的 PDF 格式手抄报文文件，该文件内容为表格形式
- 接收 TXT 格式的参照标准报文文件

#### 2. PDF 内容提取与解析
- 准确识别并提取 PDF 中的表格内容
- 正确解析报文结构：
  - 识别并提取前三行的报文头部信息，包括但不限于报文组数、时间等关键信息
  - 解析报文主体内容，其中数字以 4 个为一组，每行包含 10 组数字
  - 识别报文分段结构，每 100 组数字（即 10 行）为 1 段，通常包含 3 段

#### 3. 比对与错误检测
- 将 PDF 提取的报文内容与 TXT 参照报文进行逐组比对
- 精确识别并记录所有错误位置及具体内容差异

#### 4. 评分系统
- 实现评分机制，总分 100 分，每处错误扣 1 分
- 确保评分计算准确反映错误数量

#### 5. 输出报告
- 生成详细的错误信息报告，包含错误位置、原文内容与参照内容对比
- 提供总体评分结果
- 支持将批阅结果以清晰易读的格式输出（可考虑文本报告或生成带批注的 PDF）

#### 6. 技术要求
- 确保 PDF 文字识别准确率，特别是对手写数字的识别
- 处理可能的格式变异和识别误差
- 优化算法以处理不同质量的扫描 PDF 文件
- 保证工具运行稳定，处理速度合理

工具应具备良好的错误处理机制，能够处理 PDF 识别失败、格式异常等特殊情况，并提供清晰的错误提示。

---

## 技术架构

### 后端技术栈
- **框架**: FastAPI
- **OCR 引擎**: PaddleOCR（支持手写数字识别）
- **PDF 处理**: PyMuPDF (fitz)
- **图像处理**: OpenCV, Pillow
- **报告生成**: ReportLab

### 前端技术栈
- **框架**: Vue.js 3
- **构建工具**: Vite
- **HTTP 客户端**: Axios
- **UI**: 自定义深色主题

### 部署
- **容器化**: Docker
- **编排**: Docker Compose
- **Web 服务器**: Nginx（前端静态文件服务 + API 反向代理）

## 项目结构

```
174/
├── backend/                    # 后端项目
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 入口
│   │   ├── config.py          # 配置模块
│   │   ├── models.py          # 数据模型
│   │   ├── ocr_processor.py   # OCR 处理模块
│   │   ├── message_parser.py  # 报文解析模块
│   │   ├── comparator.py      # 比对模块
│   │   ├── scorer.py          # 评分模块
│   │   ├── report_generator.py# 报告生成模块
│   │   └── review_service.py  # 批阅服务
│   ├── uploads/               # 上传文件目录
│   ├── templates/             # 模板目录
│   ├── requirements.txt       # Python 依赖
│   └── Dockerfile
├── frontend-admin/            # 前端管理后台
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   └── style.css
│   ├── public/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml         # Docker 编排配置
├── .gitignore
└── README.md
```

## 核心功能模块说明

### OCR 处理器 (ocr_processor.py)
- PDF 转图像（高分辨率）
- 图像预处理（灰度化、二值化、去噪）
- 表格区域检测
- 文本识别与位置排序

### 报文解析器 (message_parser.py)
- 头部信息解析（组数、时间等）
- 数字组提取（4 位一组）
- 行列结构重建（每行 10 组，每段 10 行）

### 比对器 (comparator.py)
- 逐组内容比对
- OCR 常见错误自动修正（O→0, l→1 等）
- 错误类型分类（错误/缺失/多余）

### 评分器 (scorer.py)
- 基于错误数量计分
- 等级评定（A/B/C/D/F）
- 反馈信息生成

### 报告生成器 (report_generator.py)
- 文本报告
- JSON 报告
- PDF 报告（含表格）

## 许可证

MIT License
