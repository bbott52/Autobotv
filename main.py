import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import requests
import threading
import time
from database import *
from utils import *

BOT_TOKEN = "7854510116:AAEpFEs3b_YVNs4jvFH6d1JOZ5Dern69_Sg"
OWNER_ID = 6976365864
BNB_ADDRESS = "0xa84bd2cfbBad66Ae2c5daf9aCe764dc845b94C7C"

bot = telebot.TeleBot(BOT_TOKEN)
active_visits = {}

# ---------------------- MAIN BUTTONS ----------------------
def show_main_buttons(user_id):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("➕ Add Link", callback_data="add_link"),
        InlineKeyboardButton("💎 Buy Premium", callback_data="buy_premium")
    )
    markup.row(
        InlineKeyboardButton("👥 Referral", callback_data="referral"),
        InlineKeyboardButton("🔗 Manage Links", callback_data="manage_links")
    )
    markup.row(
        InlineKeyboardButton("🧑‍💼 Contact Admin", url="https://wa.me/2349114301708")
    )
    bot.send_message(user_id, "👋 Welcome to Link Visitor Bot!", reply_markup=markup)

# ---------------------- /START HANDLER ----------------------
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    parts = message.text.strip().split()
    ref_by = None

    if len(parts) == 2 and parts[1].startswith("ref_"):
        ref_by = int(parts[1][4:])
        if ref_by != user_id:
            init_user(user_id, ref_by)
            add_referral(ref_by)

    init_user(user_id)

    if not has_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("📢 Join Telegram", url="https://t.me/boostlinkv"),
            InlineKeyboardButton("▶️ Subscribe YouTube", url="https://youtube.com/@bbottecbot?si=T7u0Y9s1WolxMFW8")
        )
        markup.row(
            InlineKeyboardButton("✅ I Have Subscribed", callback_data="confirm_subscription")
        )
        bot.send_message(user_id, "🔔 Before using the bot, please:\n\n"
                                  "1️⃣ Join our Telegram channel\n"
                                  "2️⃣ Subscribe to our YouTube\n\n"
                                  "Then click 'I Have Subscribed' below 👇", reply_markup=markup)
        return

    show_main_buttons(user_id)

# ---------------------- CALLBACK HANDLERS ----------------------
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data

    if data == "confirm_subscription":
        mark_subscribed(user_id)
        bot.answer_callback_query(call.id, "✅ Subscription confirmed!")
        show_main_buttons(user_id)

    elif data == "add_link":
        user_state = active_visits.get(user_id, {})
        can_add_multiple = user_state.get("can_add_multiple", False)

        if user_state.get("step") == "running" and not can_add_multiple:
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, "❌ You already have a running link. Stop it before adding a new one.")
            return

        bot.send_message(user_id, "🔗 Send the URL to auto-visit:")
        active_visits[user_id] = {"step": "waiting_for_link"}

    elif data == "buy_premium":
        qr = generate_qr(BNB_ADDRESS)
        bot.send_photo(user_id, qr, caption="💰 Pay to the BNB Address above:\n\n"
                         "5$ = 3 months\n10$ = 9 months\n20$ = 1.5 years\n50$ = Lifetime\n\n"
                         f"Address: `{BNB_ADDRESS}`", parse_mode="Markdown")
        bot.send_message(user_id, "📩 After payment, send a screenshot and TXID here.")

    elif data == "referral":
        link = f"https://t.me/linkvisitorbyurlbot?start=ref_{user_id}"
        bot.send_message(user_id, f"👥 Share your referral link:\n{link}")

    elif data == "manage_links":
        user_state = active_visits.get(user_id)

        if not user_state or user_state.get("step") != "running":
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, "😕 You have no active links.")
            return

        url = user_state.get("link")
        interval = user_state.get("interval", "unknown")

        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🛑 Stop Visiting", callback_data="stop_visiting")
        )
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, f"🔗 Currently visiting:\n{url}\n⏱️ Interval: {interval} seconds", reply_markup=markup)

    elif data == "stop_visiting":
        if user_id in active_visits:
            active_visits.pop(user_id)
            bot.answer_callback_query(call.id, "🛑 Visiting stopped.")
            bot.send_message(user_id, "✅ Your link visiting has been stopped.")
        else:
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, "❌ No active visiting found.")

# ---------------------- MESSAGE HANDLER ----------------------
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # OWNER: Confirm Premium
    if user_id == OWNER_ID and text.startswith("confirm "):
        parts = text.split()
        if len(parts) == 3:
            target_id = int(parts[1])
            months = int(parts[2])
            set_premium(target_id, months * 30)
            bot.send_message(target_id, "✅ Premium activated.")
            bot.send_message(OWNER_ID, f"✅ User {target_id} upgraded for {months} month(s).")
        return

    # OWNER: Allow Multiple Links
    if user_id == OWNER_ID and text.startswith("allow_multiple "):
        target_id = int(text.split()[1])
        if target_id not in active_visits:
            active_visits[target_id] = {}
        active_visits[target_id]["can_add_multiple"] = True
        bot.send_message(OWNER_ID, f"✅ User {target_id} can now add multiple links.")
        return

    # Handle user interaction flow
    state = active_visits.get(user_id, {})
    step = state.get("step")

    if step == "waiting_for_link":
        url = text
        if not url.startswith("http"):
            bot.send_message(user_id, "❌ Invalid URL. Must start with http or https.")
            return
        active_visits[user_id]["link"] = url
        active_visits[user_id]["step"] = "waiting_for_interval"
        bot.send_message(user_id, "⏱️ How often (in seconds) should we visit this link?")
        return

    elif step == "waiting_for_interval":
        try:
            interval = int(text)
            if interval < 10:
                bot.send_message(user_id, "⚠️ Interval must be at least 10 seconds.")
                return
        except ValueError:
            bot.send_message(user_id, "❌ Please enter a valid number.")
            return

        url = active_visits[user_id]["link"]
        active_visits[user_id]["interval"] = interval
        active_visits[user_id]["step"] = "running"
        bot.send_message(user_id, f"🚀 Now visiting:\n{url}\nEvery {interval} seconds.")

        def visit():
            while active_visits.get(user_id, {}).get("step") == "running":
                try:
                    requests.get(url, headers=generate_headers(), timeout=5)
                    print(f"[{datetime.now()}] Visited {url}")
                except:
                    print(f"[{datetime.now()}] Error visiting {url}")
                time.sleep(interval)

        threading.Thread(target=visit, daemon=True).start()
        return

    # Default fallback
    bot.send_message(user_id, "❓ Use /start or click a menu button.")

# ---------------------- START POLLING ----------------------
bot.polling()