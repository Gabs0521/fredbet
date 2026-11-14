import os
import requests
import psycopg2
import http.server
import socketserver
import threading
import time
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "9099278569:AAEXXy_-aTojgls8UquwGBcy5n80eCsIgTA")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8286139008")
DATABASE_URL = os.environ.get("DATABASE_URL")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "92ebb20e57a944758f79328d32fe7283")

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

def check_and_save_prediction(match_name, prediction_text):
    """Saves match prediction to Neon DB and sends alert only if it's new."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM goal_predictions WHERE match_name = %s", (match_name,))
        exists = cur.fetchone()
        
        if not exists:
            cur.execute(
                "INSERT INTO goal_predictions (match_name, prediction) VALUES (%s, %s)",
                (match_name, prediction_text)
            )
            conn.commit()
            
            alert_message = (
                f"🎯 **New Over 1.5 Goals Pick!**\n\n"
                f"⚽ **Match:** {match_name}\n"
                f"📊 **Tip:** {prediction_text}\n"
                f"🔥 *Source: Multi-League Scan*"
            )
            send_telegram_alert(alert_message)
            print(f"New prediction saved and alerted: {match_name}")
        else:
            print(f"Match already processed: {match_name}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database / Prediction error: {e}")

def fetch_live_fixtures():
    """Fetches upcoming matches across multiple major European leagues"""
    # PL = Premier League, PD = La Liga, SA = Serie A, BL1 = Bundesliga, CL = Champions League
    competitions = ["PL", "PD", "SA", "BL1", "CL"]
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    for comp in competitions:
        url = f"https://api.football-data.org/v4/competitions/{comp}/matches?status=SCHEDULED"
        try:
            print(f"Scanning competition: {comp}...")
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                matches = data.get("matches", [])
                print(f"Found {len(matches)} matches for {comp}")
                
                for match in matches[:3]: # Check top 3 upcoming matches per league per scan
                    home = match['homeTeam']['name']
                    away = match['awayTeam']['name']
                    match_name = f"{home} vs {away}"
                    
                    prediction_text = f"Over 1.5 Goals ({comp} Multi-League Filter)"
                    check_and_save_prediction(match_name, prediction_text)
            else:
                print(f"API Error for {comp}: {response.status_code}")
        except Exception as e:
            print(f"Error fetching {comp}: {e}")

def background_scheduler():
    """Continuously runs the multi-league fixture scan every 4 hours automatically"""
    while True:
        fetch_live_fixtures()
        # Sleep for 4 hours (4 * 60 * 60 seconds)
        time.sleep(14400)

def run_web_server():
    PORT = int(os.environ.get("PORT", 10000))
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving web port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    init_db()
    send_telegram_alert("🤖 **Over 1.5 Goals Bot is Live with Multi-League Scanning!**")
    
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    
    scheduler_thread = threading.Thread(target=background_scheduler, daemon=True)
    scheduler_thread.start()
    
    server_thread.join()
