import logging
from playwright.sync_api import sync_playwright, Page, Browser

import config

logger = logging.getLogger(__name__)

LOGIN_URL = f"{config.TBID_URL}/index.tms"
BID_LIST_URL = f"{config.TBID_URL}/bidding/bidding_list.tms"


class BidSession:
    def __init__(self):
        self._playwright = None
        self._browser: Browser = None
        self.page: Page = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.close()

    def start(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self.page = self._browser.new_page()

    def close(self):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def _fill_and_click_login(self) -> dict:
        """로그인 폼 입력 후 버튼 클릭, 응답 JSON 반환"""
        result = {}

        def capture(response):
            if "login_proc.json" in response.url:
                try:
                    result["data"] = response.json()
                except Exception:
                    pass

        self.page.on("response", capture)
        self.page.fill("input[name='member_id']", config.TBID_USER_ID)
        self.page.fill("input[name='member_pwd']", config.TBID_PASSWORD)
        self.page.click("input[type='image']")
        self.page.wait_for_timeout(2000)
        self.page.remove_listener("response", capture)

        return result.get("data", {}).get("login_proc", {})

    def login(self) -> bool:
        logger.info("로그인 시도: %s", LOGIN_URL)
        self.page.goto(LOGIN_URL, wait_until="networkidle")

        proc = self._fill_and_click_login()
        logger.info("로그인 응답: %s", proc)

        # 다른 기기 세션이 존재하면 강제 로그아웃 후 페이지 새로고침 후 재시도
        if proc.get("already_yn", 0) > 0:
            logger.warning("다른 기기에서 로그인 중 → 강제 로그아웃 후 재시도")
            force_resp = self.page.request.post(
                f"{config.TBID_URL}/member/already_logout.json",
                form={"member_id": config.TBID_USER_ID},
            )
            force_result = force_resp.json()
            logger.info("강제 로그아웃 응답: %s", force_result)
            if force_result.get("already_logout", {}).get("out", 0) <= 0:
                logger.error("강제 로그아웃 실패")
                return False

            # 페이지 새로고침 후 재로그인
            self.page.goto(LOGIN_URL, wait_until="networkidle")
            proc = self._fill_and_click_login()
            logger.info("재로그인 응답: %s", proc)

        if proc.get("error", 0) > 0:
            logger.error("로그인 실패: 아이디/비밀번호를 확인하세요.")
            return False

        # 로그인 성공 → 입찰 목록 페이지로 이동
        self.page.goto(BID_LIST_URL, wait_until="networkidle")
        logger.info("로그인 성공 → 입찰 목록 이동")
        return True

    def get_bid_list_html(self, page_no: int = 1) -> str:
        self.page.evaluate(f"exeuteAction.goPage('{page_no}', '1')")
        self.page.wait_for_load_state("networkidle")
        return self.page.content()
