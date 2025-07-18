# bot.py

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import time
from database import *
from utils import *

BOT_TOKEN = "7782600997:AAHkI0CBrgQqeFdykaI7qFWMEECYImmd00M"
bot = telebot.TeleBot(BOT_TOKEN)
OWNER_ID = 6940101627

YOUTUBE_LINK = "https://youtube.com/@bbottecbot?si=OI0u1AQFxYBpvl4f"
TELEGRAM_CHANNEL = "@boostlinkv"

@bot.message_handler(commands=["start"])
def start_cmd(message):
    user_id = message.from_user.id
    args = message.text.split(" ")
    if len(args) > 1:
        ref = args[1]
        if ref != str(user_id):
            add_referral(ref)
            bot.send_message(ref, f"🎉 You referred {message.from_user.first_name} and earned 1 referral.")

    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("✅ Joined Both", callback_data="verify_join"))
    msg = (
        f"👋 Hello {message.from_user.first_name}!\n\n"
        "Please join our required channels before using the bot:\n\n"
        f"📺 YouTube: [Click here]({YOUTUBE_LINK})\n"
        f"📢 Telegram: {TELEGRAM_CHANNEL}\n\n"
        "Click the button below once you’ve joined both."
    )
    bot.send_message(user_id, msg, reply_markup=keyboard, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "verify_join")
def verify_callback(call):
    user_id = call.from_user.id
    joined = check_telegram_channel_membership(bot, TELEGRAM_CHANNEL, user_id)
    subscribed = check_youtube_subscription(user_id)

    if joined and subscribed:
        set_user_joined(user_id)
        set_user_subscribed(user_id)
        bot.answer_callback_query(call.id, "✅ Verified!")
        show_main_menu(user_id)
    else:
        bot.answer_callback_query(call.id, "❌ Please make sure you joined both Telegram and YouTube.")

def show_main_menu(user_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("➕ Add Link", callback_data="add_link"))
    keyboard.add(InlineKeyboardButton("🔗 View/Stop Link", callback_data="view_link"))
    keyboard.add(InlineKeyboardButton("👥 Refer & Earn", callback_data="referral"))
    bot.send_message(user_id, "🔘 Main Menu:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda c: c.data == "add_link")
def add_link_callback(call):
    user_id = call.from_user.id
    if not is_user_subscribed(user_id):
        bot.answer_callback_query(call.id, "Please join channels first.")
        return

    if not has_allowance(user_id):
        bot.send_message(user_id, "❌ You must refer 3 users to earn 1-day posting allowance.")
        return

    bot.send_message(user_id, "🔗 Send the link you want to promote:")
    bot.register_next_step_handler(call.message, get_link_url)

def get_link_url(message):
    user_id = message.from_user.id
    url = message.text.strip()
    bot.send_message(user_id, "⏱ How many seconds should users stay on this link? (Example: 30)")
    bot.register_next_step_handler(message, lambda msg: set_link_duration(msg, url))

def set_link_duration(message, url):
    user_id = message.from_user.id
    try:
        duration = int(message.text.strip())
        if duration <= 0 or duration > 300:
            raise ValueError()
    except ValueError:
        bot.send_message(user_id, "⚠️ Please enter a valid number of seconds (1-300).")
        return

    add_link(user_id, url, duration)
    grant_allowance(user_id)
    bot.send_message(user_id, f"✅ Your link has been added for {duration} seconds.")
    show_main_menu(user_id)

@bot.callback_query_handler(func=lambda c: c.data == "view_link")
def view_user_link(call):
    user_id = call.from_user.id
    link_data = get_user_link(user_id)
    if not link_data:
        bot.send_message(user_id, "❌ You have not added any link yet.")
        return

    status = "🟢 Active" if link_data["active"] else "🔴 Stopped"
    msg = (
        f"🔗 Your Link: {link_data['url']}\n"
        f"⏱ Duration: {link_data['duration']} sec\n"
        f"📅 Posted: {link_data['start_time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"⚙️ Status: {status}"
    )
    keyboard = InlineKeyboardMarkup()
    if link_data["active"]:
        keyboard.add(InlineKeyboardButton("⛔ Stop Link", callback_data="stop_link"))
    bot.send_message(user_id, msg, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda c: c.data == "stop_link")
def stop_link_now(call):
    user_id = call.from_user.id
    stop_user_link(user_id)
    bot.send_message(user_id, "✅ Your link has been stopped.")
    show_main_menu(user_id)

@bot.callback_query_handler(func=lambda c: c.data == "referral")
def referral_menu(call):
    user_id = call.from_user.id
    ref_link = f"https://t.me/boostlinkv?start={user_id}"
    referrals = users.get(user_id, {}).get("referrals", 0)
    msg = (
        f"👥 Your Referral Link:\n`{ref_link}`\n\n"
        f"🎯 Referrals: {referrals}\n\n"
        "📌 Refer 3 users to get 1 day allowance to post your link."
    )
    bot.send_message(user_id, msg, parse_mode="Markdown")

bot.infinity_polling()