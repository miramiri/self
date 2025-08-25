from telethon import events
import os, psycopg2

# --- اتصال به دیتابیس ---
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PUBLIC_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL/DATABASE_PUBLIC_URL is not set")

conn = psycopg2.connect(DATABASE_URL, sslmode="require")

# --- توابع دیتابیس ---
def db_get_auto_groups(session_name):
    with conn.cursor() as c:
        c.execute("SELECT gid FROM auto_groups WHERE session_name=%s;", (session_name,))
        return [r[0] for r in c.fetchall()]

def db_get_copy_groups(session_name):
    with conn.cursor() as c:
        c.execute("SELECT gid FROM copy_groups WHERE session_name=%s;", (session_name,))
        return [r[0] for r in c.fetchall()]

def db_add_auto_group(session_name, gid):
    with conn.cursor() as c:
        c.execute(
            "INSERT INTO auto_groups (session_name, gid) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
            (session_name, gid),
        )
    conn.commit()

def db_add_copy_group(session_name, gid):
    with conn.cursor() as c:
        c.execute(
            "INSERT INTO copy_groups (session_name, gid) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
            (session_name, gid),
        )
    conn.commit()

def db_remove_group(session_name, gid):
    with conn.cursor() as c:
        c.execute("DELETE FROM auto_groups WHERE session_name=%s AND gid=%s;", (session_name, gid))
        c.execute("DELETE FROM copy_groups WHERE session_name=%s AND gid=%s;", (session_name, gid))
    conn.commit()


# ---------------- ثبت / حذف ----------------
def register_save_group(client, state, groups, save_state, send_status, session_name):
    def is_owner(e):
        return e.sender_id == state.get("owner_id")

    # --- ثبت گروه برای اتوکچ ---
    @client.on(events.NewMessage(pattern=r"^\.سبت(?: (.+))?$"))
    async def register_group(event):
        if not is_owner(event): return

        arg = event.pattern_match.group(1)
        if arg:
            try:
                gid = int(arg)
            except ValueError:
                await event.edit("خو جقی آیدی درست بزن 🤦🏻‍♂️.")
                return
        else:
            if not event.is_group:
                await event.edit("کص زن جقیت کنم فقط تو گروه کار می‌کنه🤦🏻‍♂️.")
                return
            gid = event.chat_id

        db_add_auto_group(session_name, gid)
        state["auto_groups"] = db_get_auto_groups(session_name)
        save_state()
        await event.edit("گروه در حالت سکوت قرار گرفت 😴.")

    # --- ثبت گروه برای کپی ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت کپی(?: (.+))?$"))
    async def register_copy_group(event):
        if not is_owner(event): return

        arg = event.pattern_match.group(1)
        if arg:
            try:
                gid = int(arg)
            except ValueError:
                await event.edit("❌ آیدی درست وارد کن.")
                return
        else:
            if not event.is_group:
                await event.edit("❌ فقط داخل گروه می‌تونی بزنی.")
                return
            gid = event.chat_id

        db_add_copy_group(session_name, gid)
        state["copy_groups"] = db_get_copy_groups(session_name)
        save_state()
        await event.edit("✅ گروه به لیست کپی اضافه شد.")
        await send_status()

    # --- حذف گروه ---
    @client.on(events.NewMessage(pattern=r"^\.حذف(?: (.+))?$"))
    async def unregister_group(event):
        if not is_owner(event): return

        arg = event.pattern_match.group(1)
        if arg:
            try:
                gid = int(arg)
            except ValueError:
                await event.edit("خو جقی آیدی درست بزن 🤦🏻‍♂️.")
                return
        else:
            if not event.is_group:
                await event.edit("تو پیوی نزن خو جقی🤦🏻‍♂️.")
                return
            gid = event.chat_id

        db_remove_group(session_name, gid)
        state["auto_groups"] = db_get_auto_groups(session_name)
        state["copy_groups"] = db_get_copy_groups(session_name)
        save_state()
        await event.edit("گروه از حالت سکوت در اومد 🦦.")
        await send_status()

