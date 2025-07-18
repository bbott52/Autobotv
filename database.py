# database.py

from datetime import datetime, timedelta

users = {}
links = {}

def is_user_subscribed(user_id):
    user = users.get(user_id, {})
    return user.get("joined", False) and user.get("subscribed", False)

def set_user_joined(user_id):
    users.setdefault(user_id, {})["joined"] = True

def set_user_subscribed(user_id):
    users.setdefault(user_id, {})["subscribed"] = True

def add_referral(referrer_id):
    user = users.setdefault(referrer_id, {})
    user["referrals"] = user.get("referrals", 0) + 1

def has_allowance(user_id):
    user = users.get(user_id, {})
    return user.get("referrals", 0) >= 3 or user.get("allowance_expiry", datetime.min) > datetime.utcnow()

def grant_allowance(user_id):
    users.setdefault(user_id, {})["allowance_expiry"] = datetime.utcnow() + timedelta(days=1)
    users[user_id]["referrals"] = 0

def add_link(user_id, url, duration):
    links[user_id] = {"url": url, "duration": duration, "active": True, "start_time": datetime.utcnow()}

def get_user_link(user_id):
    return links.get(user_id)

def stop_user_link(user_id):
    if user_id in links:
        links[user_id]["active"] = False