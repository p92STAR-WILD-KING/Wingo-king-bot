import os
import threading
import time
import requests
import telebot
from telebot import types
from flask import Flask

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = "8884038113:AAEX8v7pFHqfS7n3M6ztXmu7iTgOWu2B8Ko"
REGISTER_LINK = "https://92blaze99.com/register?inviteCode=HD6Y3BN&from=web"
API_URL = "https://sky-predictor-1012593186417.asia-southeast1.run.app/api/wingo-history-30s-100"

BANNER_CARD_URL = "https://i.ibb.co/L8mN9v3/wingo-card.jpg"

WIN_STICKER = "CAACAgIAAxkBAAEZ78pl3gAB1QAB..."   
LOSS_STICKER = "CAACAgIAAxkBAAEZ8E9l3gAB2QAB..."  

bot = telebot.TeleBot(BOT_TOKEN)

active_prediction_users = set()
user_channels = {}
last_processed_period = ""
active_prediction = None

total_signals = 0
total_wins = 0
total_losses = 0

# --- Flask Server (Keep-Alive & Health Check) ---
app = Flask(__name__)

@app.route("/")
@app.route("/health")
def home():
    return "WINGO CYBER 24/7 PRO BOT IS LIVE (NO POLLING CONFLICT)", 200

# --- Command /start handler via standard HTTP or basic listener ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    first_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "N/A"

    welcome_text = (
        f"🕊️ **CYBER 24/7** 🕊️\n\n"
        f"Welcome, {first_name} 🔥!\n\n"
        f"👤 **USER ID:** `{user_id}`\n"
        f"👤 **USERNAME:** {username}\n"
        f"👑 **YOUR STATUS:** Free User\n\n"
        f"✅ **Access Granted**\n\n"
        f"🚀 **Bot is actively broadcasting live Wingo signals!**"
    )

    try:
        bot.send_photo(user_id, BANNER_CARD_URL, caption=welcome_text, parse_mode="Markdown")
    except Exception:
        bot.send_message(user_id, welcome_text, parse_mode="Markdown")

# --- API Data & Prediction Engine ---
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

def generate_prediction(history_list):
    if not history_list:
        return "BIG", "9/6"
    latest = history_list[0]
    num = int(latest.get("number", 0))
    sz = latest.get("size", "").upper() or ("BIG" if num >= 5 else "SMALL")

    pred = "SMALL" if sz == "BIG" else "BIG"
    nums = "9/6" if pred == "BIG" else "1/3"
    return pred, nums

def broadcast_prediction(period, prediction, number_hint):
    signal_msg = (
        f"🪽 **WINGO 1 MIN** 🔊\n"
        f"🔍 **PERIOD** -> ( {period} )\n\n"
        f"🏹 **SIGNAL** -> **{prediction}GG**\n\n"
        f"⚛️ **NUMBER** -> {number_hint}\n\n"
        f"🔗 [Click to Register & Play]({REGISTER_LINK})"
    )

    # Broadcast to your target channel or chat ID if configured, or default broadcast
    # For testing, you can put your chat ID directly here or use active users/channels
    targets = ["@pak92_qayoom"] + list(active_prediction_users) + list(set(user_channels.values()))
    for target in list(set(targets)):
        try:
            bot.send_photo(target, BANNER_CARD_URL, caption=signal_msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Error sending to {target}: {e}")

def check_and_send_result(history_list):
    global active_prediction, total_signals, total_wins, total_losses
    if not active_prediction or not history_list:
        return

    latest = history_list[0]
    latest_period = str(latest.get("issueNumber"))

    if latest_period[-4:] == active_prediction["period"] or latest_period == active_prediction["period"]:
        num = int(latest.get("number", 0))
        actual_size = latest.get("size", "").upper() or ("BIG" if num >= 5 else "SMALL")
        predicted = active_prediction["prediction"]

        total_signals += 1
        targets = ["@pak92_qayoom"] + list(active_prediction_users) + list(set(user_channels.values()))

        if actual_size == predicted:
            total_wins += 1
            win_rate = round((total_wins / total_signals) * 100, 1) if total_signals > 0 else 0
            res_msg = f"✅ **WIN!**\n===========================\nPeriod => #{latest_period[-4:]}\nResult => NUM:{num} 🔵 {actual_size}"
            for target in list(set(targets)):
                try:
                    bot.send_message(target, res_msg, parse_mode="Markdown")
                    if WIN_STICKER: bot.send_sticker(target, WIN_STICKER)
                except Exception: pass
        else:
            total_losses += 1
            win_rate = round((total_wins / total_signals) * 100, 1) if total_signals > 0 else 0
            res_msg = f"❌ **LOSS**\n===========================\nPeriod => #{latest_period[-4:]}\nResult => NUM:{num} 🔴 {actual_size}"
            for target in list(set(targets)):
                try:
                    bot.send_message(target, res_msg, parse_mode="Markdown")
                    if LOSS_STICKER: bot.send_sticker(target, LOSS_STICKER)
                except Exception: pass

        active_prediction = None

def bot_loop():
    global last_processed_period, active_prediction
    print("🚀 Background Wingo Broadcast Engine Started...")
    time.sleep(3)
    while True:
        try:
            history = get_live_data()
            if history:
                check_and_send_result(history)
                latest = history[0]
                curr_issue = int(latest.get("issueNumber"))
                next_period_full = str(curr_issue + 1)
                next_period_short = next_period_full[-3:]

                if next_period_full != last_processed_period:
                    last_processed_period = next_period_full
                    pred, num_hint = generate_prediction(history)
                    active_prediction = {"period": next_period_full, "prediction": pred}
                    broadcast_prediction(next_period_short, pred, num_hint)
        except Exception as e:
            print(f"Loop Error: {e}")
        time.sleep(2)

if __name__ == "__main__":
    # Clear any webhooks or stuck updates completely via HTTP request
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=True", timeout=10)
    except:
        pass

    # Start Background Broadcast Loop (No Polling Conflict!)
    t_loop = threading.Thread(target=bot_loop)
    t_loop.daemon = True
    t_loop.start()

    # Start Flask Web Server for Render 24/7 Uptime
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    
