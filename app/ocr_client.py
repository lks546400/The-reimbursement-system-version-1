import base64
import json
from typing import Any

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.ocr.v20181119 import ocr_client, models


class TencentOcrClient:
    def __init__(self, secret_id: str, secret_key: str, region: str) -> None:
        cred = credential.Credential(secret_id, secret_key)
        http_profile = HttpProfile()
        http_profile.endpoint = "ocr.tencentcloudapi.com"

        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile

        self.client = ocr_client.OcrClient(cred, region, client_profile)

    def general_basic_ocr(self, image_bytes: bytes) -> list[str]:
        req = models.GeneralBasicOCRRequest()
        payload = {
            "ImageBase64": base64.b64encode(image_bytes).decode("utf-8"),
            "LanguageType": "zh",
        }
        req.from_json_string(json.dumps(payload))
        resp = self.client.GeneralBasicOCR(req)
        data = json.loads(resp.to_json_string())
        detections = data.get("TextDetections", [])
        return [x.get("DetectedText", "") for x in detections if x.get("DetectedText")]

    def detect_text(self, image_bytes: bytes) -> list[str]:
        return self.general_basic_ocr(image_bytes)
