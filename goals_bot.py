import os
import requests
import psycopg2

TELEGRAM_BOT_TOKEN = "9099278569:AAEXXy_-aTojgls8UquwGBcy5n80eCsIgTA"
TELEGRAM_CHAT_ID = "8286139008"
DATABASE_URL = "postgresql://neondb_owner:npg_Ean30NweykBR@ep-purple-mountain-bdtw4wms.c-8.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Telegram error: {e}")

def init_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS goal_predictions (
                id SERIAL PRIMARY KEY,
                match_name TEXT UNIQUE,
                prediction TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Database connected & goal_predictions table ready!")
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    init_db()
    send_telegram_alert("⚽ **Over 1.5 Goals Bot is Live and Connected!**")
    print("Test alert sent to Telegram!")
