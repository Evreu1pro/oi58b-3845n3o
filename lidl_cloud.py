import os
import requests
import time
import random
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Берем данные из секретов GitHub (чтобы не светить пароли в коде)
LIDL_PHONE = os.environ.get("LIDL_PHONE")
LIDL_PASSWORD = os.environ.get("LIDL_PASSWORD")

TOKEN_URL = "https://api.lidl-connect.de/api/token"
GRAPHQL_URL = "https://api.lidl-connect.de/api/graphql"
TARIFF_OPTION_ID = "CCS_92061"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
]

def get_token():
    payload = {
        "grant_type": "password",
        "client_id": "lidl",
        "client_secret": "lidl",
        "username": LIDL_PHONE,
        "password": LIDL_PASSWORD
    }
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    
    response = requests.post(TOKEN_URL, json=payload, headers=headers)
    if response.status_code == 200:
        logging.info("Токен успешно получен.")
        return f"Bearer {response.json()['access_token']}"
    else:
        logging.error(f"Ошибка авторизации: {response.text}")
        return None

def book_gigabyte(token):
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
    
    response = requests.post(GRAPHQL_URL, json=mutation, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data.get("data", {}).get("bookTariffoptionsDirect", {}).get("success"):
            logging.info("УСПЕХ: +1 GB начислен.")
            return True
        else:
            logging.warning(f"Отказ биллинга: {data}")
            return False
    else:
        logging.error(f"Ошибка GraphQL: {response.status_code}")
        return False

if __name__ == "__main__":
    if not LIDL_PHONE or not LIDL_PASSWORD:
        logging.critical("Не заданы переменные окружения LIDL_PHONE или LIDL_PASSWORD!")
        exit(1)
        
    # Добавляем рандомную задержку, чтобы эмулировать человека и не триггерить WAF
    time.sleep(random.uniform(1, 10))
    
    token = get_token()
    if token:
        book_gigabyte(token)
