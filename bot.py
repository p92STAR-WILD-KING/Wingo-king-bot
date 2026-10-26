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

WIN_STICKER = "CAACAgIAAxkBAAEZ78pl3gAB1QAB..."   
LOSS_STICKER = "CAACAgIAAxkBAAEZ8E9l3gAB2QAB..."  

bot = telebot.TeleBot(BOT_TOKEN)

active_prediction_users = set()
user_channels = {}
last_processed_period = ""
active_prediction = None

SESSION_TITLE = "3:00 PM Session"
TARGET_WINS_LIMIT = 10
current_session_wins = 0

# --- Flask Server ---
app = Flask(__name__)

@app.route("/")
@app.route("/health")
def home():
    return "WILD KING TEXT BOT IS LIVE", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    first_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "N/A"

    welcome_text = (
        f"👑 **WILD KING BOT** 👑\n\n"
        f"Welcome, {first_name} 🔥!\n\n"
        f"👤 **USER ID:** `{user_id}`\n"
        f"👤 **USERNAME:** {username}\n\n"
        f"✅ **Session Active:** {SESSION_TITLE}\n"
        f"🚀 **Clean 30s Text Signal Engine Ready!**"
    )
    bot.send_message(user_id, welcome_text, parse_mode="Markdown")

# --- Live API & Safe VIP Prediction Engine ---
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

def safe_vip_prediction(history_list):
    if not history_list or len(history_list) < 5:
        return "BIG"
    
    latest = history_list[0]
    last_num = int(latest.get("number", 0))
    last_size = latest.get("size", "").upper() or ("BIG" if last_num >= 5 else "SMALL")

    if last_size == "BIG":
        return "SMALL"
    else:
        return "BIG"

def broadcast_signal(period, signal_display):
    signal_msg = (
        f"🎁 **30 Sec Wingo** 🎁\n\n"
        f"Maintain 7 - 8 Level ✅\n\n"
        f"⏰ **{SESSION_TITLE}**\n"
        f"------------------------------------\n\n"
        f"📌 **Period:** `{period}`\n"
        f"🏹 **Signal:** **{signal_display}**\n\n"
        f"🔗 [Click to Register & Play]({REGISTER_LINK})"
    )

    targets = ["@pak92_qayoom"] + list(active_prediction_users) + list(set(user_channels.values()))
    for target in list(set(targets)):
        try:
            bot.send_message(target, signal_msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Broadcast Error: {e}")

def check_result(history_list):
    global active_prediction, current_session_wins
    if not active_prediction or not history_list:
        return

    latest = history_list[0]
    latest_period = str(latest.get("issueNumber"))

    if latest_period[-4:] == active_prediction["period"][-4:] or latest_period == active_prediction["period"]:
        num = int(latest.get("number", 0))
        actual_size = latest.get("size", "").upper() or ("BIG" if num >= 5 else "SMALL")
        predicted_side = active_prediction["prediction"]

        is_win = (actual_size == predicted_side)
        res_text = f"{latest_period[-4:]} {predicted_side} " + ("✅✅✅ WIN" if is_win else "❌ LOST")

        targets = ["@pak92_qayoom"] + list(active_prediction_users) + list(set(user_channels.values()))
        
        for target in list(set(targets)):
            try:
                bot.send_message(target, res_text)
                if is_win and WIN_STICKER:
                    bot.send_sticker(target, WIN_STICKER)
                elif not is_win and LOSS_STICKER:
                    bot.send_sticker(target, LOSS_STICKER)
            except:
                pass

        if is_win:
            current_session_wins += 1

        active_prediction = None

def bot_loop():
    global last_processed_period, active_prediction
    print("👑 Wild King Text Bot Engine Started...")
    time.sleep(3)

    while True:
        try:
            history = get_live_data()
            if history:
                check_result(history)
                latest = history[0]
                curr_issue = int(latest.get("issueNumber"))
                next_period_full = str(curr_issue + 1)
                next_period_short = next_period_full[-4:]

                if next_period_full != last_processed_period:
                    last_processed_period = next_period_full
                    signal_display = safe_vip_prediction(history)

                    active_prediction = {
                        "period": next_period_full,
                        "prediction": signal_display
                    }

                    broadcast_signal(next_period_short, signal_display)
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
        
