# utils.py

def check_youtube_subscription(user_id):
    return True  # Simulated for now

def check_telegram_channel_membership(bot, channel_username, user_id):
    try:
        member = bot.get_chat_member(channel_username, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False