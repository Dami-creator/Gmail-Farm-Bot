from telethon import TelegramClient, events
import asyncio
import re
import json
import os
import sys
from datetime import datetime

# ========== YOUR DETAILS ==========
API_ID = 32349198
API_HASH = "d7540ba8c42381a1e6f230b94f5eae4b"
BOT_TOKEN = "8639197079:AAGgAfEYfTqQ1YbiJmi2Zykxv-Ln3UneXog"
ADMIN_ID = 8461617516  # REPLACE WITH YOUR TELEGRAM ID
# ==================================

REAL_BOT = "@GmailFProBot"
MAX_PENDING_TASKS = 5

# ========== FORCE SESSION FILE IN CURRENT DIRECTORY ==========
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# ==============================================================

users = {}
if os.path.exists("users.json"):
    with open("users.json", "r") as f:
        users = json.load(f)

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

# ========== USE SESSION FILE (workdir removed) ==========
user_client = TelegramClient("user_session", API_ID, API_HASH)
bot_client = TelegramClient("bot_session", API_ID, API_HASH)

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
        
        uid = str(user_id)
        if uid not in users:
            users[uid] = {"total": 0, "pending": 0.0, "on_hold": 0.0, "accounts": []}
        
        users[uid]["accounts"].append({
            "email": email,
            "password": password,
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        })
        save_users()
        
        await bot_client.send_message(
            user_id,
            f"📧 **New Account Generated**\n\n"
            f"👤 **Email:** `{email}`\n"
            f"🔑 **Password:** `{password}`\n\n"
            f"📌 **Instructions:**\n"
            f"➡️ Go to Gmail.com\n"
            f"➡️ Create this account\n"
            f"➡️ Send `/confirm` to submit for verification\n\n"
            f"💰 **Reward:** $0.50 (on hold until verified)\n"
            f"📊 **Pending Tasks:** {len([a for a in users[uid]['accounts'] if a['status'] == 'pending'])}/{MAX_PENDING_TASKS}\n"
            f"⏳ You can request more tasks while waiting!\n"
            f"❌ To cancel, send `/cancel`"
        )
        print(f"✅ Credentials sent to user {user_id}")

@bot_client.on(events.NewMessage(pattern='/start'))
async def start_cmd(event):
    uid = str(event.sender_id)
    if uid not in users:
        users[uid] = {"total": 0, "pending": 0.0, "on_hold": 0.0, "accounts": []}
        save_users()
    
    await event.respond(
        "💰 **Earn $0.50 Per Gmail Account!** 💰\n\n"
        "💵 **Start earning immediately!**\n"
        "✅ $0.50 per verified account\n"
        "✅ Quick verification (2-5 mins)\n"
        "✅ Create up to 5 accounts at once\n"
        "✅ Cancel anytime\n"
        "✅ Withdraw from $5.00 (just 10 accounts!)\n"
        "✅ 24-hour hold period\n\n"
        "📌 **Get Started Now:**\n"
        "➕ `/task` - Get your first account\n"
        "✅ `/confirm` - Submit for verification\n"
        "📋 `/tasks` - View your progress\n"
        "💰 `/balance` - Track your earnings\n"
        "💳 `/withdraw` - Request payout\n\n"
        "💡 **Tip:** Create 10 accounts = $5.00 withdrawal!\n"
        "🚀 Start now and watch your balance grow!"
    )
    print(f"✅ /start from {event.sender_id}")

@bot_client.on(events.NewMessage(pattern='/task'))
async def task_cmd(event):
    user_id = event.sender_id
    uid = str(user_id)
    
    if uid not in users:
        users[uid] = {"total": 0, "pending": 0.0, "on_hold": 0.0, "accounts": []}
        save_users()
    
    pending_tasks = [acc for acc in users[uid]["accounts"] if acc["status"] == "pending"]
    
    if len(pending_tasks) >= MAX_PENDING_TASKS:
        await event.respond(
            f"⏳ **You have {len(pending_tasks)} pending tasks**\n\n"
            f"📌 Maximum {MAX_PENDING_TASKS} pending tasks allowed.\n"
            f"⚡ Please complete or cancel them first.\n\n"
            f"📋 Use `/tasks` to view pending.\n"
            f"❌ Use `/cancel` to cancel a task."
        )
        return
    
    waiting_users.append(user_id)
    await user_client.send_message(REAL_BOT, "➕ New Account")
    await event.respond(
        f"⏳ **Generating new account...**\n"
        f"📌 Please wait 3-5 seconds.\n\n"
        f"📊 **Pending Tasks:** {len(pending_tasks) + 1}/{MAX_PENDING_TASKS}\n"
        f"💰 **Reward:** $0.50 (on hold until verified)\n"
        f"💡 You can request more tasks while waiting!\n"
        f"❌ To cancel, use `/cancel`"
    )
    print(f"✅ /task from {user_id}")

@bot_client.on(events.NewMessage(pattern='/confirm'))
async def confirm_cmd(event):
    uid = str(event.sender_id)
    
    if uid not in users:
        users[uid] = {"total": 0, "pending": 0.0, "on_hold": 0.0, "accounts": []}
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
        f"💡 Send `/task` for more accounts to boost your earnings!\n"
        f"🏦 **Target:** $5.00 minimum withdrawal (10 accounts)"
    )
    print(f"✅ /confirm from {uid}")

@bot_client.on(events.NewMessage(pattern='/cancel'))
async def cancel_cmd(event):
    uid = str(event.sender_id)
    
    if uid not in users:
        users[uid] = {"total": 0, "pending": 0.0, "on_hold": 0.0, "accounts": []}
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
    
    cancelled_count = 0
    for acc in pending:
        acc["status"] = "cancelled"
        cancelled_count += 1
    save_users()
    
    await event.respond(
        f"❌ **Registration Cancelled**\n\n"
        f"📌 {cancelled_count} task(s) have been cancelled.\n"
        f"📊 **Available Slots:** {MAX_PENDING_TASKS}\n"
        f"💡 Send `/task` to start a new registration.\n"
        f"💰 Earn $0.50 per verified account!"
    )
    print(f"✅ /cancel from {uid}")

@bot_client.on(events.NewMessage(pattern='/tasks'))
async def tasks_cmd(event):
    uid = str(event.sender_id)
    
    if uid not in users:
        users[uid] = {"total": 0, "pending": 0.0, "on_hold": 0.0, "accounts": []}
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
    
    msg = f"📋 **Your Tasks**\n\n"
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
        msg += f"\n❌ To cancel, use `/cancel`\n"
    
    if verifying:
        msg += "\n**🔍 Verifying Accounts:**\n"
        for acc in verifying[:5]:
            msg += f"• `{acc['email']}`\n"
    
    if verified:
        msg += f"\n✅ **Verified:** {len(verified)} accounts\n"
        msg += f"💰 **Earned:** ${len(verified) * 0.50:.2f}\n"
    
    await event.respond(msg)

# ========== ADMIN COMMANDS ==========

@bot_client.on(events.NewMessage(pattern='/verify'))
async def verify_cmd(event):
    if event.sender_id != ADMIN_ID:
        await event.respond("⛔ Unauthorized.")
        return
    
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
            save_users()
            
            await bot_client.send_message(
                int(uid),
                f"✅ **Account Verified!**\n\n"
                f"📧 **Email:** `{acc['email']}`\n"
                f"💰 **Amount:** +$0.50 added to balance\n"
                f"📊 **Pending Balance:** ${users[uid]['pending']:.2f}\n"
                f"🏦 **Total Earned:** ${users[uid]['pending'] + users[uid]['on_hold']:.2f}\n\n"
                f"⏳ Withdrawal available after 24 hours.\n"
                f"💳 **Min Withdrawal:** $5.00\n"
                f"📌 Send `/task` for more accounts to boost your earnings!"
            )
            
            await event.respond(f"✅ Verified account for user {uid}")
            return
    
    await event.respond(f"❌ No verifying accounts for user {uid}.")

@bot_client.on(events.NewMessage(pattern='/reject'))
async def reject_cmd(event):
    if event.sender_id != ADMIN_ID:
        await event.respond("⛔ Unauthorized.")
        return
    
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
                f"📌 Send `/task` to try again.\n"
                f"💰 Earn $0.50 per verified account!"
            )
            
            await event.respond(f"❌ Rejected account for user {uid}")
            return
    
    await event.respond(f"❌ No verifying accounts for user {uid}.")

@bot_client.on(events.NewMessage(pattern='/admin_stats'))
async def admin_stats_cmd(event):
    if event.sender_id != ADMIN_ID:
        await event.respond("⛔ Unauthorized.")
        return
    
    total_users = len(users)
    total_accounts = sum(len(u["accounts"]) for u in users.values())
    total_verified = sum(len([a for a in u["accounts"] if a["status"] == "verified"]) for u in users.values())
    total_pending = sum(len([a for a in u["accounts"] if a["status"] == "pending"]) for u in users.values())
    total_verifying = sum(len([a for a in u["accounts"] if a["status"] == "verifying"]) for u in users.values())
    total_rejected = sum(len([a for a in u["accounts"] if a["status"] == "rejected"]) for u in users.values())
    total_cancelled = sum(len([a for a in u["accounts"] if a["status"] == "cancelled"]) for u in users.values())
    total_earned = sum(u["pending"] for u in users.values())
    
    await event.respond(
        f"📊 **Admin Statistics**\n\n"
        f"👤 **Total Users:** {total_users}\n"
        f"📧 **Total Accounts:** {total_accounts}\n"
        f"✅ **Verified:** {total_verified}\n"
        f"⏳ **Pending:** {total_pending}\n"
        f"🔍 **Verifying:** {total_verifying}\n"
        f"❌ **Rejected:** {total_rejected}\n"
        f"🚫 **Cancelled:** {total_cancelled}\n"
        f"💰 **Total Paid Out:** ${total_earned:.2f}\n\n"
        f"📁 Data saved in `users.json`"
    )

# ========== USER COMMANDS ==========

@bot_client.on(events.NewMessage(pattern='/balance'))
async def balance_cmd(event):
    uid = str(event.sender_id)
    if uid not in users:
        users[uid] = {"total": 0, "pending": 0.0, "on_hold": 0.0, "accounts": []}
        save_users()
    
    pending = users[uid]["pending"]
    on_hold = users[uid]["on_hold"]
    total = users[uid]["total"]
    verified_count = len([a for a in users[uid]["accounts"] if a["status"] == "verified"])
    
    await event.respond(
        f"💰 **Your Earnings**\n\n"
        f"📊 **Accounts Created:** {total}\n"
        f"✅ **Verified:** {verified_count}\n"
        f"💰 **Ready to Withdraw:** ${pending:.2f}\n"
        f"⏳ **On Hold:** ${on_hold:.2f}\n"
        f"🏦 **Total Earned:** ${pending + on_hold:.2f}\n\n"
        f"💳 **Min Withdrawal:** $5.00\n"
        f"⏱️ **Hold Period:** 24 hours\n\n"
        f"📌 Create {max(0, int((5.00 - pending) / 0.50))} more accounts to withdraw!\n"
        f"💡 Send `/task` to earn more!"
    )

@bot_client.on(events.NewMessage(pattern='/withdraw'))
async def withdraw_cmd(event):
    uid = str(event.sender_id)
    if uid not in users:
        users[uid] = {"total": 0, "pending": 0.0, "on_hold": 0.0, "accounts": []}
        save_users()
    
    pending = users[uid]["pending"]
    total = users[uid]["total"]
    
    if total < 10:
        await event.respond(
            f"❌ **Minimum Withdrawal: $5.00**\n\n"
            f"📊 **Accounts Created:** {total}\n"
            f"💰 **Current Balance:** ${pending + users[uid]['on_hold']:.2f}\n"
            f"📝 **Need {10 - total} more accounts** to reach $5.00.\n\n"
            f"📌 Send `/task` to earn $0.50 per account!\n"
            f"💡 Create just 10 accounts to withdraw your first $5.00!"
        )
    elif pending < 5.00:
        await event.respond(
            f"⏳ **Hold Period Active**\n\n"
            f"💰 **Ready to Withdraw:** ${pending:.2f}\n"
            f"⏳ **On Hold:** ${users[uid]['on_hold']:.2f}\n"
            f"📊 **Need ${5.00 - pending:.2f} more on hold to release.**\n\n"
            f"⏱️ Wait 24 hours or complete more accounts.\n"
            f"💡 Create {int((5.00 - pending) / 0.50)} more accounts to withdraw!"
        )
    else:
        await event.respond(
            f"⏳ **Withdrawal Requested**\n\n"
            f"💰 **Amount:** ${pending:.2f}\n"
            f"📋 **Status:** Processing... (24-48 hours)\n"
            f"🔒 **Security Verification:** In progress.\n\n"
            f"✅ You'll receive confirmation shortly.\n"
            f"📌 Keep creating accounts to earn more!"
        )

@bot_client.on(events.NewMessage(pattern='/history'))
async def history_cmd(event):
    await event.respond(
        "📜 **Recent Withdrawals**\n\n"
        "👤 **User @john_doe** - $7.50 - ✅ PAID (1 day ago)\n"
        "👤 **User @jane_smith** - $6.00 - ✅ PAID (3 days ago)\n"
        "👤 **User @mike_23** - $12.50 - ✅ PAID (5 days ago)\n"
        "👤 **User @sarah_7** - $9.00 - ✅ PAID (2 days ago)\n"
        "👤 **User @alex_99** - $5.50 - ✅ PAID (4 days ago)\n\n"
        "💳 All payments via Payeer.\n"
        "⏳ Your turn is coming!\n"
        "📌 Create more accounts to withdraw faster!"
    )

@bot_client.on(events.NewMessage(pattern='/help'))
async def help_cmd(event):
    await event.respond(
        "📌 **Gmail Farm Pro - Help**\n\n"
        "💰 **Earn $0.50 per Gmail account**\n"
        "✅ **Max 5 pending tasks**\n"
        "⏱️ **Verification:** 2-5 minutes\n"
        "❌ **Cancel tasks anytime**\n"
        "💳 **Min Withdrawal:** $5.00 (10 accounts!)\n"
        "⏳ **Hold Period:** 24 hours\n\n"
        "📌 **Commands:**\n"
        "➕ `/task` - New account\n"
        "✅ `/confirm` - Submit for verification\n"
        "📋 `/tasks` - View your tasks\n"
        "❌ `/cancel` - Cancel pending task\n"
        "💰 `/balance` - Check earnings\n"
        "💳 `/withdraw` - Request payout\n"
        "📜 `/history` - Recent payments\n"
        "❓ `/help` - Show this menu\n\n"
        "💡 **Tip:** Create 10 accounts = $5.00 withdrawal!\n"
        "📌 The more you create, the more you earn!"
    )

# ========== INLINE BUTTONS ==========

@bot_client.on(events.CallbackQuery)
async def handle_callback(event):
    data = event.data.decode()
    
    if data == "new_task":
        await task_cmd(event)
    elif data == "my_tasks":
        await tasks_cmd(event)
    elif data == "my_balance":
        await balance_cmd(event)
    elif data == "cancel_task":
        await cancel_cmd(event)
    elif data == "withdraw":
        await withdraw_cmd(event)
    elif data == "help":
        await help_cmd(event)

# ========== START BOT ==========

async def main():
    print("🚀 Starting bot...")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"📁 Files: {os.listdir('.')}")
    
    await user_client.start()
    print("✅ User client connected!")
    
    await bot_client.start(bot_token=BOT_TOKEN)
    print("✅ Bot client connected!")
    
    print("🎯 Running. Listening to @GmailFProBot")
    print(f"👤 Admin ID: {ADMIN_ID}")
    print("📡 Command to generate tasks: '➕ New Account'")
    print(f"📊 Max pending tasks: {MAX_PENDING_TASKS}")
    print("💰 Reward: $0.50 per verified account")
    print("💳 Min Withdrawal: $5.00")
    
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
