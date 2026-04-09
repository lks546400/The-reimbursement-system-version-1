import base64
import json
from typing import Any

import httpx


class FeishuClient:
    def __init__(self, app_id: str, app_secret: str) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.base = "https://open.feishu.cn/open-apis"

    async def get_tenant_access_token(self) -> str:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{self.base}/auth/v3/tenant_access_token/internal",
                json={"app_id": self.app_id, "app_secret": self.app_secret},
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                raise RuntimeError(f"获取飞书 token 失败: {data}")
            return data["tenant_access_token"]

    async def download_image_bytes(self, tenant_access_token: str, message_id: str, image_key: str) -> bytes:
        headers = {"Authorization": f"Bearer {tenant_access_token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            # 新版资源下载接口
            resp = await client.get(
                f"{self.base}/im/v1/messages/{message_id}/resources/{image_key}",
                params={"type": "image"},
                headers=headers,
            )
            if resp.status_code == 200 and resp.content:
                return resp.content

            # 兼容旧版图片接口
            old = await client.get(
                f"{self.base}/image/v4/get",
                params={"image_key": image_key},
                headers=headers,
            )
            old.raise_for_status()
            return old.content

    async def reply_text(self, tenant_access_token: str, message_id: str, text: str) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {tenant_access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{self.base}/im/v1/messages/{message_id}/reply",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                raise RuntimeError(f"飞书回复失败: {data}")
            return data


def decode_event_content(content: str) -> dict[str, Any]:
    # 飞书 content 是 JSON 字符串
    try:
        return json.loads(content or "{}")
    except json.JSONDecodeError:
        return {}


def maybe_decode_base64_image(raw: bytes) -> bytes:
    # 某些场景返回 base64 字节串，做兼容
    try:
        text = raw.decode("utf-8")
        if len(text) > 100 and all(c.isalnum() or c in "+/=\n\r" for c in text[:200]):
            return base64.b64decode(text)
    except Exception:
        pass
    return raw
