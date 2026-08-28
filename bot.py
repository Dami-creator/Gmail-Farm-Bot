from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon import Button
import asyncio
import re
import json
import os
import sys
from datetime import datetime
import random
import string
import traceback

# ========== YOUR DETAILS ==========
API_ID = 32349198
API_HASH = "d7540ba8c42381a1e6f230b94f5eae4b"
BOT_TOKEN = "8639197079:AAGgAfEYfTqQ1YbiJmi2Zykxv-Ln3UneXog"
ADMIN_ID = 8461617516

# ========== YOUR SESSION STRING ==========
SESSION_STRING = "1BJWap1sBu0YynaXeQAIeZAzaPaLpxpBERSZhzjcHy_h_sfcjlNhcjFRS2e8Za-G7zrY6fNirZZwpJIRxkgo3249mgwt0HXps1bRJWPoSVdWiRZhpV6wLQOMe3yqmuhLRzMdNRWVURBFfpEhkiYpjEU1dGt9FHdO6cTp8DH0J8ZP92km3KbHK3pJUamYIX351pVQV18t0kKQsqc__KzDf2ZPxtrgRmQOxOFk9-Mq6CUUE3Co_GDBYbgk8YSZ-_fVnavJBL87ZlW84jORgpk9_wFlC_jO4ktnv6BtpJ1wYdFbLPG4Q2-7lSsc2ZgUNShIoVyl41q3Fx1XMj33pr0C4TQl_p0qwOEY="
# ==========================================

REAL_BOT = "@GmailFProBot"
MAX_PENDING_TASKS = 5
REFERRAL_BONUS = 0.20

users = {}
if os.path.exists("users.json"):
    with open("users.json", "r") as f:
        users = json.load(f)

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient("bot_session", API_ID, API_HASH)

waiting_users = []
processing_users = set()

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_bot_username():
    return "MyFarmBot12_bot"

@user_client.on(events.NewMessage(from_users=REAL_BOT))
async def catch_reply(event):
    try:
        text = event.raw_text
        print(f"[CAPTURED] {text}")
        
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@gmail\.com', text)
        password_match = re.search(r'(?:pass|pw|password)[\s:]+([^\s\n]+)', text, re.IGNORECASE)
        
        if email_match and password_match and waiting_users:
            user_id = waiting_users.pop(0)
            email = email_match.group(0)
            password = password_match.group(1)
            
            uid = str(user_id)
            if uid not in users:
                users[uid] = {
                    "total": 0,
                    "pending": 0.0,
                    "on_hold": 0.0,
                    "referral_code": generate_referral_code(),
                    "referred_by": None,
                    "referrals": [],
                    "referral_earnings": 0.0,
                    "accounts": []
                }
                save_users()
            
            users[uid]["accounts"].append({
                "email": email,
                "password": password,
                "status": "pending",
                "timestamp": datetime.now().isoformat(),
                "original_message_id": event.id
            })
            save_users()
            
            buttons = [
                [Button.inline("✅ Done", "confirm_account")],
                [Button.inline("🔄 Cancel registration", "cancel_registration")],
                [Button.inline("❓ How to create account", "how_to")]
            ]
            
            await bot_client.send_message(
                user_id,
                f"📧 **New Account Generated**\n\n"
                f"👤 **Email:** `{email}`\n"
                f"🔑 **Password:** `{password}`\n\n"
                f"⚠️ Be sure to use the specified data, otherwise the account will not be paid.\n\n"
                f"📌 **Instructions:**\n"
                f"➡️ Go to Gmail.com\n"
                f"➡️ Create this account using the details above\n"
                f"➡️ Click **'Done'** when finished\n\n"
                f"💰 **Reward:** $0.50 (on hold until verified)\n"
                f"📊 **Pending Tasks:** {len([a for a in users[uid]['accounts'] if a['status'] == 'pending'])}/{MAX_PENDING_TASKS}",
                buttons=buttons
            )
            print(f"✅ Credentials sent to user {user_id}")
    except Exception as e:
        print(f"❌ Error in catch_reply: {e}")
        traceback.print_exc()

@bot_client.on(events.NewMessage(pattern='/start'))
async def start_cmd(event):
    try:
        uid = str(event.sender_id)
        print(f"✅ /start received from {uid}")
        
        if uid not in users:
            users[uid] = {
                "total": 0,
                "pending": 0.0,
                "on_hold": 0.0,
                "referral_code": generate_referral_code(),
                "referred_by": None,
                "referrals": [],
                "referral_earnings": 0.0,
                "accounts": []
            }
            save_users()
        
        args = event.text.split()
        ref_code = None
        if len(args) > 1:
            ref_code = args[1]
            if ref_code:
                for user_id, data in users.items():
                    if data.get("referral_code") == ref_code and user_id != uid:
                        users[uid]["referred_by"] = user_id
                        users[user_id]["referrals"].append(uid)
                        save_users()
                        
                        await bot_client.send_message(
                            int(user_id),
                            f"👤 **New Referral!**\n\n"
                            f"Someone joined using your referral link!\n"
                            f"💰 You'll earn **${REFERRAL_BONUS:.2f}** when they verify their first account.\n\n"
                            f"📊 Total referrals: {len(users[user_id]['referrals'])}"
                        )
                        
                        await event.respond(
                            "✅ **You were referred!**\n\n"
                            "💰 You'll both earn bonuses when you verify your first account!\n"
                            "📌 Send /task to get started!"
                        )
                        break
        
        bot_username = get_bot_username()
        ref_code = users[uid].get("referral_code", generate_referral_code())
        if "referral_code" not in users[uid]:
            users[uid]["referral_code"] = ref_code
            save_users()
        
        referral_link = f"https://t.me/{bot_username}?start={ref_code}"
        
        referred_by = users[uid].get("referred_by")
        referrer_info = ""
        if referred_by:
            referrer_info = f"\n👤 **Referred by:** {referred_by}"
        
        buttons = [
            [Button.inline("➕ New Account", "new_task")],
            [Button.inline("📋 My accounts", "my_tasks")],
            [Button.inline("💰 Balance", "my_balance")],
            [Button.inline("👤 My referrals", "referrals")],
            [Button.inline("🔄 Cancel registration", "cancel_registration")],
            [Button.inline("❓ Help", "help")]
        ]
        
        await event.respond(
            f"💰 **Gmail Farmer PRO** 💰\n\n"
            f"💵 Earn **$0.50** per Gmail account!\n"
            f"✅ Quick verification (2-5 mins)\n"
            f"✅ Create up to 5 accounts at once\n"
            f"✅ Cancel anytime\n"
            f"✅ Withdraw from $5.00 (just 10 accounts!)\n"
            f"✅ 24-hour hold period\n"
            f"✅ **Referral Bonus: ${REFERRAL_BONUS:.2f}** per referral{referrer_info}\n\n"
            f"🔗 **Your Referral Link:**\n"
            f"`{referral_link}`\n\n"
            f"📌 **Menu:**",
            buttons=buttons
        )
        print(f"✅ /start response sent to {uid}")
        
    except Exception as e:
        print(f"❌ Error in /start: {e}")
        traceback.print_exc()
        await event.respond(f"⚠️ Error: {str(e)}")

async def task_handler(event):
    try:
        user_id = event.sender_id
        uid = str(user_id)
        
        if uid in processing_users:
            return
        processing_users.add(uid)
        
        try:
            if uid not in users:
                users[uid] = {
                    "total": 0,
                    "pending": 0.0,
                    "on_hold": 0.0,
                    "referral_code": generate_referral_code(),
                    "referred_by": None,
                    "referrals": [],
                    "referral_earnings": 0.0,
                    "accounts": []
                }
                save_users()
            
            pending_tasks = [acc for acc in users[uid]["accounts"] if acc["status"] == "pending"]
            
            if len(pending_tasks) >= MAX_PENDING_TASKS:
                await event.respond(
                    f"⏳ **You have {len(pending_tasks)} pending tasks**\n\n"
                    f"📌 Maximum {MAX_PENDING_TASKS} pending tasks allowed.\n"
                    f"⚡ Please complete or cancel them first."
                )
                return
            
            waiting_users.append(user_id)
            await user_client.send_message(REAL_BOT, "➕ New Account")
            await event.respond(
                f"⏳ **Generating new account...**\n"
                f"📌 Please wait 3-5 seconds.\n\n"
                f"📊 **Pending Tasks:** {len(pending_tasks) + 1}/{MAX_PENDING_TASKS}\n"
                f"💰 **Reward:** $0.50 (on hold until verified)"
            )
            print(f"✅ /task from {user_id}")
        finally:
            processing_users.discard(uid)
    except Exception as e:
        print(f"❌ Error in task_handler: {e}")
        traceback.print_exc()
        await event.respond(f"⚠️ Error: {str(e)}")
        processing_users.discard(uid)

@bot_client.on(events.NewMessage(pattern='/task'))
async def task_cmd(event):
    await task_handler(event)

async def cancel_on_original_bot():
    try:
        async for msg in user_client.iter_messages(REAL_BOT, limit=5):
            if msg.buttons:
                for row in msg.buttons:
                    for button in row:
                        if "Cancel" in button.text or "cancel" in button.text.lower():
                            print(f"✅ Found cancel button: {button.text}")
                            await msg.click(button.text)
                            print("✅ Clicked cancel on original bot")
                            await asyncio.sleep(2)
                            return True
        print("❌ No cancel button found on original bot")
        return False
    except Exception as e:
        print(f"❌ Error clicking cancel on original bot: {e}")
        return False

@bot_client.on(events.NewMessage(pattern='/cancel'))
async def cancel_cmd(event):
    try:
        uid = str(event.sender_id)
        
        if uid in processing_users:
            return
        processing_users.add(uid)
        
        try:
            if uid not in users:
                users[uid] = {
                    "total": 0,
                    "pending": 0.0,
                    "on_hold": 0.0,
                    "referral_code": generate_referral_code(),
                    "referred_by": None,
                    "referrals": [],
                    "referral_earnings": 0.0,
                    "accounts": []
                }
                save_users()
                await event.respond("❌ No pending tasks to cancel.")
                return
            
            pending = [acc for acc in users[uid]["accounts"] if acc["status"] == "pending"]
            
            if not pending:
                await event.respond(
                    "❌ **No pending tasks**\n\n"
                    "📌 Send `/task` to get a new account."
                )
                return
            
            # Try to cancel on original bot (silently)
            await cancel_on_original_bot()
            
            # Cancel locally
            for acc in pending:
                acc["status"] = "cancelled"
            save_users()
            
            # Clean user-facing message - no mention of original bot
            await event.respond(
                f"❌ **Registration Cancelled**\n\n"
                f"📌 {len(pending)} task(s) have been cancelled.\n"
                f"📊 **Available Slots:** {MAX_PENDING_TASKS}\n"
                f"💡 Send `/task` to start a new registration."
            )
            print(f"✅ /cancel from {uid}")
        finally:
            processing_users.discard(uid)
    except Exception as e:
        print(f"❌ Error in /cancel: {e}")
        traceback.print_exc()
        await event.respond(f"⚠️ Error: {str(e)}")
        processing_users.discard(uid)

@bot_client.on(events.NewMessage(pattern='/tasks'))
async def tasks_cmd(event):
    try:
        uid = str(event.sender_id)
        
        if uid in processing_users:
            return
        processing_users.add(uid)
        
        try:
            if uid not in users:
                users[uid] = {
                    "total": 0,
                    "pending": 0.0,
                    "on_hold": 0.0,
                    "referral_code": generate_referral_code(),
                    "referred_by": None,
                    "referrals": [],
                    "referral_earnings": 0.0,
                    "accounts": []
                }
                save_users()
                await event.respond("❌ No tasks found.")
                return
            
            accounts = users[uid]["accounts"]
            if not accounts:
                await event.respond("📭 **No tasks yet**\n\nSend `/task` to get started!")
                return
            
            pending = [acc for acc in accounts if acc["status"] == "pending"]
            verifying = [acc for acc in accounts if acc["status"] == "verifying"]
            verified = [acc for acc in accounts if acc["status"] == "verified"]
            rejected = [acc for acc in accounts if acc["status"] == "rejected"]
            cancelled = [acc for acc in accounts if acc["status"] == "cancelled"]
            
            msg = f"📋 **Your Accounts**\n\n"
            msg += f"⏳ **Pending:** {len(pending)}/{MAX_PENDING_TASKS}\n"
            msg += f"🔍 **Verifying:** {len(verifying)}\n"
            msg += f"✅ **Verified:** {len(verified)}\n"
            msg += f"❌ **Rejected:** {len(rejected)}\n"
            msg += f"🚫 **Cancelled:** {len(cancelled)}\n\n"
            
            if pending:
                msg += "**📌 Pending Accounts:**\n"
                for acc in pending[:5]:
                    msg += f"• `{acc['email']}`\n"
                if len(pending) > 5:
                    msg += f"• ... and {len(pending) - 5} more\n"
            
            if verifying:
                msg += "\n**🔍 Verifying Accounts:**\n"
                for acc in verifying[:5]:
                    msg += f"• `{acc['email']}`\n"
            
            if verified:
                msg += f"\n✅ **Verified:** {len(verified)} accounts\n"
                msg += f"💰 **Earned:** ${len(verified) * 0.50:.2f}\n"
            
            await event.respond(msg)
        finally:
            processing_users.discard(uid)
    except Exception as e:
        print(f"❌ Error in /tasks: {e}")
        traceback.print_exc()
        await event.respond(f"⚠️ Error: {str(e)}")
        processing_users.discard(uid)

@bot_client.on(events.NewMessage(pattern='/referrals'))
async def referrals_cmd(event):
    try:
        uid = str(event.sender_id)
        
        if uid in processing_users:
            return
        processing_users.add(uid)
        
        try:
            if uid not in users:
                users[uid] = {
                    "total": 0,
                    "pending": 0.0,
                    "on_hold": 0.0,
                    "referral_code": generate_referral_code(),
                    "referred_by": None,
                    "referrals": [],
                    "referral_earnings": 0.0,
                    "accounts": []
                }
                save_users()
            
            bot_username = get_bot_username()
            ref_code = users[uid].get("referral_code", generate_referral_code())
            referral_link = f"https://t.me/{bot_username}?start={ref_code}"
            
            referrals = users[uid].get("referrals", [])
            referral_earnings = users[uid].get("referral_earnings", 0.0)
            
            msg = f"👤 **My Referrals**\n\n"
            msg += f"🔗 **Your Referral Link:**\n"
            msg += f"`{referral_link}`\n\n"
            msg += f"💰 **Referral Bonus:** ${REFERRAL_BONUS:.2f} per referral\n"
            msg += f"📊 **Total Referrals:** {len(referrals)}\n"
            msg += f"🏦 **Referral Earnings:** ${referral_earnings:.2f}\n\n"
            
            if referrals:
                msg += "**📌 Referred Users:**\n"
                for ref_id in referrals[:10]:
                    msg += f"• `{ref_id}`\n"
                if len(referrals) > 10:
                    msg += f"• ... and {len(referrals) - 10} more\n"
            else:
                msg += "📌 **No referrals yet.**\n"
                msg += "Share your link and earn bonuses!"
            
            await event.respond(msg)
        finally:
            processing_users.discard(uid)
    except Exception as e:
        print(f"❌ Error in /referrals: {e}")
        traceback.print_exc()
        await event.respond(f"⚠️ Error: {str(e)}")
        processing_users.discard(uid)

@bot_client.on(events.NewMessage(pattern='/balance'))
async def balance_cmd(event):
    try:
        uid = str(event.sender_id)
        
        if uid in processing_users:
            return
        processing_users.add(uid)
        
        try:
            if uid not in users:
                users[uid] = {
                    "total": 0,
                    "pending": 0.0,
                    "on_hold": 0.0,
                    "referral_code": generate_referral_code(),
                    "referred_by": None,
                    "referrals": [],
                    "referral_earnings": 0.0,
                    "accounts": []
                }
                save_users()
            
            pending = users[uid]["pending"]
            on_hold = users[uid]["on_hold"]
            total = users[uid]["total"]
            verified_count = len([a for a in users[uid]["accounts"] if a["status"] == "verified"])
            referral_earnings = users[uid].get("referral_earnings", 0.0)
            
            await event.respond(
                f"💰 **Your Balance**\n\n"
                f"📊 **Accounts Created:** {total}\n"
                f"✅ **Verified:** {verified_count}\n"
                f"💰 **Ready to Withdraw:** ${pending:.2f}\n"
                f"⏳ **On Hold:** ${on_hold:.2f}\n"
                f"👤 **Referral Earnings:** ${referral_earnings:.2f}\n"
                f"🏦 **Total Earned:** ${pending + on_hold + referral_earnings:.2f}\n\n"
                f"💳 **Min Withdrawal:** $5.00\n"
                f"⏱️ **Hold Period:** 24 hours"
            )
        finally:
            processing_users.discard(uid)
    except Exception as e:
        print(f"❌ Error in /balance: {e}")
        traceback.print_exc()
        await event.respond(f"⚠️ Error: {str(e)}")
        processing_users.discard(uid)

@bot_client.on(events.NewMessage(pattern='/withdraw'))
async def withdraw_cmd(event):
    try:
        uid = str(event.sender_id)
        
        if uid in processing_users:
            return
        processing_users.add(uid)
        
        try:
            if uid not in users:
                users[uid] = {
                    "total": 0,
                    "pending": 0.0,
                    "on_hold": 0.0,
                    "referral_code": generate_referral_code(),
                    "referred_by": None,
                    "referrals": [],
                    "referral_earnings": 0.0,
                    "accounts": []
                }
                save_users()
            
            pending = users[uid]["pending"]
            total = users[uid]["total"]
            
            if total < 10:
                await event.respond(
                    f"❌ **Minimum Withdrawal: $5.00**\n\n"
                    f"📊 **Accounts Created:** {total}\n"
                    f"💰 **Current Balance:** ${pending + users[uid]['on_hold']:.2f}\n"
                    f"📝 **Need {10 - total} more accounts** to reach $5.00."
                )
            elif pending < 5.00:
                await event.respond(
                    f"⏳ **Hold Period Active**\n\n"
                    f"💰 **Ready to Withdraw:** ${pending:.2f}\n"
                    f"⏳ **On Hold:** ${users[uid]['on_hold']:.2f}\n"
                    f"📊 **Need ${5.00 - pending:.2f} more on hold to release.**"
                )
            else:
                await event.respond(
                    f"⏳ **Withdrawal Requested**\n\n"
                    f"💰 **Amount:** ${pending:.2f}\n"
                    f"📋 **Status:** Processing... (24-48 hours)\n"
                    f"🔒 **Security Verification:** In progress."
                )
        finally:
            processing_users.discard(uid)
    except Exception as e:
        print(f"❌ Error in /withdraw: {e}")
        traceback.print_exc()
        await event.respond(f"⚠️ Error: {str(e)}")
        processing_users.discard(uid)

@bot_client.on(events.NewMessage(pattern='/history'))
async def history_cmd(event):
    try:
        await event.respond(
            "📜 **Recent Withdrawals**\n\n"
            "👤 **User @john_doe** - $7.50 - ✅ PAID (1 day ago)\n"
            "👤 **User @jane_smith** - $6.00 - ✅ PAID (3 days ago)\n"
            "👤 **User @mike_23** - $12.50 - ✅ PAID (5 days ago)\n"
            "👤 **User @sarah_7** - $9.00 - ✅ PAID (2 days ago)\n"
            "👤 **User @alex_99** - $5.50 - ✅ PAID (4 days ago)\n\n"
            "💳 All payments via Payeer."
        )
    except Exception as e:
        print(f"❌ Error in /history: {e}")
        traceback.print_exc()
        await event.respond(f"⚠️ Error: {str(e)}")

@bot_client.on(events.NewMessage(pattern='/help'))
async def help_cmd(event):
    try:
        buttons = [
            [Button.inline("➕ New Account", "new_task")],
            [Button.inline("📋 My accounts", "my_tasks")],
            [Button.inline("💰 Balance", "my_balance")],
            [Button.inline("👤 My referrals", "referrals")]
        ]
        
        await event.respond(
            "📌 **Gmail Farmer PRO - Help**\n\n"
            "💰 **Earn $0.50 per Gmail account**\n"
            "✅ **Max 5 pending tasks**\n"
            "⏱️ **Verification:** 2-5 minutes\n"
            "❌ **Cancel tasks anytime**\n"
            "💳 **Min Withdrawal:** $5.00 (10 accounts!)\n"
            "⏳ **Hold Period:** 24 hours\n"
            "👤 **Referral Bonus:** $0.20 per referral\n\n"
            "📌 **Commands:**\n"
            "➕ `/task` - New account\n"
            "📋 `/tasks` - View your accounts\n"
            "🔄 `/cancel` - Cancel pending task\n"
            "💰 `/balance` - Check earnings\n"
            "💳 `/withdraw` - Request payout\n"
            "📜 `/history` - Recent payments\n"
            "👤 `/referrals` - Your referral link\n"
            "❓ `/help` - Show this menu\n\n"
            "💡 **Tip:** Create 10 accounts = $5.00 withdrawal!",
            buttons=buttons
        )
    except Exception as e:
        print(f"❌ Error in /help: {e}")
        traceback.print_exc()
        await event.respond(f"⚠️ Error: {str(e)}")

@bot_client.on(events.CallbackQuery)
async def handle_callback(event):
    try:
        await event.answer()
        
        data = event.data.decode()
        print(f"📩 Callback received: {data}")
        
        if data == "new_task":
            await task_handler(event)
        elif data == "my_tasks":
            await tasks_cmd(event)
        elif data == "my_balance":
            await balance_cmd(event)
        elif data == "referrals":
            await referrals_cmd(event)
        elif data == "help":
            await help_cmd(event)
        elif data == "confirm_account":
            await confirm_cmd(event)
        elif data == "cancel_registration":
            await cancel_cmd(event)
        elif data == "how_to":
            await event.respond(
                "📌 **How to Create a Gmail Account**\n\n"
                "1️⃣ Go to **gmail.com**\n"
                "2️⃣ Click **'Create account'**\n"
                "3️⃣ Enter the **Email** and **Password** provided\n"
                "4️⃣ Fill in the required details (any name/DOB)\n"
                "5️⃣ Skip phone verification if possible\n"
                "6️⃣ Once created, click **'Done'** to submit for verification\n\n"
                "⚠️ Make sure to use the exact email and password provided!"
            )
        else:
            await event.respond("❌ Unknown command.")
        
    except Exception as e:
        print(f"❌ Callback error: {e}")
        traceback.print_exc()

@bot_client.on(events.NewMessage(pattern='/confirm'))
async def confirm_cmd(event):
    try:
        uid = str(event.sender_id)
        
        if uid in processing_users:
            return
        processing_users.add(uid)
        
        try:
            if uid not in users:
                users[uid] = {
                    "total": 0,
                    "pending": 0.0,
                    "on_hold": 0.0,
                    "referral_code": generate_referral_code(),
                    "referred_by": None,
                    "referrals": [],
                    "referral_earnings": 0.0,
                    "accounts": []
                }
                save_users()
                await event.respond("❌ No pending accounts to confirm.")
                return
            
            pending = [acc for acc in users[uid]["accounts"] if acc["status"] == "pending"]
            
            if not pending:
                await event.respond(
                    "❌ **No pending accounts**\n\n"
                    "📌 Send `/task` to get a new account first."
                )
                return
            
            acc = pending[0]
            acc["status"] = "verifying"
            acc["confirm_time"] = datetime.now().isoformat()
            users[uid]["on_hold"] += 0.50
            users[uid]["total"] += 1
            save_users()
            
            remaining_pending = len([a for a in users[uid]["accounts"] if a["status"] == "pending"])
            
            # Silent click on original bot
            try:
                async for msg in user_client.iter_messages(REAL_BOT, limit=3):
                    if msg.buttons:
                        for row in msg.buttons:
                            for button in row:
                                if "Done" in button.text or "done" in button.text.lower():
                                    await msg.click(button.text)
                                    print("✅ Clicked Done on original bot")
                                    break
            except Exception as e:
                print(f"⚠️ Could not click Done on original bot: {e}")
            
            await bot_client.send_message(
                ADMIN_ID,
                f"🔍 **Verification Required**\n\n"
                f"👤 **User ID:** `{uid}`\n"
                f"📧 **Email:** `{acc['email']}`\n"
                f"🔑 **Password:** `{acc['password']}`\n"
                f"💰 **Amount:** $0.50\n"
                f"📅 **Submitted:** {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"✅ `/verify {uid}` - Approve\n"
                f"❌ `/reject {uid}` - Reject"
            )
            
            await event.respond(
                f"⏳ **Account Submitted for Verification**\n\n"
                f"📧 **Email:** `{acc['email']}`\n"
                f"⏱️ **Status:** Waiting for admin review...\n"
                f"💰 **Amount on Hold:** $0.50\n"
                f"📊 **Remaining Tasks:** {remaining_pending}/{MAX_PENDING_TASKS}\n\n"
                f"📌 You'll be notified when verified.\n"
                f"💡 Send `/task` for more accounts to boost your earnings!"
            )
            print(f"✅ /confirm from {uid}")
        finally:
            processing_users.discard(uid)
    except Exception as e:
        print(f"❌ Error in /confirm: {e}")
        traceback.print_exc()
        await event.respond(f"⚠️ Error: {str(e)}")
        processing_users.discard(uid)

@bot_client.on(events.NewMessage(pattern='/verify'))
async def verify_cmd(event):
    if event.sender_id != ADMIN_ID:
        await event.respond("⛔ Unauthorized.")
        return
    
    try:
        parts = event.text.split()
        if len(parts) < 2:
            await event.respond("❌ Usage: `/verify [user_id]`")
            return
        
        uid = parts[1]
        
        if uid not in users:
            await event.respond(f"❌ User {uid} not found.")
            return
        
        for acc in users[uid]["accounts"]:
            if acc["status"] == "verifying":
                acc["status"] = "verified"
                acc["verify_time"] = datetime.now().isoformat()
                users[uid]["on_hold"] -= 0.50
                users[uid]["pending"] += 0.50
                
                referred_by = users[uid].get("referred_by")
                if referred_by and referred_by in users:
                    verified_count = len([a for a in users[uid]["accounts"] if a["status"] == "verified"])
                    if verified_count == 1:
                        users[referred_by]["pending"] += REFERRAL_BONUS
                        users[referred_by]["referral_earnings"] += REFERRAL_BONUS
                        
                        await bot_client.send_message(
                            int(referred_by),
                            f"🎉 **Referral Bonus Earned!**\n\n"
                            f"👤 Someone you referred just verified their first account!\n"
                            f"💰 +${REFERRAL_BONUS:.2f} added to your balance.\n"
                            f"📊 Total referral earnings: ${users[referred_by]['referral_earnings']:.2f}"
                        )
                
                save_users()
                
                await bot_client.send_message(
                    int(uid),
                    f"✅ **Account Verified!**\n\n"
                    f"📧 **Email:** `{acc['email']}`\n"
                    f"💰 **Amount:** +$0.50 added to balance\n"
                    f"📊 **Pending Balance:** ${users[uid]['pending']:.2f}\n"
                    f"🏦 **Total Earned:** ${users[uid]['pending'] + users[uid]['on_hold']:.2f}\n\n"
                    f"⏳ Withdrawal available after 24 hours.\n"
                    f"💳 **Min Withdrawal:** $5.00"
                )
                
                await event.respond(f"✅ Verified account for user {uid}")
                return
        
        await event.respond(f"❌ No verifying accounts for user {uid}.")
    except Exception as e:
        print(f"❌ Error in /verify: {e}")
        traceback.print_exc()
        await event.respond(f"⚠️ Error: {str(e)}")

@bot_client.on(events.NewMessage(pattern='/reject'))
async def reject_cmd(event):
    if event.sender_id != ADMIN_ID:
        await event.respond("⛔ Unauthorized.")
        return
    
    try:
        parts = event.text.split()
        if len(parts) < 2:
            await event.respond("❌ Usage: `/reject [user_id]`")
            return
        
        uid = parts[1]
        
        if uid not in users:
            await event.respond(f"❌ User {uid} not found.")
            return
        
        for i, acc in enumerate(users[uid]["accounts"]):
            if acc["status"] == "verifying":
                acc["status"] = "rejected"
                users[uid]["on_hold"] -= 0.50
                users[uid]["total"] -= 1
                save_users()
                
                await bot_client.send_message(
                    int(uid),
                    f"❌ **Account Rejected**\n\n"
                    f"📧 **Email:** `{acc['email']}`\n"
                    f"⚠️ **Reason:** Verification failed.\n"
                    f"❗ No balance added.\n\n"
                    f"📌 Send `/task` to try again."
                )
                
                await event.respond(f"❌ Rejected account for user {uid}")
                return
        
        await event.respond(f"❌ No verifying accounts for user {uid}.")
    except Exception as e:
        print(f"❌ Error in /reject: {e}")
        traceback.print_exc()
        await event.respond(f"⚠️ Error: {str(e)}")

@bot_client.on(events.NewMessage(pattern='/admin_stats'))
async def admin_stats_cmd(event):
    if event.sender_id != ADMIN_ID:
        await event.respond("⛔ Unauthorized.")
        return
    
    try:
        total_users = len(users)
        total_accounts = sum(len(u["accounts"]) for u in users.values())
        total_verified = sum(len([a for a in u["accounts"] if a["status"] == "verified"]) for u in users.values())
        total_pending = sum(len([a for a in u["accounts"] if a["status"] == "pending"]) for u in users.values())
        total_verifying = sum(len([a for a in u["accounts"] if a["status"] == "verifying"]) for u in users.values())
        total_rejected = sum(len([a for a in u["accounts"] if a["status"] == "rejected"]) for u in users.values())
        total_cancelled = sum(len([a for a in u["accounts"] if a["status"] == "cancelled"]) for u in users.values())
        total_earned = sum(u["pending"] for u in users.values())
        total_referrals = sum(len(u.get("referrals", [])) for u in users.values())
        
        await event.respond(
            f"📊 **Admin Statistics**\n\n"
            f"👤 **Total Users:** {total_users}\n"
            f"📧 **Total Accounts:** {total_accounts}\n"
            f"✅ **Verified:** {total_verified}\n"
            f"⏳ **Pending:** {total_pending}\n"
            f"🔍 **Verifying:** {total_verifying}\n"
            f"❌ **Rejected:** {total_rejected}\n"
            f"🚫 **Cancelled:** {total_cancelled}\n"
            f"💰 **Total Paid Out:** ${total_earned:.2f}\n"
            f"👤 **Total Referrals:** {total_referrals}\n\n"
            f"📁 Data saved in `users.json`"
        )
    except Exception as e:
        print(f"❌ Error in /admin_stats: {e}")
        traceback.print_exc()
        await event.respond(f"⚠️ Error: {str(e)}")

async def main():
    print("🚀 Starting bot...")
    print("💰 Reward: $0.50 per verified account")
    print("👤 Referral Bonus: $0.20 per referral")
    print("💳 Min Withdrawal: $5.00")
    
    try:
        await user_client.start()
        print("✅ User client connected!")
    except Exception as e:
        print(f"❌ User client error: {e}")
        sys.exit(1)
    
    try:
        await bot_client.start(bot_token=BOT_TOKEN)
        print("✅ Bot client connected!")
    except Exception as e:
        print(f"❌ Bot client error: {e}")
        sys.exit(1)
    
    print("🎯 Running. Listening to @GmailFProBot")
    print(f"👤 Admin ID: {ADMIN_ID}")
    print("📡 Command to generate tasks: '➕ New Account'")
    print(f"📊 Max pending tasks: {MAX_PENDING_TASKS}")
    
    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⏹️ Bot stopped")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
