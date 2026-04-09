#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import get_missing_required_configs


if __name__ == "__main__":
    result = get_missing_required_configs()
    if not result.missing:
        print("✅ 环境变量检查通过")
    else:
        print("❌ 缺少以下必填配置：")
        for item in result.missing:
            print(f"- {item}")
        raise SystemExit(1)
