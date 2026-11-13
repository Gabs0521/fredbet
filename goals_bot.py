import os
import requests
import psycopg2
import http.server
import socketserver
import threading
import time

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

def check_and_save_prediction(match_name, prediction_text):
    """Saves match prediction to Neon DB and sends alert only if it's new."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check if match already exists in database
        cur.execute("SELECT id FROM goal_predictions WHERE match_name = %s", (match_name,))
        exists = cur.fetchone()
        
        if not exists:
            # Insert new prediction
            cur.execute(
                "INSERT INTO goal_predictions (match_name, prediction) VALUES (%s, %s)",
                (match_name, prediction_text)
            )
            conn.commit()
            
            # Send Telegram Alert
            alert_message = (
                f"🎯 **New Over 1.5 Goals Prediction!**\n\n"
                f"⚽ **Match:** {match_name}\n"
                f"📊 **Tip:** {prediction_text}\n"
                f"🔥 *Confidence: High*"
            )
            send_telegram_alert(alert_message)
            print(f"New prediction saved and alerted: {match_name}")
        else:
            print(f"Match already processed: {match_name}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database / Prediction error: {e}")

# Dummy web server to keep Render's Web Service active
def run_web_server():
    PORT = int(os.environ.get("PORT", 10000))
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving web port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    init_db()
    send_telegram_alert("⚽ **Over 1.5 Goals Bot is Live and Ready for Predictions!**")
    
    # Start web server in background thread
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    
    # Example test prediction loop/logic check
    # (Here is where you can plug in your match scanner or API loop later)
    check_and_save_prediction("Arsenal vs Chelsea", "Over 1.5 Goals (Stats: 85% Over 1.5 trend)")
    
    # Keep main thread alive
    server_thread.join()
