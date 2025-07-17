
import telebot
import requests
import time

# === CONFIGURATION ===
BOT_TOKEN = "7854510116:AAEpFEs3b_YVNs4jvFH6d1JOZ5Dern69_Sg"
OWNER_ID = 6976365864  # Replace with your Telegram ID

bot = telebot.TeleBot(BOT_TOKEN)

# === BOT STATE ===
user_settings = {}

@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⛔ Access denied. Only the bot owner can use this.")
        return

    bot.reply_to(message, "👋 Welcome to Auto Visitor Bot!\n\n"
                          "Please send the link you want to auto-visit.")

    user_settings[message.chat.id] = {
        'step': 'waiting_for_link'
    }

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    if message.from_user.id != OWNER_ID:
        return

    user_id = message.chat.id
    state = user_settings.get(user_id, {})

    if state.get('step') == 'waiting_for_link':
        url = message.text.strip()
        if not url.startswith("http"):
            bot.reply_to(message, "❌ Invalid URL. Please enter a valid link starting with http or https.")
            return

        state['url'] = url
        state['step'] = 'waiting_for_interval'
        bot.reply_to(message, "✅ Link saved.\n\nNow enter visit interval in seconds (e.g., 10):")
        return

    elif state.get('step') == 'waiting_for_interval':
        try:
            interval = int(message.text.strip())
            if interval <= 0:
                raise ValueError()
        except ValueError:
            bot.reply_to(message, "❌ Please enter a valid number of seconds.")
            return

        state['interval'] = interval
        state['step'] = 'running'
        bot.reply_to(message, f"🚀 Started visiting {state['url']} every {interval} seconds.\n\n"
                              f"Send /stop to end the visit loop.")

        # Start loop in background
        bot.send_message(user_id, "👀 Visiting...")
        start_visiting(user_id, state['url'], interval)

    elif message.text == "/stop":
        state['step'] = 'stopped'
        bot.reply_to(message, "🛑 Visiting stopped.")
        return

    else:
        bot.reply_to(message, "❓ Send /start to begin.")

def start_visiting(user_id, url, interval):
    def visit_loop():
        while user_settings.get(user_id, {}).get('step') == 'running':
            try:
                response = requests.get(url)
                print(f"Visited {url} - Status: {response.status_code}")
            except Exception as e:
                print(f"Error visiting {url}: {e}")
            time.sleep(interval)
    import threading
    threading.Thread(target=visit_loop, daemon=True).start()

bot.polling()