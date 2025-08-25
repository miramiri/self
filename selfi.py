# -*- coding: utf-8 -*-
import asyncio
import json
import os
from telethon import TelegramClient, events, Button
from flask import Flask
from threading import Thread
import psycopg2
from psycopg2.extras import Json

# --- ماژول‌ها ---
from autocatch import register_autocatch
from selfi2 import register_extra_cmds   # دستورات جدا (لیست/آیدی/بلاک/تاریخ/تنظیم)
from games import register_games
from menu import register_menu
from sargarmi_plus import register_sargarmi_plus
from security import register_security
from help1 import register_help1
from sargarmi import register_sargarmi
from sell import register_sell
from save_group import register_save_group   # ← وصله‌ی دیتابیسی ثبت/حذف گروه
from selfi3 import register_selfi3_cmds

# --- اتصال به دیتابیس PostgreSQL ---
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PUBLIC_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL/DATABASE_PUBLIC_URL is not set")

try:
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor()

    # --- ساخت جدول‌ها (در صورت نبودن) ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS auto_groups (
        id SERIAL PRIMARY KEY,
        session_name TEXT NOT NULL,
        gid BIGINT NOT NULL,
        UNIQUE(session_name, gid)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS copy_groups (
        id SERIAL PRIMARY KEY,
        session_name TEXT NOT NULL,
        gid BIGINT NOT NULL,
        UNIQUE(session_name, gid)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id SERIAL PRIMARY KEY,
        chat_id BIGINT UNIQUE NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_name TEXT PRIMARY KEY,
        state JSONB
    );
    """)

    conn.commit()
    print("✅ دیتابیس آماده است.")
except Exception as e:
    print("❌ خطا در اتصال/تهیه‌ی دیتابیس:", e)
    raise

# --- سرور keep_alive برای ریپلیت/ریل‌وی ---
app = Flask('')

@app.route('/')
def home():
    return "نيما نوب سگ!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- خواندن API_ID و API_HASH ---
with open("confing.json", "r", encoding="utf-8") as f:
    config = json.load(f)
API_ID = int(config["api_id"])
API_HASH = config["api_hash"]

SESSIONS = [
    "acc", "acc1", "acc2", "acc3", "acc4",
    "acc5", "acc7"
]

# --- گروه‌های عمومی (جدول groups) ---
def load_groups():
    cur.execute("SELECT chat_id FROM groups;")
    return [row[0] for row in cur.fetchall()]

def save_group_db(chat_id):
    cur.execute("INSERT INTO groups (chat_id) VALUES (%s) ON CONFLICT DO NOTHING;", (chat_id,))
    conn.commit()

GLOBAL_GROUPS = load_groups()

# --- state پیش‌فرض ---
def default_state():
    return {
        "owner_id": None,
        "echo_users": [],
        "enabled": True,
        "delay": 2.0,
        "stop_emoji": ["⚜", "💮", "⚡", "❓"],
        "last_user": None,
        "last_group": None,
        "funny_text": "نیما فشاری 😂",
        "status_msg_id": None,
        "auto_groups": [],
        "copy_plus_user": None,
        "copy_groups": []
    }

def load_state(session_name):
    cur.execute("SELECT state FROM sessions WHERE session_name=%s;", (session_name,))
    row = cur.fetchone()
    return row[0] if row else default_state()

def db_get_auto_groups(session_name):
    cur.execute("SELECT gid FROM auto_groups WHERE session_name=%s;", (session_name,))
    return [r[0] for r in cur.fetchall()]

def db_get_copy_groups_for_all():
    # همه‌ی گروه‌های کپی در همه‌ی سشن‌ها (الگوی نسخه ۱)
    cur.execute("SELECT gid FROM copy_groups;")
    return [r[0] for r in cur.fetchall()]

def db_get_copy_groups_for_session(session_name):
    cur.execute("SELECT gid FROM copy_groups WHERE session_name=%s;", (session_name,))
    return [r[0] for r in cur.fetchall()]

async def setup_client(session_name):
    state = load_state(session_name)

    # همگام‌سازی مقداردهی اولیه از دیتابیس
    try:
        state["auto_groups"] = db_get_auto_groups(session_name)
        state["copy_groups"] = db_get_copy_groups_for_session(session_name)
    except Exception as e:
        print(f"⚠️ [{session_name}] خطا در sync اولیه‌ی گروه‌ها:", e)

    def save_state():
        cur.execute("""
        INSERT INTO sessions (session_name, state)
        VALUES (%s, %s)
        ON CONFLICT (session_name) DO UPDATE SET state = EXCLUDED.state;
        """, (session_name, Json(state)))
        conn.commit()

    client = TelegramClient(session_name, API_ID, API_HASH)
    await client.start()

    me = await client.get_me()
    if not state["owner_id"]:
        state["owner_id"] = me.id
        save_state()
        print(f"✅ [{session_name}] Owner set: {me.id}")
    else:
        print(f"✅ [{session_name}] Started")

    def is_owner(e):
        return e.sender_id == state["owner_id"]

    # ---------- متن وضعیت
    def _status_text():
        return (
            f"🤖 وضعیت ربات {session_name}\n"
            f"═════════════════════════\n"
            f"🔹 وضعیت:\n"
            f"   ✅ فعال: {'بله' if state['enabled'] else 'خیر'}\n"
            f"   ⏳ تاخیر: {state['delay']} ثانیه\n"
            f"   🔄 کاربران کپی: {len(state['echo_users'])}\n"
            f"   ⛔ ایموجی قطع‌کننده: {', '.join(state['stop_emoji']) if state['stop_emoji'] else 'هیچ'}\n"
            f"   🟢 گروه‌های اتوکچ (این اکانت): {len(state['auto_groups'])}\n"
            f"   🟣 گروه‌های کپی (عمومی): {len(GLOBAL_GROUPS)}\n"
            f"\n"
            f"📖 دستورات موجود:\n"
            f"   👤 مدیریت کاربران:\n"
            f"      • .کپی (ریپلای)\n"
            f"      • .کپی خاموش (ریپلای)\n"
            f"      • .کپی پلاس (ریپلای)\n"
            f"      • .لیست\n"
            f"   ⚙️ مدیریت ربات:\n"
            f"      • .ریست دیتا\n"
            f"      • .عدد (مثل .0.5)\n"
            f"      • .تنظیم [متن]\n"
            f"      • .ست 😀 💮 ⚡️\n"
            f"      • .ست حذف همه\n"
            f"   🛡 مدیریت گروه/کاربر:\n"
            f"      • .ثبت / .حذف\n"
            f"      • .ثبت کپی\n"
            f"      • .بلاک (ریپلای یا آیدی)\n"
            f"      • .آیدی (ریپلای)\n"
            f"   📅 ابزارها:\n"
            f"      • .تاریخ\n"
        )

    # ---------- تابع ارسال وضعیت ----------
    async def send_status():
        try:
            text = _status_text()
            if state.get("status_msg_id") and state.get("last_group"):
                # ویرایش پیام قبلی
                await client.edit_message(state["last_group"], state["status_msg_id"], text)
            elif state.get("last_group"):
                # ارسال پیام جدید
                msg = await client.send_message(state["last_group"], text)
                state["status_msg_id"] = msg.id
                save_state()
        except Exception as e:
            print(f"⚠️ [{session_name}] خطا در send_status: {e}")

    # ---------- ماژول‌ها ----------
    register_autocatch(client, state, GLOBAL_GROUPS, save_state, send_status)
    register_games(client, state, GLOBAL_GROUPS, save_state, send_status)
    register_menu(client, state, GLOBAL_GROUPS, save_state, send_status)
    register_sargarmi_plus(client, state, GLOBAL_GROUPS, save_state, send_status)
    register_security(client, state, GLOBAL_GROUPS, save_state, send_status)
    register_help1(client, state, GLOBAL_GROUPS, save_state, send_status)
    register_sargarmi(client, state, GLOBAL_GROUPS, save_state, send_status)
    register_sell(client)
    register_save_group(client, state, GLOBAL_GROUPS, save_state, send_status, session_name)
    register_extra_cmds(client, state, GLOBAL_GROUPS, save_state, send_status, conn, session_name)
    register_selfi3_cmds(client, state, GLOBAL_GROUPS, save_state, send_status, session_name)

    return client

async def main():
    clients = await asyncio.gather(*[setup_client(s) for s in SESSIONS])
    print(f"🚀 {len(clients)} کلاینت ران شد.")
    await asyncio.gather(*[asyncio.create_task(c.run_until_disconnected()) for c in clients])


if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
