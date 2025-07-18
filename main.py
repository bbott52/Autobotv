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
user_links = {}

def show_main_buttons(user_id):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("➕ Add Link", callback_data="add_link"),
        InlineKeyboardButton("📄 My Links", callback_data="my_links")
    )
    markup.row(
        InlineKeyboardButton("💎 Buy Premium", callback_data="buy_premium"),
        InlineKeyboardButton("👥 Referral", callback_data="referral"),
    )
    markup.row(
        InlineKeyboardButton("🧑‍💼 Contact Admin", url="https://wa.me/2349114301708")
    )
    bot.send_message(user_id, "👋 Welcome to Link Visitor Bot!", reply_markup=markup)

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

@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data

    if data == "confirm_subscription":
        mark_subscribed(user_id)
        bot.answer_callback_query(call.id, "✅ Subscription confirmed!")
        show_main_buttons(user_id)

    elif data == "add_link":
        if not is_premium(user_id) and len(user_links.get(user_id, [])) >= 1:
            bot.answer_callback_query(call.id, "⛔ Trial expired or max link reached.")
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

    elif data == "my_links":
        links = user_links.get(user_id, [])
        if not links:
            bot.send_message(user_id, "📭 You haven’t added any links yet.")
            return
        markup = InlineKeyboardMarkup()
        for idx, url in enumerate(links):
            markup.row(InlineKeyboardButton(f"❌ Stop {idx+1}", callback_data=f"remove_{idx}"))
        links_str = "\n".join([f"{i+1}. {url}" for i, url in enumerate(links)])
        bot.send_message(user_id, f"🔗 Your Links:\n{links_str}", reply_markup=markup)

    elif data.startswith("remove_"):
        index = int(data.split("_")[1])
        links = user_links.get(user_id, [])
        if 0 <= index < len(links):
            removed = links.pop(index)
            active_visits[user_id] = {"step": None}
            bot.send_message(user_id, f"✅ Link removed: {removed}")
        else:
            bot.send_message(user_id, "❌ Invalid link number.")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    user_id = message.from_user.id
    text = message.text

    if user_id == OWNER_ID and text.startswith("confirm "):
        parts = text.split()
        if len(parts) == 3:
            target_id = int(parts[1])
            months = int(parts[2])
            set_premium(target_id, months * 30)
            bot.send_message(target_id, "✅ Premium activated.")
            bot.send_message(OWNER_ID, f"✅ User {target_id} upgraded for {months} month(s).")
        return

    state = active_visits.get(user_id, {})
    if state.get("step") == "waiting_for_link":
        url = text.strip()
        if not url.startswith("http"):
            bot.send_message(user_id, "❌ Invalid URL.")
            return

        user_links.setdefault(user_id, []).append(url)
        active_visits[user_id]["step"] = "running"

        bot.send_message(user_id, f"🚀 Visiting {url} every 30 seconds in background.")

        def visit():
            while url in user_links.get(user_id, []):
                try:
                    requests.get(url, headers=generate_headers(), timeout=5)
                    print(f"[{datetime.now()}] Visited {url}")
                except:
                    pass
                time.sleep(30)

        threading.Thread(target=visit, daemon=True).start()

    else:
        bot.send_message(user_id, "❓ Use /start or click a button.")

bot.polling()