#!/usr/bin/env bash
# PPStructureV3 Docker 镜像构建脚本
set -euo pipefail

cd "$(dirname "$0")"

IMAGE_NAME="${IMAGE_NAME:-paddleocr-ppstructure}"
IMAGE_TAG="${IMAGE_TAG:-cpu}"
FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"

echo "=============================================="
echo " 构建 PPStructureV3 OCR Docker 镜像 (CPU)"
echo "=============================================="
echo " 镜像名: ${FULL_IMAGE}"
echo " 开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "----------------------------------------------"
echo ""
echo "提示:"
echo "  - 首次构建会下载 paddlepaddle + paddleocr + 全部模型"
echo "  - 预计耗时 15~30 分钟（取决于网络）"
echo "  - 镜像大小约 2~3 GB"
echo "----------------------------------------------"
echo ""

docker build -t "${FULL_IMAGE}" .

echo ""
echo "=============================================="
echo " 构建完成！"
echo "=============================================="
echo " 镜像: ${FULL_IMAGE}"
echo " 结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo " 启动服务:"
echo "   docker compose up -d"
echo " 或直接运行:"
echo "   docker run -d -p 8080:8080 --name paddleocr ${FULL_IMAGE}"
echo ""
echo " 查看日志:"
echo "   docker logs -f paddleocr-ppstructure"
echo "=============================================="