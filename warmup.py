#!/usr/bin/env python3
"""
Docker build 阶段的模型预热脚本。
创建 PPStructureV3 管线一次，触发所有模型下载并完成 JIT 编译。
"""
import os
import sys
import numpy as np

os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

print("=" * 60)
print("PPStructureV3 模型预热开始")
print("这将下载并缓存所有需要的模型文件...")
print("=" * 60)

try:
    from paddleocr import PPStructureV3

    print("\n[1/2] 正在创建 PPStructureV3 管线...")
    pipeline = PPStructureV3()
    print("  ✓ 管线创建成功")

    print("\n[2/2] 正在运行预热推理（触发 JIT 编译）...")
    img = np.ones((100, 200, 3), dtype=np.uint8) * 255
    result = pipeline.predict(img)
    print(f"  ✓ 预热推理完成，结果页数: {len(result)}")

    pipeline.close()

    print("\n" + "=" * 60)
    print("PPStructureV3 模型预热成功！")
    print("模型缓存位置: /root/.paddlex/official_models/")
    print("=" * 60)

except Exception as e:
    print(f"\n[WARN] 预热过程出现异常: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    print(
        "模型将在运行时首次调用时自动下载（会增加首次请求延迟）。",
        file=sys.stderr,
    )