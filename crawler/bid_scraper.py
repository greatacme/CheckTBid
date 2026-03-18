import logging
import re
from dataclasses import dataclass
from typing import List

from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)


@dataclass
class BidItem:
    bid_no: str        # 공고 NO (고유 식별자)
    title: str         # 공고건명
    category: str      # 구분
    field: str         # 분야
    bid_method: str    # 입찰방식
    start_date: str    # 입찰시작
    end_date: str      # 입찰마감
    status: str        # 상태
    detail_url: str    # 상세 URL


def parse_bid_list(html: str) -> List[BidItem]:
    soup = BeautifulSoup(html, "lxml")
    items: List[BidItem] = []

    # 테이블 본문 행 탐색
    rows = soup.select("table tbody tr")
    if not rows:
        # 일부 사이트는 thead/tbody 없이 tr만 사용
        rows = soup.select("table tr")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 8:
            continue

        bid_no = cols[0].get_text(strip=True)
        if not bid_no.isdigit():
            continue  # 헤더 행 등 스킵

        # 상세 링크 추출
        link_tag = cols[1].find("a")
        detail_url = ""
        if link_tag and link_tag.get("href"):
            href = link_tag["href"]
            detail_url = href if href.startswith("http") else config.TBID_URL + href
        elif link_tag and link_tag.get("onclick"):
            # onclick="location.href='/bidding/detail.tms?id=xxx'" 패턴
            match = re.search(r"location\.href=['\"]([^'\"]+)['\"]", link_tag["onclick"])
            if match:
                path = match.group(1)
                detail_url = path if path.startswith("http") else config.TBID_URL + path

        item = BidItem(
            bid_no=bid_no,
            title=cols[1].get_text(strip=True),
            category=cols[2].get_text(strip=True),
            field=cols[3].get_text(strip=True),
            bid_method=cols[4].get_text(strip=True),
            start_date=cols[5].get_text(strip=True),
            end_date=cols[6].get_text(strip=True),
            status=cols[7].get_text(strip=True),
            detail_url=detail_url,
        )
        items.append(item)

    logger.info("파싱된 공고 수: %d", len(items))
    return items


def scrape_all_pages(session) -> List[BidItem]:
    """첫 페이지만 크롤링 (필요 시 다중 페이지로 확장 가능)"""
    html = session.get_bid_list_html(page_no=1)
    return parse_bid_list(html)
