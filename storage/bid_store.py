import sqlite3
import logging
from typing import List
from datetime import datetime

from crawler.bid_scraper import BidItem

logger = logging.getLogger(__name__)

DB_PATH = "data/bids.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_bids (
                bid_no      TEXT PRIMARY KEY,
                title       TEXT,
                category    TEXT,
                field       TEXT,
                bid_method  TEXT,
                start_date  TEXT,
                end_date    TEXT,
                status      TEXT,
                detail_url  TEXT,
                first_seen  TEXT
            )
        """)
    logger.info("DB 초기화 완료: %s", DB_PATH)


def find_new(bids: List[BidItem]) -> List[BidItem]:
    if not bids:
        return []

    with _connect() as conn:
        existing = {
            row["bid_no"]
            for row in conn.execute("SELECT bid_no FROM seen_bids")
        }

    new_bids = [b for b in bids if b.bid_no not in existing]
    logger.info("전체 %d건 중 신규 %d건", len(bids), len(new_bids))
    return new_bids


def save(bids: List[BidItem]):
    if not bids:
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _connect() as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO seen_bids
                (bid_no, title, category, field, bid_method,
                 start_date, end_date, status, detail_url, first_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (b.bid_no, b.title, b.category, b.field, b.bid_method,
                 b.start_date, b.end_date, b.status, b.detail_url, now)
                for b in bids
            ],
        )
    logger.info("%d건 저장 완료", len(bids))
