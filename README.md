# CheckTBid

T-Money 입찰공고 사이트를 주기적으로 크롤링하여 신규 입찰공고 등록 여부를 확인하고, 신규 건 발생 시 이메일로 통보하는 자동화 프로그램.

---

## 기능

1. **로그인** — Playwright(Chromium headless)로 T-Money 구매시스템 자동 로그인
   - 중복 세션(다른 기기 로그인 중) 감지 시 강제 로그아웃 후 재시도
2. **크롤링** — 입찰공고 목록 페이지 파싱 (BeautifulSoup)
3. **신규 판별** — SQLite DB에 저장된 공고 ID와 비교하여 신규 건만 추출
4. **이메일 알림** — 신규 공고를 HTML 이메일로 발송 (로컬 SMTP 서버 사용)
5. **오류 알림** — 로그인 실패 등 예외 발생 시 오류 내용 이메일 발송

---

## 대상 사이트

| 항목 | 값 |
|------|-----|
| 로그인 페이지 | https://bid.tmoney.co.kr/index.tms |
| 입찰공고 목록 | https://bid.tmoney.co.kr/bidding/bidding_list.tms |
| 알림 수신자 | jhypark@lgcns.com |
| SMTP | 로컬 메일 서버 (localhost:25) |

---

## 프로젝트 구조

```
CheckTBid/
├── main.py                  # 진입점
├── config.py                # 환경변수 로드
├── requirements.txt         # 의존성
├── .env                     # 계정/설정 (git 제외)
├── .gitignore
├── crawler/
│   ├── session.py           # Playwright 로그인 및 페이지 이동
│   └── bid_scraper.py       # 입찰공고 목록 파싱 (BidItem 반환)
├── storage/
│   └── bid_store.py         # SQLite 신규 공고 판별 및 저장
├── notifier/
│   └── email_sender.py      # HTML 이메일 발송
├── logs/                    # 실행 로그 (git 제외)
└── data/
    └── bids.db              # SQLite DB (git 제외)
```

---

## 설치 및 실행

### 사전 요구사항

- Python 3.10+
- WSL2 (Ubuntu)

### 설치

```bash
pip install -r requirements.txt
playwright install chromium
```

### 환경변수 설정 (.env)

```env
TBID_USER_ID=아이디
TBID_PASSWORD=비밀번호
TBID_URL=https://bid.tmoney.co.kr
SMTP_HOST=localhost
SMTP_PORT=25
NOTIFY_EMAIL=jhypark@lgcns.com
SENDER_EMAIL=checkbid@localhost
```

### 실행

```bash
cd /home/acme/dev/CheckTBid
python3 main.py
```

---

## 실행 스케줄 등록 (Windows Task Scheduler)

Windows PowerShell(관리자)에서 실행:

```powershell
$action = New-ScheduledTaskAction `
    -Execute "wsl.exe" `
    -Argument "-d Ubuntu -- bash -c 'cd /home/acme/dev/CheckTBid && /usr/bin/python3 main.py >> /home/acme/dev/CheckTBid/logs/scheduler.log 2>&1'"

$trigger = New-ScheduledTaskTrigger -Daily -At "08:30"

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -RunOnlyIfNetworkAvailable `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "CheckTBid" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "T-Money 입찰공고 신규 등록 모니터링" `
    -RunLevel Highest
```

---

## 의존성

| 라이브러리 | 용도 |
|------------|------|
| playwright | Chromium headless 브라우저 (로그인) |
| beautifulsoup4 | HTML 파싱 |
| lxml | BS4 파서 |
| python-dotenv | .env 환경변수 로드 |
