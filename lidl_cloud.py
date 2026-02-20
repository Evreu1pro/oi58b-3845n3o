import os
import requests
import time
import random
import logging
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

# === НАСТРОЙКИ ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

LIDL_PHONE = os.environ.get("LIDL_PHONE")
LIDL_PASSWORD = os.environ.get("LIDL_PASSWORD")

# Новые переменные для Телеги (опционально)
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

TOKEN_URL = "https://api.lidl-connect.de/api/token"
GRAPHQL_URL = "https://api.lidl-connect.de/api/graphql"
TARIFF_OPTION_ID = "CCS_92061"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]

def send_tg_alert(message_text):
    """Тихо отправляет пуш в Телеграм, если заданы токены"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": message_text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        logging.error(f"Не удалось отправить алерт в ТГ: {e}")

def is_sleep_time():
    """Спим с 3 до 6 утра по Берлину"""
    tz = ZoneInfo("Europe/Berlin")
    now = datetime.now(tz)
    if 3 <= now.hour < 6:
        logging.info(f"😴 Ночной режим (Берлин: {now.strftime('%H:%M:%S')}). Сервера отдыхают.")
        return True
    return False

def simulate_human_flow():
    """Стелс-эмуляция: выжигание -> запуск аппки -> раздумья"""
    # Ждем от 30 до 90 секунд (экономим лимиты GitHub, но ломаем паттерны WAF)
    burn_time = random.uniform(30.5, 89.2)
    logging.info(f"⏳ [Фаза 1] Смотрим YouTube... ({burn_time:.1f} сек)")
    time.sleep(burn_time)
    
    app_open_time = random.uniform(5.1, 12.4)
    logging.info(f"📱 [Фаза 2] Открываем приложение Lidl... ({app_open_time:.1f} сек)")
    time.sleep(app_open_time)

def get_token():
    payload = {
        "grant_type": "password", "client_id": "lidl", "client_secret": "lidl",
        "username": LIDL_PHONE, "password": LIDL_PASSWORD
    }
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        resp = requests.post(TOKEN_URL, json=payload, headers=headers, timeout=15)
        if resp.status_code == 200:
            logging.info("🔑 Токен получен.")
            return f"Bearer {resp.json()['access_token']}"
        else:
            err_msg = f"❌ Ошибка авторизации: {resp.status_code}. Проверь пароль!"
            logging.error(err_msg)
            send_tg_alert(err_msg)
            return None
    except Exception as e:
        logging.error(f"🔌 Отвал сети при логине: {e}")
        return None

def book_gigabyte(token):
    ui_reaction = random.uniform(2.1, 5.5)
    logging.info(f"👆 [Фаза 3] Пользователь жмет кнопку '+1 GB' ({ui_reaction:.1f} сек)")
    time.sleep(ui_reaction)

    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": random.choice(USER_AGENTS)
    }
    mutation = {
        "operationName": "bookTariffOptionsDirect",
        "variables": {"bookTariffoptionsDirectInput": {"bookTariffoptions": [{"tariffoptionId": TARIFF_OPTION_ID}]}},
        "query": "mutation bookTariffOptionsDirect($bookTariffoptionsDirectInput: BookTariffoptionsDirectInput!) { bookTariffoptionsDirect(bookTariffoptionsDirectInput: $bookTariffoptionsDirectInput) { success __typename } }"
    }
    
    try:
        resp = requests.post(GRAPHQL_URL, json=mutation, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data", {}).get("bookTariffoptionsDirect", {}).get("success"):
                msg = "✅ <b>УСПЕХ:</b> +1 GB успешно начислен машиной."
                logging.info(msg)
                send_tg_alert(msg)
            else:
                logging.warning(f"⚠️ Отказ биллинга (лимит или баг): {data}")
        else:
            err_msg = f"💥 Ошибка GraphQL: {resp.status_code}"
            logging.error(err_msg)
            send_tg_alert(err_msg)
    except Exception as e:
        logging.error(f"🔌 Отвал сети при бронировании: {e}")

if __name__ == "__main__":
    if not LIDL_PHONE or not LIDL_PASSWORD:
        logging.critical("💀 Нет учеток! Добавь LIDL_PHONE и LIDL_PASSWORD в GitHub Secrets.")
        exit(1)
        
    if is_sleep_time():
        exit(0)
        
    simulate_human_flow()
    token = get_token()
    if token:
        book_gigabyte(token)
