# PPStructureV3 OCR 服务 Docker 部署
# 基于 PP-StructureV3 管线：文字识别 + 表格 + 公式 + 版面 + 印章 + 图表
FROM ubuntu_py:24.04

LABEL maintainer="ocr"
LABEL description="PaddleOCR PP-StructureV3 full pipeline OCR service (CPU)"

# ============================================================
# 系统依赖
# ============================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libopenblas0 \
    libgl1 \
    libglib2.0-0t64 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgflags-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# Python 依赖
# ============================================================
# 允许在 Ubuntu 24.04 (PEP 668) 系统 Python 上安装
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# 先装大包 paddlepaddle（变化少），再装 paddleocr（充分利用 Docker 层缓存）
RUN pip3 install --no-cache-dir paddlepaddle==3.2.2

RUN pip3 install --no-cache-dir paddleocr==3.7.0

RUN pip3 install --no-cache-dir "paddlex[ocr]==3.7.2"

# PaddleX 服务化插件
RUN paddlex --install serving --yes

# ============================================================
# 模型预热（build 时下载所有模型到镜像内）
# ============================================================
ENV PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

COPY warmup.py /tmp/warmup.py
# 模型下载 + JIT 编译预热（此步骤耗时较长，约 15-30 分钟）
RUN python3 /tmp/warmup.py && rm /tmp/warmup.py

# ============================================================
# 应用代码
# ============================================================
COPY app.py /app/app.py
WORKDIR /app

# ============================================================
# 运行时配置
# ============================================================
ENV HOST=0.0.0.0
ENV PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python3", "/app/app.py"]