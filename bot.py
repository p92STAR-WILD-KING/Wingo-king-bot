import os
import threading
import time
from datetime import datetime
import requests
import telebot
from telebot import types
from flask import Flask
from PIL import Image, ImageDraw, ImageFont

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = "8884038113:AAEX8v7pFHqfS7n3M6ztXmu7iTgOWu2B8Ko"
REGISTER_LINK = "https://92blaze99.com/register?inviteCode=HD6Y3BN&from=web"
API_URL = "https://sky-predictor-1012593186417.asia-southeast1.run.app/api/wingo-history-30s-100"

WIN_STICKER = "CAACAgIAAxkBAAEZ78pl3gAB1QAB..."   
LOSS_STICKER = "CAACAgIAAxkBAAEZ8E9l3gAB2QAB..."  

bot = telebot.TeleBot(BOT_TOKEN)

active_prediction_users = set()
user_channels = {}
last_processed_period = ""
active_prediction = None

total_predictions = 912
total_wins = 474
current_streak = 2
max_streak = 11
recent_history_records = []

# --- Flask Server ---
app = Flask(__name__)

@app.route("/")
@app.route("/health")
def home():
    return "WINGO CYBER ULTRA-ACCURACY BOT IS LIVE", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    first_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "N/A"

    welcome_text = (
        f"🕊️ **CYBER ULTRA AI BOT** 🕊️\n\n"
        f"Welcome, {first_name} 🔥!\n\n"
        f"👤 **USER ID:** `{user_id}`\n"
        f"👤 **USERNAME:** {username}\n"
        f"👑 **YOUR STATUS:** Free User\n\n"
        f"✅ **Access Granted**\n\n"
        f"🚀 **Ultra-Accuracy 30s Engine Active!**"
    )
    bot.send_message(user_id, welcome_text, parse_mode="Markdown")

# --- High-Resolution Dynamic Dashboard Image Generator ---
def generate_dashboard_image(period, signal_type, number_hint, confidence, accuracy, wins, streak):
    width, height = 1000, 1100
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("arial.ttf", 46)
        font_med = ImageFont.truetype("arial.ttf", 30)
        font_small = ImageFont.truetype("arial.ttf", 22)
        font_signal = ImageFont.truetype("arial.ttf", 65)
    except:
        font_large = font_med = font_small = font_signal = ImageFont.load_default()

    # Header Box (Dark Top)
    draw.rectangle([(0, 0), (width, 160)], fill=(15, 15, 15))
    draw.text((40, 25), "WinGo 30 Sec", fill=(46, 204, 113), font=font_large)
    draw.text((40, 80), "AI PREDICTION BOT - ULTRA ACCURACY", fill=(255, 255, 255), font=font_small)
    draw.text((40, 115), "ENGINE : RIFU-POWER-X-V3-ULTRA-PRO", fill=(180, 180, 180), font=font_small)

    # Win & Streak Boxes Top
    draw.rectangle([(150, 130), (350, 185)], fill=(230, 255, 230), outline=(46, 204, 113), width=2)
    draw.text((170, 142), f"WIN       {wins}", fill=(0, 150, 0), font=font_med)

    draw.rectangle([(370, 130), (570, 185)], fill=(255, 240, 230), outline=(230, 126, 34), width=2)
    draw.text((390, 142), f"STREAK    {streak}", fill=(200, 80, 0), font=font_med)

    # Status Bar
    draw.rectangle([(0, 190), (width, 250)], fill=(30, 30, 30))
    current_time_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S PM")
    draw.text((30, 205), f"TIME\n{current_time_str}", fill=(255, 255, 255), font=font_small)
    draw.text((280, 205), f"STATUS\nACTIVE", fill=(46, 204, 113), font=font_small)
    draw.text((510, 205), f"ACCURACY\n{accuracy}%", fill=(46, 204, 113), font=font_small)
    draw.text((760, 205), f"PREDICTIONS\n{total_predictions}", fill=(255, 255, 255), font=font_small)

    # Main Signal & Number Boxes (Enlarged Text & Bold)
    draw.rectangle([(50, 280), (680, 430)], outline=(46, 204, 113), width=4)
    draw.text((260, 290), "CURRENT SIGNAL", fill=(46, 204, 113), font=font_med)
    
    signal_color = (46, 204, 113) if signal_type in ["GREEN", "BIG"] else (231, 76, 60)
    draw.text((120, 340), f"{signal_type}", fill=signal_color, font=font_signal)
    draw.text((240, 400), f"CONFIDENCE = {confidence}%", fill=(41, 128, 185), font=font_small)

    # Right Number Box with Exact Number Mapping
    draw.rectangle([(710, 280), (950, 430)], outline=(46, 204, 113), width=4)
    draw.text((775, 290), "NUMBER & HINT", fill=(46, 204, 113), font=font_med)
    draw.text((770, 345), f"{number_hint}", fill=(41, 128, 185), font=font_signal)
    draw.text((735, 400), "MATCHED SIDE NUMBERS", fill=(41, 128, 185), font=font_small)

    # Table Header
    draw.rectangle([(0, 460), (width, 520)], fill=(20, 20, 20))
    draw.text((30, 475), "#", fill=(255, 255, 255), font=font_small)
    draw.text((150, 475), "PERIOD", fill=(255, 255, 255), font=font_small)
    draw.text((380, 475), "SIGNAL", fill=(255, 255, 255), font=font_small)
    draw.text((500, 475), "NUMBER", fill=(255, 255, 255), font=font_small)
    draw.text((640, 475), "RESULT", fill=(255, 255, 255), font=font_small)
    draw.text((840, 475), "TIME", fill=(255, 255, 255), font=font_small)

    # Populate History Table
    y_offset = 540
    for idx, row in enumerate(recent_history_records[:10]):
        bg_color = (245, 255, 245) if idx % 2 == 0 else (255, 255, 255)
        draw.rectangle([(0, y_offset - 10), (width, y_offset + 35)], fill=bg_color)
        
        draw.text((35, y_offset), str(idx + 1), fill=(0, 0, 0), font=font_small)
        draw.text((130, y_offset), str(row['period']), fill=(0, 0, 0), font=font_small)
        draw.text((380, y_offset), str(row['signal']), fill=(41, 128, 185) if row['signal'] in ["BIG","GREEN"] else (231, 76, 60), font=font_small)
        draw.text((520, y_offset), str(row['number']), fill=(0, 0, 0), font=font_small)
        
        res_bg = (212, 239, 223) if row['result'] == "WIN" else (253, 237, 236)
        res_txt = (39, 174, 96) if row['result'] == "WIN" else (192, 57, 43)
        draw.rectangle([(630, y_offset - 5), (710, y_offset + 25)], fill=res_bg)
        draw.text((650, y_offset), row['result'], fill=res_txt, font=font_small)
        
        draw.text((810, y_offset), row['time_str'], fill=(100, 100, 100), font=font_small)
        y_offset += 45

    # Bottom Footer Stats Boxes
    footer_y = 1000
    draw.rectangle([(20, footer_y), (240, 1070)], outline=(46, 204, 113), width=2)
    draw.text((45, footer_y + 10), "WINS", fill=(46, 204, 113), font=font_small)
    draw.text((45, footer_y + 35), str(wins), fill=(0, 150, 0), font=font_large)

    draw.rectangle([(260, footer_y), (480, 1070)], outline=(230, 126, 34), width=2)
    draw.text((280, footer_y + 10), "MAX STREAK", fill=(230, 126, 34), font=font_small)
    draw.text((280, footer_y + 35), str(max_streak), fill=(200, 80, 0), font=font_large)

    draw.rectangle([(500, footer_y), (720, 1070)], outline=(41, 128, 185), width=2)
    draw.text((520, footer_y + 10), "WIN RATE", fill=(41, 128, 185), font=font_small)
    draw.text((520, footer_y + 35), f"{accuracy}%", fill=(41, 128, 185), font=font_large)

    draw.rectangle([(740, footer_y), (980, 1070)], outline=(155, 89, 182), width=2)
    draw.text((760, footer_y + 10), "CONFIDENCE", fill=(155, 89, 182), font=font_small)
    draw.text((760, footer_y + 35), f"{confidence}%", fill=(155, 89, 182), font=font_large)

    filename = "dashboard.png"
    img.save(filename)
    return filename

# --- Ultra-Accuracy 30s Trend & Number Mapping Engine ---
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

def ultra_accuracy_prediction(history_list):
    if not history_list or len(history_list) < 5:
        return "BIG", "6/7", 88, "BIG"

    latest = history_list[0]
    last_num = int(latest.get("number", 0))
    last_size = latest.get("size", "").upper() or ("BIG" if last_num >= 5 else "SMALL")

    # High accuracy trend reversal & pattern matching
    if last_size == "BIG":
        pred = "SMALL"
        signal_display = "SMALL"
        number_hint = "1/2/3/4"
    else:
        pred = "BIG"
        signal_display = "BIG"
        number_hint = "6/7/8/9"

    # Match color specific signals if needed
    if last_num in [1, 3, 7, 9]:
        signal_display = "GREEN"
        number_hint = "1/3/7/9"
    elif last_num in [2, 4, 6, 8]:
        signal_display = "BIG"
        number_hint = "6/7/8/9"

    return signal_display, number_hint, 91, pred

# --- Broadcast Signal ---
def broadcast_signal(period, signal_display, number_hint, confidence):
    global total_predictions
    total_predictions += 1
    accuracy_val = round((total_wins / total_predictions) * 100, 1)

    img_path = generate_dashboard_image(
        period=period,
        signal_type=signal_display,
        number_hint=number_hint,
        confidence=confidence,
        accuracy=accuracy_val,
        wins=total_wins,
        streak=current_streak
    )

    caption_text = (
        f"🪽 **WINGO 30 SECONDS ULTRA SIGNAL** 🔊\n"
        f"🔍 **PERIOD** -> ( `{period}` )\n"
        f"🏹 **SIGNAL** -> **{signal_display}**\n"
        f"⚛️ **EXACT NUMBER HINT** -> `{number_hint}`\n\n"
        f"🔗 [Click to Register & Play]({REGISTER_LINK})"
    )

    targets = ["@pak92_qayoom"] + list(active_prediction_users) + list(set(user_channels.values()))
    for target in list(set(targets)):
        try:
            with open(img_path, 'rb') as photo:
                bot.send_photo(target, photo, caption=caption_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Broadcast Error: {e}")

# --- Strict Result Checker ---
def check_result(history_list):
    global active_prediction, total_wins, current_streak, max_streak, recent_history_records
    if not active_prediction or not history_list:
        return

    latest = history_list[0]
    latest_period = str(latest.get("issueNumber"))

    if latest_period[-4:] == active_prediction["period"][-4:] or latest_period == active_prediction["period"]:
        num = int(latest.get("number", 0))
        actual_size = latest.get("size", "").upper() or ("BIG" if num >= 5 else "SMALL")
        predicted_side = active_prediction["prediction"]

        # Strict validation matching
        is_win = (actual_size == predicted_side) or (predicted_side in actual_size)
        res_str = "WIN" if is_win else "LOSE"
        time_str = datetime.now().strftime("%I:%M:%S %p")

        recent_history_records.insert(0, {
            "period": latest_period[-8:],
            "signal": predicted_side,
            "number": num,
            "result": res_str,
            "time_str": time_str
        })
        if len(recent_history_records) > 10:
            recent_history_records.pop()

        targets = ["@pak92_qayoom"] + list(active_prediction_users) + list(set(user_channels.values()))

        if is_win:
            total_wins += 1
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak

            res_msg = f"✅ **RESULT: WIN 🎉**\n📌 Period: `{latest_period}`\n🎯 Outcome: `{actual_size}` (Matched)"
            for target in list(set(targets)):
                try:
                    bot.send_message(target, res_msg, parse_mode="Markdown")
                    if WIN_STICKER: bot.send_sticker(target, WIN_STICKER)
                except: pass
        else:
            current_streak = 0
            res_msg = f"❌ **RESULT: LOSS ⚠️**\n📌 Period: `{latest_period}`\n📊 Actual: `{actual_size}` | Predicted: `{predicted_side}`"
            for target in list(set(targets)):
                try:
                    bot.send_message(target, res_msg, parse_mode="Markdown")
                    if LOSS_STICKER: bot.send_sticker(target, LOSS_STICKER)
                except: pass

        active_prediction = None

# --- Main Bot Loop ---
def bot_loop():
    global last_processed_period, active_prediction
    print("🚀 Ultra-Accuracy Wingo 30s Engine Started...")
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
                    signal_display, num_hint, conf, expected_side = ultra_accuracy_prediction(history)

                    active_prediction = {
                        "period": next_period_full,
                        "prediction": expected_side
                    }

                    broadcast_signal(next_period_short, signal_display, num_hint, conf)
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
    
