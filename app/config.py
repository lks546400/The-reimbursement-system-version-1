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
    )
