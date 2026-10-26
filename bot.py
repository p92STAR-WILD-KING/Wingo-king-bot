import os
import threading
import time
from datetime import datetime
import requests
import telebot
from flask import Flask

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = "8884038113:AAEX8v7pFHqfS7n3M6ztXmu7iTgOWu2B8Ko"
REGISTER_LINK = "https://www.92pkr4.com/#/register?invitationCode=446251637459"
API_URL = "https://sky-predictor-1012593186417.asia-southeast1.run.app/api/wingo-history-30s-100"

bot = telebot.TeleBot(BOT_TOKEN)

last_processed_period = ""
active_prediction = None

SESSION_TITLE = "3:00 PM Session"
session_history_log = []

# --- Flask Server ---
app = Flask(__name__)

@app.route("/")
@app.route("/health")
def home():
    return "WILD KING CLEAN BOT IS LIVE", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    first_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "N/A"

    welcome_text = (
        f"👑 **WILD KING VIP BOT** 👑\n\n"
        f"Welcome, {first_name} 🔥!\n\n"
        f"👤 **USER ID:** `{user_id}`\n"
        f"👤 **USERNAME:** {username}\n\n"
        f"✅ **Session Active:** {SESSION_TITLE}\n"
        f"🚀 **Clean Signal Ledger Running!**"
    )
    bot.send_message(user_id, welcome_text, parse_mode="Markdown")

# --- Live API & VIP Smart Engine ---
def get_live_data():
    try:
        res = requests.get(API_URL, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get("code") == 0 and "data" in data and "list" in data["data"]:
                return data["data"]["list"]
    except Exception as e:
        print(f"API Error: {e}")
    return None

def vip_smart_prediction(history_list):
    if not history_list or len(history_list) < 5:
        return "BIG"
    
    recent_results = [item.get("size", "").upper() for item in history_list[:3]]
    if recent_results.count("BIG") >= 2:
        return "SMALL"
    elif recent_results.count("SMALL") >= 2:
        return "BIG"
    
    latest = history_list[0]
    last_num = int(latest.get("number", 0))
    last_size = latest.get("size", "").upper() or ("BIG" if last_num >= 5 else "SMALL")

    return "SMALL" if last_size == "BIG" else "BIG"

def build_session_message():
    log_lines = "\n".join(session_history_log[-12:]) if session_history_log else "Waiting for rounds..."
    
    msg = (
        f"Maintain 7 - 8 Level ✅\n\n"
        f"👑 **WILD KING** 👑\n\n"
        f"⏰ **{SESSION_TITLE}**\n"
        f"------------------------------------\n"
        f"{log_lines}\n"
        f"------------------------------------\n"
        f"{REGISTER_LINK}"
    )
    return msg

def broadcast_or_update_ledger():
    text_content = build_session_message()
    targets = ["@pak92_qayoom"]
    
    for target in list(set(targets)):
        try:
            bot.send_message(target, text_content, parse_mode="Markdown")
        except Exception as e:
            print(f"Broadcast Error to {target}: {e}")

def check_and_update_results(history_list):
    global active_prediction, session_history_log
    if not history_list or not active_prediction:
        return

    latest = history_list[0]
    latest_period = str(latest.get("issueNumber"))
    short_period = latest_period[-4:]

    if latest_period[-4:] == active_prediction["period"][-4:] or latest_period == active_prediction["period"]:
        num = int(latest.get("number", 0))
        actual_size = latest.get("size", "").upper() or ("BIG" if num >= 5 else "SMALL")
        predicted_side = active_prediction["prediction"]

        is_win = (actual_size == predicted_side)
        
        # Replace the pending/open signal line with final win/loss result line
        if session_history_log:
            session_history_log.pop()

        if is_win:
            res_line = f"`{short_period}` **{predicted_side}** ✅✅✅ WIN"
        else:
            res_line = f"`{short_period}` **{predicted_side}** ❌ LOST"

        session_history_log.append(res_line)
        active_prediction = None
        broadcast_or_update_ledger()

def bot_loop():
    global last_processed_period, active_prediction, session_history_log
    print("👑 Wild King Clean Bot Engine Started...")
    time.sleep(3)

    while True:
        try:
            history = get_live_data()
            if history:
                check_and_update_results(history)
                
                latest = history[0]
                curr_issue = int(latest.get("issueNumber"))
                next_period_full = str(curr_issue + 1)
                next_period_short = next_period_full[-4:]

                if next_period_full != last_processed_period:
                    last_processed_period = next_period_full
                    signal_display = vip_smart_prediction(history)

                    active_prediction = {
                        "period": next_period_full,
                        "prediction": signal_display
                    }
                    
                    # Add new incoming signal
                    session_history_log.append(f"`{next_period_short}` **{signal_display}**")
                    if len(session_history_log) > 15:
                        session_history_log.pop(0)

                    broadcast_or_update_ledger()
        except Exception as e:
            print(f"Main Loop Error: {e}")
        time.sleep(2)

if __name__ == "__main__":
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=True", timeout=10)
    except:
        pass

    t_loop = threading.Thread(target=bot_loop)
    t_loop.daemon = True
    t_loop.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    
