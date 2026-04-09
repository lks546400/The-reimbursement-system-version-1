import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Any


CATEGORY_RULES: list[tuple[str, str]] = [
    (r"(地铁|出租|滴滴|高铁|火车|机票|航班|打车)", "交通"),
    (r"(酒店|宾馆|住宿|旅店)", "住宿"),
    (r"(餐|外卖|咖啡|饮品|小吃)", "餐饮"),
]


def classify(text: str) -> str:
    for pattern, cat in CATEGORY_RULES:
        if re.search(pattern, text):
            return cat
    return "其他"


def extract_amount(text: str) -> float | None:
    # 优先匹配“合计/金额/实收”等关键词附近金额
    candidates = re.findall(r"(?:合计|金额|实收|总计)?\s*[¥￥]?\s*(\d+\.\d{1,2})", text)
    if not candidates:
        return None
    # 取最大值，避免识别出小计干扰
    nums = [float(x) for x in candidates]
    return max(nums) if nums else None


def extract_date(text: str) -> str:
    patterns = [
        r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})",
        r"(20\d{2})(\d{2})(\d{2})",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            y, mth, d = m.groups()
            return f"{int(y):04d}-{int(mth):02d}-{int(d):02d}"
    return datetime.now().strftime("%Y-%m-%d")


def extract_vendor(text_lines: list[str]) -> str:
    # 取首个相对像商户名的行
    for line in text_lines[:5]:
        x = line.strip()
        if len(x) >= 3 and not re.search(r"(发票|金额|日期|电话|地址)", x):
            return x[:30]
    return "未知商户"


def build_record(text_lines: list[str]) -> dict[str, Any]:
    joined = "\n".join(text_lines)
    amount = extract_amount(joined)
    date = extract_date(joined)
    vendor = extract_vendor(text_lines)
    category = classify(joined)
    return {
        "date": date,
        "amount": amount,
        "vendor": vendor,
        "category": category,
        "raw_text": joined,
    }


def ensure_dirs(storage_dir: str, data_dir: str) -> None:
    Path(storage_dir).mkdir(parents=True, exist_ok=True)
    Path(data_dir).mkdir(parents=True, exist_ok=True)


def save_image(storage_dir: str, record: dict[str, Any], image_bytes: bytes, ext: str = "jpg") -> str:
    date = record["date"]
    y, m, _ = date.split("-")
    category = record["category"]
    amount = "0.00" if record["amount"] is None else f"{record['amount']:.2f}"
    vendor = re.sub(r"[^\w\u4e00-\u9fa5-]", "", record["vendor"])[:20] or "未知商户"
    folder = Path(storage_dir) / y / m / category
    folder.mkdir(parents=True, exist_ok=True)
    file_name = f"{date}_{category}_{amount}_{vendor}.{ext}"
    path = folder / file_name
    path.write_bytes(image_bytes)
    return str(path)


def append_csv(data_dir: str, row: dict[str, Any]) -> str:
    file_path = Path(data_dir) / "reimbursement_records.csv"
    exists = file_path.exists()
    with file_path.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["date", "amount", "vendor", "category", "file_path", "source_message_id"],
        )
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    return str(file_path)
