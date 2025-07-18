from tinydb import TinyDB, Query
from datetime import datetime, timedelta

db = TinyDB("users.json")
User = Query()

def init_user(user_id, ref_by=None):
    if not db.contains(User.id == user_id):
        db.insert({
            'id': user_id,
            'is_admin': user_id == 6976365864,
            'premium_until': str(datetime.utcnow() + timedelta(days=3)),
            'ref_by': ref_by,
            'ref_count': 0,
            'subscribed': False
        })

def get_user(user_id):
    return db.get(User.id == user_id)

def set_premium(user_id, days):
    premium_until = datetime.utcnow() + timedelta(days=days)
    db.update({'premium_until': str(premium_until)}, User.id == user_id)

def is_premium(user_id):
    user = get_user(user_id)
    if not user:
        return False
    expiry = datetime.fromisoformat(user['premium_until'])
    return datetime.utcnow() < expiry

def add_referral(ref_id):
    user = get_user(ref_id)
    if user:
        count = user.get('ref_count', 0) + 1
        db.update({'ref_count': count}, User.id == ref_id)
        if count % 3 == 0:
            set_premium(ref_id, 1)

def has_subscribed(user_id):
    user = get_user(user_id)
    return user and user.get("subscribed", False)

def mark_subscribed(user_id):
    db.update({'subscribed': True}, User.id == user_id)