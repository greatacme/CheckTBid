import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from datetime import datetime

import config
from crawler.bid_scraper import BidItem

logger = logging.getLogger(__name__)


def _build_html(bids: List[BidItem]) -> str:
    rows = ""
    for b in bids:
        title_cell = (
            f'<a href="{b.detail_url}">{b.title}</a>'
            if b.detail_url
            else b.title
        )
        rows += f"""
        <tr>
            <td style="padding:6px 10px;border:1px solid #ddd;text-align:center;">{b.bid_no}</td>
            <td style="padding:6px 10px;border:1px solid #ddd;">{title_cell}</td>
            <td style="padding:6px 10px;border:1px solid #ddd;text-align:center;">{b.category}</td>
            <td style="padding:6px 10px;border:1px solid #ddd;text-align:center;">{b.field}</td>
            <td style="padding:6px 10px;border:1px solid #ddd;text-align:center;">{b.start_date}</td>
            <td style="padding:6px 10px;border:1px solid #ddd;text-align:center;">{b.end_date}</td>
            <td style="padding:6px 10px;border:1px solid #ddd;text-align:center;">{b.status}</td>
        </tr>"""

    return f"""
    <html><body>
    <p>T-Money 입찰공고 시스템에서 <strong>신규 입찰공고 {len(bids)}건</strong>이 등록되었습니다.</p>
    <p>확인 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    <table style="border-collapse:collapse;font-size:13px;width:100%;">
        <thead>
            <tr style="background:#f2f2f2;">
                <th style="padding:6px 10px;border:1px solid #ddd;">NO</th>
                <th style="padding:6px 10px;border:1px solid #ddd;">공고건명</th>
                <th style="padding:6px 10px;border:1px solid #ddd;">구분</th>
                <th style="padding:6px 10px;border:1px solid #ddd;">분야</th>
                <th style="padding:6px 10px;border:1px solid #ddd;">입찰시작</th>
                <th style="padding:6px 10px;border:1px solid #ddd;">입찰마감</th>
                <th style="padding:6px 10px;border:1px solid #ddd;">상태</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    <br>
    <p><a href="{config.TBID_URL}/bidding/bidding_list.tms">▶ 입찰공고 목록 바로가기</a></p>
    </body></html>
    """


def send_new_bids(bids: List[BidItem]):
    subject = f"[T-Money 입찰공고] 신규 {len(bids)}건 등록 ({datetime.now().strftime('%Y-%m-%d')})"
    html_body = _build_html(bids)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.SENDER_EMAIL
    msg["To"] = ", ".join(config.NOTIFY_EMAILS)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as smtp:
            smtp.sendmail(config.SENDER_EMAIL, config.NOTIFY_EMAILS, msg.as_string())
        logger.info("이메일 발송 완료 → %s", config.NOTIFY_EMAILS)
    except Exception as e:
        logger.error("이메일 발송 실패: %s", e)
        raise


def send_error(error_msg: str):
    """크롤링/로그인 오류 발생 시 관리자에게 알림"""
    msg = MIMEText(f"CheckTBid 오류 발생:\n\n{error_msg}", "plain", "utf-8")
    msg["Subject"] = f"[CheckTBid] 오류 발생 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    msg["From"] = config.SENDER_EMAIL
    msg["To"] = ", ".join(config.NOTIFY_EMAILS)

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as smtp:
            smtp.sendmail(config.SENDER_EMAIL, config.NOTIFY_EMAILS, msg.as_string())
    except Exception as e:
        logger.error("오류 알림 이메일 발송 실패: %s", e)
