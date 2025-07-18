import random
import qrcode
import io

def generate_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2 like Mac OS X)",
        "Mozilla/5.0 (Linux; Android 10)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (Windows NT 6.1; WOW64)"
    ]
    return random.choice(user_agents)

def generate_headers():
    return {
        'User-Agent': generate_user_agent(),
        'Accept': '*/*',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Connection': 'keep-alive'
    }

def generate_qr(bnb_address):
    img = qrcode.make(bnb_address)
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return bio