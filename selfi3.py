# -*- coding: utf-8 -*-
from telethon import events, Button
import asyncio
import os, psycopg2

# -------------------- اتصال دیتابیس (Per-Session) --------------------
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PUBLIC_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL/DATABASE_PUBLIC_URL is not set")

conn = psycopg2.connect(DATABASE_URL, sslmode="require")

with conn, conn.cursor() as c:
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS echo_users (
            session_name TEXT NOT NULL,
            uid BIGINT NOT NULL,
            PRIMARY KEY (session_name, uid)
        );
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS copy_plus (
            session_name TEXT PRIMARY KEY,
            uid BIGINT
        );
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS stop_emoji (
            session_name TEXT NOT NULL,
            emoji TEXT NOT NULL,
            PRIMARY KEY (session_name, emoji)
        );
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            session_name TEXT PRIMARY KEY,
            delay DOUBLE PRECISION DEFAULT 2.0
        );
        """
    )

# ---- توابع دیتابیس ----

def db_echo_users_get(session_name):
    with conn.cursor() as c:
        c.execute("SELECT uid FROM echo_users WHERE session_name=%s;", (session_name,))
        return [r[0] for r in c.fetchall()]

def db_echo_users_add(session_name, uid):
    with conn.cursor() as c:
        c.execute(
            "INSERT INTO echo_users(session_name, uid) VALUES(%s,%s) ON CONFLICT DO NOTHING;",
            (session_name, uid),
        )
    conn.commit()

def db_echo_users_del(session_name, uid):
    with conn.cursor() as c:
        c.execute("DELETE FROM echo_users WHERE session_name=%s AND uid=%s;", (session_name, uid))
    conn.commit()

def db_copy_plus_get(session_name):
    with conn.cursor() as c:
        c.execute("SELECT uid FROM copy_plus WHERE session_name=%s;", (session_name,))
        row = c.fetchone()
        return row[0] if row else None

def db_copy_plus_set(session_name, uid):
    with conn.cursor() as c:
        c.execute(
            "INSERT INTO copy_plus(session_name, uid) VALUES(%s,%s) ON CONFLICT (session_name) DO UPDATE SET uid=EXCLUDED.uid;",
            (session_name, uid),
        )
    conn.commit()

def db_copy_plus_clear(session_name):
    with conn.cursor() as c:
        c.execute("DELETE FROM copy_plus WHERE session_name=%s;", (session_name,))
    conn.commit()

def db_stop_emoji_get(session_name):
    with conn.cursor() as c:
        c.execute("SELECT emoji FROM stop_emoji WHERE session_name=%s;", (session_name,))
        return [r[0] for r in c.fetchall()]

def db_stop_emoji_set_all(session_name, emojis):
    with conn.cursor() as c:
        c.execute("DELETE FROM stop_emoji WHERE session_name=%s;", (session_name,))
        for e in emojis[:10]:
            c.execute(
                "INSERT INTO stop_emoji(session_name, emoji) VALUES(%s,%s) ON CONFLICT DO NOTHING;",
                (session_name, e),
            )
    conn.commit()

def db_stop_emoji_clear(session_name):
    with conn.cursor() as c:
        c.execute("DELETE FROM stop_emoji WHERE session_name=%s;", (session_name,))
    conn.commit()

def db_delay_get(session_name, default=2.0):
    with conn.cursor() as c:
        c.execute("SELECT delay FROM settings WHERE session_name=%s;", (session_name,))
        row = c.fetchone()
        return float(row[0]) if row and row[0] is not None else float(default)

def db_delay_set(session_name, delay):
    with conn.cursor() as c:
        c.execute(
            "INSERT INTO settings(session_name, delay) VALUES(%s,%s) ON CONFLICT (session_name) DO UPDATE SET delay=EXCLUDED.delay;",
            (session_name, delay),
        )
    conn.commit()

def db_reset_session(session_name):
    with conn.cursor() as c:
        c.execute("DELETE FROM echo_users WHERE session_name=%s;", (session_name,))
        c.execute("DELETE FROM copy_plus WHERE session_name=%s;", (session_name,))
        c.execute("DELETE FROM stop_emoji WHERE session_name=%s;", (session_name,))
        c.execute("DELETE FROM settings WHERE session_name=%s;", (session_name,))
    conn.commit()


# -------------------- ثبت دستورات سلفی۳ (با دیتابیس) --------------------
def register_selfi3_cmds(client, state, GLOBAL_GROUPS, save_state, send_status, session_name):
    # ---------- کپی ----------
    @client.on(events.NewMessage(pattern=r".کپی$"))
    async def enable_copy(event):
        if event.sender_id != state["owner_id"]: return
        if not event.is_reply:
            await event.edit("❌ روی پیام ریپلای کن!")
            return
        reply = await event.get_reply_message()
        user = await reply.get_sender()
        # DB add
        db_echo_users_add(session_name, user.id)
        # Sync state (اختیاری برای نمایش وضعیت)
        eu = set(state.get("echo_users", []))
        eu.add(user.id)
        state["echo_users"] = list(eu)
        state["last_user"] = user.id
        state["last_group"] = event.chat_id
        save_state()
        await event.edit(f"✅ کپی برای {user.first_name} فعال شد.")
        await send_status()

    # ---------- کپی خاموش ----------
    @client.on(events.NewMessage(pattern=r".کپی خاموش$"))
    async def disable_copy(event):
        if event.sender_id != state["owner_id"]: return
        if not event.is_reply:
            await event.edit("❌ روی پیام ریپلای کن!")
            return
        reply = await event.get_reply_message()
        user = await reply.get_sender()
        # DB remove
        db_echo_users_del(session_name, user.id)
        # Sync state
        eu = set(state.get("echo_users", []))
        if user.id in eu:
            eu.remove(user.id)
        state["echo_users"] = list(eu)
        save_state()
        await event.edit(f"⛔ کپی برای {user.first_name} خاموش شد.")
        await send_status()

    # ---------- کپی پلاس ----------
    @client.on(events.NewMessage(pattern=r"^\.کپی پلاس$"))
    async def copy_plus(event):
        if event.sender_id != state["owner_id"]: return
        if not event.is_reply:
            await event.edit("❌ روی پیام ریپلای کن!")
            return
        reply = await event.get_reply_message()
        user = await reply.get_sender()
        # DB upsert
        db_copy_plus_set(session_name, user.id)
        state["copy_plus_user"] = user.id  # اختیاری برای وضعیت
        save_state()
        await event.edit(
            f"✨ کپی پلاس فعال شد برای {getattr(user, 'first_name', 'کاربر')}\n"
            f"هر وقت اتوکچ قطع شد، دوباره براش فعال میشه.",
            buttons=[[Button.inline("❌ حذف کپی پلاس", b"del_copy_plus")]]
        )
        await send_status()

    @client.on(events.CallbackQuery(pattern=b"del_copy_plus"))
    async def del_copy_plus(event):
        if event.sender_id != state["owner_id"]: return
        # DB clear
        db_copy_plus_clear(session_name)
        state["copy_plus_user"] = None
        save_state()
        await event.edit("❌ کپی پلاس حذف شد.")
        await send_status()

    # ---------- ریست دیتا ----------
    @client.on(events.NewMessage(pattern=r"^\.ریست دیتا$"))
    async def reset_data(event):
        if event.sender_id != state["owner_id"]: return
        # پاک کردن دیتابیس برای این سشن
        db_reset_session(session_name)
        # بازگردانی state پیش‌فرض (متن‌ها دست‌نخورده)
        status_msg_id_keep = state.get("status_msg_id")
        state.clear()
        state.update({
            "owner_id": event.sender_id,
            "echo_users": [],
            "enabled": True,
            "delay": 2.0,
            "stop_emoji": ["⚜", "💮", "⚡", "❓"],
            "last_user": None,
            "last_group": None,
            "funny_text": "مگه نیما فشاری 😂",
            "status_msg_id": status_msg_id_keep,
            "auto_groups": [],
            "copy_plus_user": None,
            "copy_groups": []
        })
        save_state()
        await event.reply("♻️ فایل دیتا ریست شد.")
        await send_status()

    # ---------- دستور .ست ----------
    @client.on(events.NewMessage(pattern=r"^\.ست حذف همه$"))
    async def clear_stop_emoji(event):
        if event.sender_id != state["owner_id"]: return
        db_stop_emoji_clear(session_name)
        state["stop_emoji"] = []
        save_state()
        await event.edit("🧹 ایموجی‌های قطع‌کننده حذف شد.")
        await send_status()

    @client.on(events.NewMessage(pattern=r"^\.ست$"))
    async def show_stop_emoji(event):
        if event.sender_id != state["owner_id"]: return
        # از DB بخون
        emojis = db_stop_emoji_get(session_name)
        if emojis:
            cur_emojis = ", ".join(emojis)
        else:
            cur_emojis = "هیچ"
        state["stop_emoji"] = emojis  # sync
        await event.edit(f"⛔ ایموجی‌های فعلی: {cur_emojis}\n"
                          f"برای تنظیم چندتا باهم: `.ست 😀 💮 ⚡️`")

    @client.on(events.NewMessage(pattern=r"^\.ست (.+)$"))
    async def set_stop_emoji(event):
        if event.sender_id != state["owner_id"]: return
        args = event.pattern_match.group(1).strip()
        tokens = [tok for tok in args.split() if tok]
        seen, emojis = set(), []
        for t in tokens:
            if t not in seen:
                seen.add(t)
                emojis.append(t)
        if len(emojis) > 10:
            emojis = emojis[:10]
        # ذخیره DB و sync state
        db_stop_emoji_set_all(session_name, emojis)
        state["stop_emoji"] = emojis
        save_state()
        cur_emojis = ", ".join(emojis) if emojis else "هیچ"
        await event.edit(f"✅ ایموجی‌های قطع‌کننده تنظیم شد: {cur_emojis}")
        await send_status()

    # ---------- دستور تاخیر ----------
    @client.on(events.NewMessage(pattern=r"^\.(\d+(?:\.\d+)?)$"))
    async def set_delay(event):
        if event.sender_id != state["owner_id"]: return
        try:
            delay = float(event.pattern_match.group(1))
        except ValueError:
            await event.edit("❌ عدد درست وارد کن.")
            return
        delay = max(0.0, delay)
        # ذخیره DB و sync state
        db_delay_set(session_name, delay)
        state["delay"] = delay
        save_state()
        if delay == 0:
            await event.edit("⏱️ تاخیر روی 0 تنظیم شد.")
        else:
            await event.edit(f"⏱️ تاخیر روی {delay} ثانیه تنظیم شد.")
        await send_status()

    # ---------- موتور کپی گروه ----------
    @client.on(events.NewMessage)
    async def copy_groups_handler(event):
        if not state.get("enabled", True):
            return
        if event.chat_id not in state.get("copy_groups", []):
            return
        # از DB لیست کاربرا و تاخیر بگیر
        echo_users = db_echo_users_get(session_name)
        if event.sender_id not in echo_users:
            return
        delay = db_delay_get(session_name, state.get("delay", 2.0))
        await asyncio.sleep(delay)
        try:
            if event.media:
                await client.send_file(event.chat_id, event.media, caption=event.text)
            else:
                await client.send_message(event.chat_id, event.text)
        except Exception as e:
            print(f"❌ خطا در کپی پیام در {event.chat_id}: {e}")