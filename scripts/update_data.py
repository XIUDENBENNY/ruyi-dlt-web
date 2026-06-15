#!/usr/bin/env python3
"""Fetch DLT history and export static JSON/CSV for GitHub Pages."""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "http://datachart.500.com/dlt/history/newinc/history.php?start=07001&end=99999"
ROOT_CSV = ROOT / "data" / "dlt_history.csv"
PAGES_DATA_DIR = ROOT / "docs" / "data"
PAGES_JSON = PAGES_DATA_DIR / "dlt_history.json"
PAGES_CSV = PAGES_DATA_DIR / "dlt_history.csv"

FIELDS = [
    "issue",
    "red1",
    "red2",
    "red3",
    "red4",
    "red5",
    "blue1",
    "blue2",
    "pool_money",
    "first_prize_count",
    "first_prize_money",
    "second_prize_count",
    "second_prize_money",
    "sales_money",
    "date",
]

NUMBER_FIELDS = {"red1", "red2", "red3", "red4", "red5", "blue1", "blue2"}
MONEY_FIELDS = {
    "pool_money",
    "first_prize_count",
    "first_prize_money",
    "second_prize_count",
    "second_prize_money",
    "sales_money",
}


def clean_int(value: str | int | None) -> int:
    text = "" if value is None else str(value)
    text = text.replace(",", "").replace(" ", "").strip()
    if not text or text in {"-", "--"}:
        return 0
    return int(float(text))


def normalize_row(row: dict[str, str]) -> dict[str, object]:
    item: dict[str, object] = {}
    for field in FIELDS:
        value = row.get(field, "")
        if field == "issue":
            item[field] = str(value).strip().zfill(5)
        elif field in NUMBER_FIELDS or field in MONEY_FIELDS:
            item[field] = clean_int(value)
        else:
            item[field] = str(value).strip()
    return item


def fetch_records() -> list[dict[str, object]]:
    response = requests.get(
        SOURCE_URL,
        timeout=30,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0 Safari/537.36"
            )
        },
    )
    response.raise_for_status()
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")
    tbody = soup.find("tbody", id="tdata")
    if not tbody:
        raise RuntimeError("未找到 500彩票网历史数据表 tbody#tdata")

    records: list[dict[str, object]] = []
    for tr in tbody.find_all("tr"):
        cells = [td.get_text(strip=True).replace(",", "") for td in tr.find_all("td")]
        if len(cells) < 15:
            continue
        row = {
            "issue": cells[0],
            "red1": cells[1],
            "red2": cells[2],
            "red3": cells[3],
            "red4": cells[4],
            "red5": cells[5],
            "blue1": cells[6],
            "blue2": cells[7],
            "pool_money": cells[8],
            "first_prize_count": cells[9],
            "first_prize_money": cells[10],
            "second_prize_count": cells[11],
            "second_prize_money": cells[12],
            "sales_money": cells[13],
            "date": cells[14],
        }
        records.append(normalize_row(row))

    if not records:
        raise RuntimeError("抓取结果为空")

    return sorted(records, key=lambda item: int(str(item["issue"])))


def load_local_csv() -> list[dict[str, object]]:
    if not ROOT_CSV.exists():
        raise FileNotFoundError(f"本地 CSV 不存在: {ROOT_CSV}")

    with ROOT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        records = [normalize_row(row) for row in reader]

    if not records:
        raise RuntimeError("本地 CSV 为空")

    return sorted(records, key=lambda item: int(str(item["issue"])))


def write_outputs(records: list[dict[str, object]], source: str) -> None:
    ROOT_CSV.parent.mkdir(parents=True, exist_ok=True)
    PAGES_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with ROOT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)

    with PAGES_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)

    latest = records[-1]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "source_url": SOURCE_URL,
        "count": len(records),
        "latest_issue": latest["issue"],
        "latest_date": latest["date"],
        "records": records,
    }
    PAGES_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def main() -> int:
    source = "500彩票网"
    try:
        records = fetch_records()
    except Exception as exc:
        print(f"在线抓取失败，改用本地 CSV: {exc}", file=sys.stderr)
        records = load_local_csv()
        source = "本地 CSV 兜底"

    write_outputs(records, source)
    latest = records[-1]
    print(
        f"已导出 {len(records)} 期数据，最新 {latest['issue']} / {latest['date']}，来源: {source}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
