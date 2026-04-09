from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, File, HTTPException, Request, UploadFile

from app.config import get_missing_required_configs, get_settings
from app.feishu_client import FeishuClient, decode_event_content, maybe_decode_base64_image
from app.ocr_client import TencentOcrClient
from app.parser import append_csv, build_record, ensure_dirs, save_image

app = FastAPI(title="Reimbursement Assistant")


@app.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    missing_count = len(get_missing_required_configs().missing)
    return {
        "status": "ok",
        "ocr_mode": settings.ocr_mode,
        "missing_required_config_count": str(missing_count),
    }


def detect_text_lines(image_bytes: bytes) -> list[str]:
    settings = get_settings()
    if settings.ocr_mode == "mock":
        today = datetime.now().strftime("%Y-%m-%d")
        return [
            "测试商户(模拟)",
            f"日期 {today}",
            "金额 88.00",
            "餐饮",
        ]

    ocr = TencentOcrClient(
        settings.tencent_secret_id,
        settings.tencent_secret_key,
        settings.tencent_region,
    )
    return ocr.detect_text(image_bytes)


def process_image_bytes(image_bytes: bytes, source_message_id: str = "manual-upload") -> dict:
    settings = get_settings()
    ensure_dirs(settings.storage_dir, settings.data_dir)

    text_lines = detect_text_lines(image_bytes)
    record = build_record(text_lines)

    file_path = save_image(settings.storage_dir, record, image_bytes, ext="jpg")
    append_csv(
        settings.data_dir,
        {
            "date": record["date"],
            "amount": "" if record["amount"] is None else f"{record['amount']:.2f}",
            "vendor": record["vendor"],
            "category": record["category"],
            "file_path": file_path,
            "source_message_id": source_message_id,
        },
    )

    amount = "未识别" if record["amount"] is None else f"¥{record['amount']:.2f}"
    summary = (
        "识别完成\n"
        f"模式：{settings.ocr_mode}\n"
        f"日期：{record['date']}\n"
        f"金额：{amount}\n"
        f"商户：{record['vendor']}\n"
        f"分类：{record['category']}\n"
        f"归档：{file_path}"
    )

    return {
        "record": record,
        "file_path": file_path,
        "summary": summary,
    }


@app.post("/feishu/events")
async def feishu_events(req: Request) -> dict:
    settings = get_settings()
    payload = await req.json()

    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge", "")}

    header = payload.get("header", {})
    event = payload.get("event", {})

    if header.get("token") != settings.feishu_verification_token:
        raise HTTPException(status_code=401, detail="invalid token")

    if header.get("event_type") != "im.message.receive_v1":
        return {"ok": True, "msg": "ignore event type"}

    message = event.get("message", {})
    if message.get("message_type") != "image":
        return {"ok": True, "msg": "ignore non-image"}

    message_id = message.get("message_id", "")
    content = decode_event_content(message.get("content", ""))
    image_key = content.get("image_key")
    if not message_id or not image_key:
        return {"ok": True, "msg": "missing image key"}

    missing = get_missing_required_configs().missing
    if missing:
        raise HTTPException(status_code=500, detail=f"缺少配置: {', '.join(missing)}")

    feishu = FeishuClient(settings.feishu_app_id, settings.feishu_app_secret)
    tenant_access_token = await feishu.get_tenant_access_token()

    try:
        image_bytes = await feishu.download_image_bytes(tenant_access_token, message_id, image_key)
        image_bytes = maybe_decode_base64_image(image_bytes)
        result = process_image_bytes(image_bytes, source_message_id=message_id)
        await feishu.reply_text(tenant_access_token, message_id, result["summary"])
        return {"ok": True}
    except Exception as e:
        try:
            await feishu.reply_text(tenant_access_token, message_id, f"处理失败：{str(e)}")
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}") from e


@app.post("/debug/mock-image")
async def debug_mock_image(file: UploadFile = File(...)) -> dict:
    missing = get_missing_required_configs().missing
    if missing:
        raise HTTPException(status_code=500, detail=f"缺少配置: {', '.join(missing)}")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="上传文件为空")

    try:
        result = process_image_bytes(content, source_message_id="debug-mock-image")
        return {
            "ok": True,
            "date": result["record"]["date"],
            "amount": result["record"]["amount"],
            "vendor": result["record"]["vendor"],
            "category": result["record"]["category"],
            "file_path": result["file_path"],
            "summary": result["summary"],
            "note": "该接口仅用于本地联调",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}") from e
