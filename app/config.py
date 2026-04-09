import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    feishu_app_id: str
    feishu_app_secret: str
    feishu_verification_token: str
    tencent_secret_id: str
    tencent_secret_key: str
    tencent_region: str
    storage_dir: str
    data_dir: str
    ocr_mode: str


@dataclass(frozen=True)
class MissingConfigResult:
    missing: list[str]


BASE_REQUIRED_ENV_MAP = {
    "FEISHU_APP_ID": "飞书应用 App ID",
    "FEISHU_APP_SECRET": "飞书应用 App Secret",
    "FEISHU_VERIFICATION_TOKEN": "飞书事件订阅 Verification Token",
}

TENCENT_REQUIRED_ENV_MAP = {
    "TENCENT_SECRET_ID": "腾讯云 SecretId",
    "TENCENT_SECRET_KEY": "腾讯云 SecretKey",
}


def _getenv(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def get_settings() -> Settings:
    return Settings(
        feishu_app_id=_getenv("FEISHU_APP_ID"),
        feishu_app_secret=_getenv("FEISHU_APP_SECRET"),
        feishu_verification_token=_getenv("FEISHU_VERIFICATION_TOKEN"),
        tencent_secret_id=_getenv("TENCENT_SECRET_ID"),
        tencent_secret_key=_getenv("TENCENT_SECRET_KEY"),
        tencent_region=_getenv("TENCENT_REGION", "ap-guangzhou"),
        storage_dir=_getenv("APP_STORAGE_DIR", "storage"),
        data_dir=_getenv("APP_DATA_DIR", "data"),
        ocr_mode=_getenv("OCR_MODE", "mock").lower(),
    )


def get_missing_required_configs() -> MissingConfigResult:
    settings = get_settings()
    required = dict(BASE_REQUIRED_ENV_MAP)
    if settings.ocr_mode == "tencent":
        required.update(TENCENT_REQUIRED_ENV_MAP)

    missing: list[str] = []
    for key, desc in required.items():
        if not _getenv(key):
            missing.append(f"{key}（{desc}）")
    return MissingConfigResult(missing=missing)

