from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request

from app.config import get_settings
from app.feishu_client import FeishuClient, decode_event_content, maybe_decode_base64_image
from app.ocr_client import TencentOcrClient
from app.parser import append_csv, build_record, ensure_dirs, save_image

app = FastAPI(title="Reimbursement Assistant")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/feishu/events")
async def feishu_events(req: Request) -> dict:
    settings = get_settings()
    payload = await req.json()

    # 飞书 URL 验证
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge", "")}

    header = payload.get("header", {})
    event = payload.get("event", {})

    # 基础 token 校验（首版）
    if header.get("token") != settings.feishu_verification_token:
        raise HTTPException(status_code=401, detail="invalid token")

    if header.get("event_type") != "im.message.receive_v1":
        return {"ok": True, "msg": "ignore event type"}

    message = event.get("message", {})
    message_type = message.get("message_type")
    if message_type != "image":
        return {"ok": True, "msg": "ignore non-image"}

    message_id = message.get("message_id", "")
    content = decode_event_content(message.get("content", ""))
    image_key = content.get("image_key")
    if not message_id or not image_key:
        return {"ok": True, "msg": "missing image key"}

    ensure_dirs(settings.storage_dir, settings.data_dir)

    feishu = FeishuClient(settings.feishu_app_id, settings.feishu_app_secret)
    tenant_access_token = await feishu.get_tenant_access_token()

    image_bytes = await feishu.download_image_bytes(tenant_access_token, message_id, image_key)
    image_bytes = maybe_decode_base64_image(image_bytes)

    ocr = TencentOcrClient(
        settings.tencent_secret_id,
        settings.tencent_secret_key,
        settings.tencent_region,
    )
    text_lines = ocr.detect_text(image_bytes)
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
            "source_message_id": message_id,
        },
    )

    amount = "未识别" if record["amount"] is None else f"¥{record['amount']:.2f}"
    reply = (
        "识别完成\n"
        f"日期：{record['date']}\n"
        f"金额：{amount}\n"
        f"商户：{record['vendor']}\n"
        f"分类：{record['category']}\n"
        f"归档：{file_path}"
    )
    await feishu.reply_text(tenant_access_token, message_id, reply)

    return {"ok": True}
