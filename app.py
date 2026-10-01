#!/usr/bin/env python3
"""
PPStructureV3 OCR HTTP Service
FastAPI wrapper around PaddleOCR PPStructureV3 pipeline.
"""
import base64
import io
import os
import logging
import uuid
from contextlib import asynccontextmanager

import numpy as np
from PIL import Image
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from paddleocr import PPStructureV3
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Pipeline singleton (initialized at startup) ──────────────────
_pipeline = None


def _json_safe(obj):
    """Recursively convert numpy types to native Python types."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pipeline
    logger.info("Initializing PPStructureV3 pipeline at startup...")
    _pipeline = PPStructureV3()
    logger.info("PPStructureV3 pipeline ready.")
    yield
    if _pipeline is not None:
        _pipeline.close()
        logger.info("Pipeline closed.")


app = FastAPI(title="PPStructureV3 OCR", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return JSONResponse({
        "logId": str(uuid.uuid4()),
        "errorCode": 0,
        "errorMsg": "Healthy",
    })


@app.post("/layout-parsing")
async def layout_parsing(request: Request):
    log_id = str(uuid.uuid4())
    try:
        body = await request.json()
        b64_file = body.get("file")
        if not b64_file:
            raise HTTPException(400, "Missing 'file' field")

        # Determine file type: 0=PDF, 1=image
        file_type = body.get("fileType", None)
        if file_type is None:
            try:
                header = base64.b64decode(b64_file[:10])
                file_type = 0 if header[:5] == b"%PDF-" else 1
            except Exception:
                file_type = 1

        data = base64.b64decode(b64_file)
        if file_type != 0:
            # Image: decode to numpy array
            data = np.array(Image.open(io.BytesIO(data)).convert("RGB"))

        logger.info("Processing request %s (fileType=%d)", log_id, file_type)
        results = _pipeline.predict(data)

        output = [_json_safe(r.json) for r in results]

        return JSONResponse({
            "logId": log_id,
            "errorCode": 0,
            "errorMsg": "Success",
            "result": output,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing request %s", log_id)
        return JSONResponse({
            "logId": log_id,
            "errorCode": 500,
            "errorMsg": str(e),
        }, status_code=500)


def main():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    logger.info("Starting PPStructureV3 OCR server on %s:%d", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()