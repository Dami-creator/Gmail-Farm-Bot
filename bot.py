from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
import re
import json
import os
import sys
import threading
import time

# ========== YOUR DETAILS ==========
API_ID = 32349198
API_HASH = "d7540ba8c42381a1e6f230b94f5eae4b"
BOT_TOKEN = "8639197079:AAGgAfEYfTqQ1YbiJmi2Zykxv-Ln3UneXog"

# ========== YOUR SESSION STRING ==========
SESSION_STRING = "1BJWap1wBu7hFsznAj1eUTupUVTsAECjGZETe1K2neK1rYjLAblAgXdqdgdO1Qhw1YqzstaERNBrLGDEw6wG6Zt18HqSgt55rj7rdBIvnsybmhuZGkdIkHahvcE1nT75LS4skNyjzrEgp26PxPIVN71udyHGpNRNgUT81Vcb_HxVn7qr5Na0oKMTWM22NwYmtLHTxgcZrilwzFlifNidj7k2aozntlyKspEnOu_7nldrH31d_mUTlXN2av1mnKB40HYoM8y4uaCvx_RLryOureR9ARaYdw1XkIDpLDLAI0s8boGP5wDQYkov4vV7eYx2i-AWZ0uVTCkdbAT_P3P5GC80GSNcj6Gc="
# ==========================================

REAL_BOT = "@GmailFProBot"

users = {}
if os.path.exists("users.json"):
    with open("users.json", "r") as f:
        users = json.load(f)

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

# Simple HTTP server to keep Render awake
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Bot is running!')
        elif self.path == '/users':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(users).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_http_server():
    try:
        server = HTTPServer(('0.0.0.0', 8000), HealthHandler)
        server.serve_forever()
    except:
        pass

# Start HTTP server in background
threading.Thread(target=run_http_server, daemon=True).start()

print("🚀 Starting...")

# Create clients with a new event loop
user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient("front_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

waiting_users = []

@user_client.on(events.NewMessage(from_users=REAL_BOT))
async def catch_reply(event):
    text = event.raw_text
    print(f"[CAPTURED] {text}")
    
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@gmail\.com', text)
    password_match = re.search(r'(?:pass|pw|password)[\s:]+([^\s\n]+)', text, re.IGNORECASE)
    
    if email_match and password_match and waiting_users:
        user_id = waiting_users.pop(0)
        email = email_match.group(0)
        password = password_match.group(1)
        
        if str(user_id) not in users:
            users[str(user_id)] = {"total": 0, "pending": 0.0, "accounts": []}
        users[str(user_id)]["accounts"].append({"email": email, "password": password})
        save_users()
        
        await bot_client.send_message(
            user_id,
            f"📧 New Account\nEmail: {email}\nPassword: {password}\n\nCreate it, then /confirm"
        )

@bot_client.on(events.NewMessage(pattern='/start'))
async def start_cmd(event):
    await event.respond("💰 Gmail Farm Pro\nSend /task to get an account")

@bot_client.on(events.NewMessage(pattern='/task'))
async def task_cmd(event):
    waiting_users.append(event.sender_id)
    await user_client.send_message(REAL_BOT, "/new")
    await event.respond("⏳ Generating...")

@bot_client.on(events.NewMessage(pattern='/confirm'))
async def confirm_cmd(event):
    uid = str(event.sender_id)
    if uid not in users:
        users[uid] = {"total": 0, "pending": 0.0, "accounts": []}
    users[uid]["total"] += 1
    users[uid]["pending"] += 1.00
    save_users()
    await user_client.send_message(REAL_BOT, "Done")
    await event.respond(f"✅ +$1.00\nTotal pending: ${users[uid]['pending']:.2f}")

@bot_client.on(events.NewMessage(pattern='/balance'))
async def balance_cmd(event):
    uid = str(event.sender_id)
    if uid not in users:
        users[uid] = {"total": 0, "pending": 0.0, "accounts": []}
    await event.respond(f"💰 Balance: ${users[uid]['pending']:.2f}")

@bot_client.on(events.NewMessage(pattern='/withdraw'))
async def withdraw_cmd(event):
    uid = str(event.sender_id)
    if uid not in users:
        users[uid] = {"total": 0, "pending": 0.0, "accounts": []}
    total = users[uid]["total"]
    if total < 50:
        await event.respond(f"❌ Need 50 accounts. You have {total}.")
    else:
        await event.respond("⏳ Withdrawal requested. Under review.")

@bot_client.on(events.NewMessage(pattern='/history'))
async def history_cmd(event):
    await event.respond(
        "📜 Recent Withdrawals\n\n"
        "User @john_doe - $52.00 - PAID\n"
        "User @jane_smith - $48.00 - PAID\n"
        "User @mike_23 - $61.00 - PAID"
    )

async def main():
    print("✅ HTTP server running on port 8000")
    print("✅ User client connecting...")
    await user_client.start()
    print("✅ User client connected!")
    print("✅ Bot client connected!")
    print("✅ Running. Listening to @GmailFProBot")
    
    # Keep running
    while True:
        try:
            await asyncio.sleep(30)
        except Exception as e:
            print(f"Keep-alive error: {e}")
            if not user_client.is_connected():
                print("Reconnecting user client...")
                await user_client.connect()
            if not bot_client.is_connected():
                print("Reconnecting bot client...")
                await bot_client.connect()

if __name__ == "__main__":
    asyncio.run(main())
