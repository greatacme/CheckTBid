import logging
import sys
import traceback
from datetime import date
from pathlib import Path

# 로그 설정 (일자별 파일)
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(f"logs/app_{date.today()}.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

from crawler.session import BidSession
from crawler.bid_scraper import scrape_all_pages
from storage import bid_store
from notifier import email_sender


def run():
    logger.info("=" * 50)
    logger.info("CheckTBid 시작")

    bid_store.init_db()

    with BidSession() as session:
        if not session.login():
            msg = "로그인 실패. 아이디/비밀번호를 확인하세요."
            logger.error(msg)
            email_sender.send_error(msg)
            sys.exit(1)

        bids = scrape_all_pages(session)

    if not bids:
        logger.warning("공고 목록을 가져오지 못했습니다.")
        return

    new_bids = bid_store.find_new(bids)

    if new_bids:
        logger.info("신규 공고 %d건 발견 → 이메일 발송", len(new_bids))
        bid_store.save(new_bids)
        email_sender.send_new_bids(new_bids)
    else:
        logger.info("신규 공고 없음")

    logger.info("CheckTBid 완료")
    logger.info("=" * 50)


if __name__ == "__main__":
    try:
        run()
    except Exception:
        err = traceback.format_exc()
        logger.error("예기치 않은 오류:\n%s", err)
        try:
            email_sender.send_error(err)
        except Exception:
            pass
        sys.exit(1)
