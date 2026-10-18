import os
import threading
import time
import requests
import telebot
from telebot import types
from flask import Flask

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = "8883836126:AAFFIuH5PI719_k_VkYbYy_mHaJWP2O12VA"
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

# --- Flask Server ---
app = Flask(__name__)

@app.route("/")
@app.route("/health")
def home():
    return "WINGO CYBER 24/7 PRO BOT IS LIVE", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# --- Keyboards ---
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_start = types.KeyboardButton("▶️ Start Prediction")
    btn_stop = types.KeyboardButton("⏹️ Stop Prediction")
    btn_add_ch = types.KeyboardButton("➕ Add Channel")
    btn_my_ch = types.KeyboardButton("📺 My Channels")
    markup.add(btn_start, btn_stop)
    markup.add(btn_add_ch, btn_my_ch)
    return markup

# --- Command /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "N/A"

    welcome_text = (
        f"🕊️ **CYBER 24/7** 🕊️\n\n"
        f"Welcome, {first_name} 🔥!\n\n"
        f"👤 **USER ID:** `{user_id}`\n"
        f"👤 **USERNAME:** {username}\n"
        f"👑 **YOUR STATUS:** Free User\n\n"
        f"✅ **Access Granted**\n\n"
        f"🚀 Press **▶️ Start Prediction** to get live signals instantly!"
    )

    try:
        bot.send_photo(user_id, BANNER_CARD_URL, caption=welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    except Exception:
        bot.send_message(user_id, welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# --- Menu Handlers ---
@bot.message_handler(func=lambda msg: True)
def handle_reply_buttons(message):
    chat_id = message.chat.id
    text = message.text

    if text == "▶️ Start Prediction":
        active_prediction_users.add(chat_id)
        bot.send_message(chat_id, "🚀 **Prediction Mode Activated!** Signals aana shuru ho jayenge.", reply_markup=get_main_keyboard())

    elif text == "⏹️ Stop Prediction":
        active_prediction_users.discard(chat_id)
        bot.send_message(chat_id, "⏹️ **Prediction Mode Stopped!**", reply_markup=get_main_keyboard())

    elif text == "➕ Add Channel":
        msg = bot.send_message(chat_id, "📌 Apna channel username send karein (e.g. `@pak92_qayoom`):")
        bot.register_next_step_handler(msg, process_add_channel)

    elif text == "📺 My Channels":
        ch = user_channels.get(chat_id, "Koi channel add nahi hua.")
        bot.send_message(chat_id, f"📺 **Your Target Channel:** {ch}")

def process_add_channel(message):
    chat_id = message.chat.id
    ch_name = message.text.strip()
    if ch_name.startswith("@"):
        user_channels[chat_id] = ch_name
        bot.send_message(chat_id, f"✅ Channel `{ch_name}` successfully connected!")
    else:
        bot.send_message(chat_id, "⚠️ Invalid Channel Username!")

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

    targets = list(active_prediction_users) + list(set(user_channels.values()))
    for target in targets:
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
        targets = list(active_prediction_users) + list(set(user_channels.values()))

        if actual_size == predicted:
            total_wins += 1
            win_rate = round((total_wins / total_signals) * 100, 1) if total_signals > 0 else 0
            res_msg = f"✅ **WIN!**\n===========================\nPeriod => #{latest_period[-4:]}\nResult => NUM:{num} 🔵 {actual_size}"
            for target in targets:
                try:
                    bot.send_message(target, res_msg, parse_mode="Markdown")
                    if WIN_STICKER: bot.send_sticker(target, WIN_STICKER)
                except Exception: pass
        else:
            total_losses += 1
            win_rate = round((total_wins / total_signals) * 100, 1) if total_signals > 0 else 0
            res_msg = f"❌ **LOSS**\n===========================\nPeriod => #{latest_period[-4:]}\nResult => NUM:{num} 🔴 {actual_size}"
            for target in targets:
                try:
                    bot.send_message(target, res_msg, parse_mode="Markdown")
                    if LOSS_STICKER: bot.send_sticker(target, LOSS_STICKER)
                except Exception: pass

        active_prediction = None

def bot_loop():
    global last_processed_period, active_prediction

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
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    t_bot = threading.Thread(target=bot_loop)
    t_bot.daemon = True
    t_bot.start()

    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            print(f"Polling Error: {e}")
            time.sleep(5)
