import os
import time
import logging
from datetime import datetime

import requests
import schedule
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ENDPOINTS = [
    {"name": "JSON Placeholder API", "url": "https://jsonplaceholder.typicode.com/posts/1"},
    {"name": "GitHub API", "url": "https://api.github.com"},
]

# configuration from environment, ID storage and Checking 
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "5")) 
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))


def make_session(retries: int = 2, backoff_factor: float = 0.5) -> requests.Session:
    session = requests.Session()
    try:
        from urllib3.util.retry import Retry
        from requests.adapters import HTTPAdapter

        retry = Retry(total=retries, backoff_factor=backoff_factor, status_forcelist=(500, 502, 503, 504))
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
    except Exception:
        # urllib3 not available? continue with plain session
        pass
    return session


SESSION = make_session()


def check_endpoint(endpoint: dict):
    """Check a single endpoint and return (is_healthy, status_code, response_time)
    """
    try:
        start = time.time()
        res = SESSION.get(endpoint["url"], timeout=REQUEST_TIMEOUT)
        response_time = round(time.time() - start, 2)
        return res.status_code == 200, res.status_code, response_time
    except requests.exceptions.RequestException as exc:
        logger.debug("Request error for %s: %s", endpoint.get("url"), exc)
        return False, None, None


def send_telegram_alert(message: str):
    """Send alert via Telegram bot"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        SESSION.post(url, json=payload, timeout=5)
    except Exception as exc:
        logger.warning("Failed to send telegram alert: %s", exc)


def send_slack_alert(message: str):
    """Send alert via Slack webhook"""
    if not SLACK_WEBHOOK_URL:
        return
    payload = {"text": message}
    try:
        SESSION.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as exc:
        logger.warning("Failed to send Slack alert: %s", exc)


def monitor_job():
    """Main monitoring job that runs on schedule"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("Running health checks...")

    for endpoint in ENDPOINTS:
        is_healthy, status_code, response_time = check_endpoint(endpoint)
        if is_healthy:
            logger.info("✓ %s: OK (%s) - %ss", endpoint["name"], status_code, response_time)
        else:
            logger.error("✗ %s: FAILED (%s)", endpoint.get("name"), status_code)
            alert_msg = (
                f"🚨 <b>{endpoint.get('name')}</b> is DOWN!\n"
                f"Status: {status_code}\n"
                f"Time: {timestamp}\n"
            )
            slack_msg = f"🚨 {endpoint.get('name')} is DOWN! Status: {status_code} ({timestamp})"
            send_telegram_alert(alert_msg)
            send_slack_alert(slack_msg)


def schedule_monitor():
    """Schedule the monitoring job"""
    schedule.every(CHECK_INTERVAL).minutes.do(monitor_job)
    logger.info("Uptime Monitor Started")
    logger.info("Checking every %s minute(s)", CHECK_INTERVAL)
    logger.info("Endpoints: %s", len(ENDPOINTS))

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    try:
        schedule_monitor()
    except KeyboardInterrupt:
        logger.info("Monitor Stopped.")

