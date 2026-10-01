# PPStructureV3 OCR 服务 (Docker CPU 版)

基于 **PaddleOCR PP-StructureV3** 管线的一键部署 OCR 服务，支持：

- **文字识别（OCR）** — 印刷体 + 手写体，中/英/日/韩等 50+ 语言
- **表格识别** — 有线/无线表格 → HTML
- **公式识别** → LaTeX
- **版面分析** — 正文/标题/页眉页脚/图片/表格区域检测，支持 20 种版面元素
- **印章识别** — 印章文字检测与识别
- **图表解析** — 图表内容理解
- **输出格式** — Markdown / JSON

---

## 快速开始

### 1. 构建镜像

```bash
bash build.sh
```

首次构建会下载 paddlepaddle + paddleocr + 全部模型（14 个），预计 **20~40 分钟**。

### 2. 启动服务

```bash
docker compose up -d
```

### 3. 检查状态

```bash
docker logs -f paddleocr-ppstructure
```

看到 `PPStructureV3 pipeline ready` 即启动成功（初始化约 60 秒）。

### 4. 健康检查

```bash
curl http://localhost:8080/health
```

---

## API 说明

### 文档解析（主接口）

```
POST http://localhost:8080/layout-parsing
Content-Type: application/json
```

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | `string` | 是 | 图片/PDF 的 Base64 编码，或可访问的 URL |
| `fileType` | `integer` | 否 | `0` = PDF，`1` = 图像文件。不填则自动推断 |

**示例请求（Base64 图片）：**

```bash
curl -X POST http://localhost:8080/layout-parsing \
  -H "Content-Type: application/json" \
  -d '{
    "file": "'"$(base64 -w0 /path/to/document.jpg)"'",
    "fileType": 1
  }'
```

**示例请求（图片 URL）：**

```bash
curl -X POST http://localhost:8080/layout-parsing \
  -H "Content-Type: application/json" \
  -d '{
    "file": "https://example.com/document.pdf",
    "fileType": 0
  }'
```

**响应体：**

```json
{
  "logId": "uuid",
  "errorCode": 0,
  "errorMsg": "Success",
  "result": {
    "prunedResult": {
      "layoutParsingResults": [
        {
          "blockLabel": "text",
          "blockContent": "识别出的文字内容...",
          "blockBbox": [x1, y1, x2, y2]
        },
        {
          "blockLabel": "table",
          "blockContent": "<table>...</table>"
        }
      ]
    },
    "markdown": {
      "text": "# 转换后的 Markdown 文本...",
      "images": { "img_0.png": "<base64>" }
    },
    "outputImages": { "layout": "<base64>", "ocr": "<base64>" }
  }
}
```

---

## 常用操作

### 查看日志

```bash
docker logs -f paddleocr-ppstructure
```

### 停止服务

```bash
docker compose down
```

### 修改端口

编辑 `.env` 文件：

```
PORT=9090
```

修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "9090:8080"
```

然后重启：

```bash
docker compose up -d
```

### 进入容器调试

```bash
docker exec -it paddleocr-ppstructure bash
```

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HOST` | `0.0.0.0` | 绑定地址 |
| `PORT` | `8080` | 服务监听端口 |

---

## 性能参考（CPU）

| 场景 | 单页耗时 | 说明 |
|------|----------|------|
| 简单图片（CPU） | ~30-60s | 纯文字/简单版面 |
| 含表格文档（CPU） | ~35-90s | 含有线/无线表格 |
| 含公式论文（CPU） | ~40-120s | 含数学公式 |
| 复杂版面（CPU） | ~50-180s | 多栏、图片、表格混合 |

> 以上为 4 核 CPU 实测数据，实际耗时取决于图片尺寸和内容复杂度。
> 内存需求：建议 **8 GB+**

---

## Python 客户端示例

```python
import base64
import json
import requests

def ocr_document(file_path: str, server_url: str = "http://localhost:8080"):
    """调用 PPStructureV3 服务解析文档"""
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    # 推断文件类型
    ext = file_path.lower().rsplit(".", 1)[-1]
    file_type = 0 if ext == "pdf" else 1

    resp = requests.post(
        f"{server_url}/layout-parsing",
        json={"file": b64, "fileType": file_type},
        timeout=300,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("errorCode") != 0:
        raise Exception(f"API error: {data.get('errorMsg')}")

    return data["result"]

# 使用
result = ocr_document("document.pdf")
print(result["markdown"]["text"])
```

---

## 镜像信息

| 项目 | 说明 |
|------|------|
| 基础镜像 | ubuntu_py:24.04 |
| Python | 3.12 |
| paddlepaddle | 3.2.2 (CPU) |
| paddleocr | 3.7.0 |
| paddlex | 3.7.2 |
| 推理引擎 | paddle_static |
| 镜像大小 | 5.23 GB |
| 端口 | 8080 |

---

## 故障排查

### 启动时模型下载失败

检查网络连接。模型从 ModelScope/百度网盘自动下载。
可设置 `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` 跳过连通性检查。

### 内存不足

建议至少 8 GB 可用内存。如果机器内存较小，可限制容器：

```yaml
# docker-compose.yml
services:
  paddleocr-ppstructure:
    deploy:
      resources:
        limits:
          memory: 6g
```

### 首次启动较慢

首次启动时管线初始化需要约 60 秒（JIT 编译 + 模型加载），后续请求在 30-180 秒之间。

### 多页 PDF 处理

编辑 `app.py` 中的 `pipeline.predict()` 调用，PDF 文件自动按页处理。