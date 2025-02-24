import requests
from dotenv import load_dotenv
import os

load_dotenv()
token = os.environ.get('MAIN_BOT_TOKEN')


def send_message(message, recivient):
    data = {
        "chat_id": recivient,
        "text": message
    }
    res = requests.post(f'https://api.telegram.org/bot{token}/sendMessage', json=data)
    return res.json()




