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

    # --- ثبت فقط برای این اکانت ---
    @client.on(events.NewMessage(pattern=r"^\.سبت$"))
    async def register_group(event):
        if not is_owner(event): return
        if not event.is_group:
            await event.edit("کص زن جقیت کنم فقط تو گروه کار می‌کنه🤦🏻‍♂️.")
            return

        gid = event.chat_id
        db_add_auto_group(session_name, gid)

        # sync
        state["auto_groups"] = db_get_auto_groups(session_name)
        save_state()

        await event.edit("گروه در حالت سکوت قرار گرفت 😴.")

    # --- ثبت کپی برای همه اکانت‌ها ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت کپی$"))
    async def register_copy_group(event):
        if not is_owner(event): return
        if not event.is_group:
            await event.edit("خو جقی برو تو گروه بزن🤦🏻‍♂️.")
            return

        gid = event.chat_id

        # همه session_name ها رو از دیتابیس بگیر
        with conn.cursor() as c:
            c.execute("""
                SELECT DISTINCT session_name FROM auto_groups
                UNION
                SELECT DISTINCT session_name FROM copy_groups;
            """)
            all_sessions = [r[0] for r in c.fetchall()]

        # اول چک کن آیا از قبل وجود داشته؟
        with conn.cursor() as c:
            c.execute("SELECT 1 FROM copy_groups WHERE gid=%s LIMIT 1;", (gid,))
            exists = c.fetchone()

        if exists:
            await event.edit("خو ی بار دست کردی تو شورت معلم بسه دیگه 🤦🏻‍♂️.")
            return

        # اگه نبود، برای همه سشن‌ها ثبت کن
        for s_name in all_sessions:
            db_add_copy_group(s_name, gid)

        # sync
        state["copy_groups"] = db_get_copy_groups(session_name)
        save_state()

        await event.edit("کی دست کرد تو شورت معلم❤️‍🔥🦦")
        await send_status()

    # --- حذف گروه ---
    @client.on(events.NewMessage(pattern=r"^\.حذف$"))
    async def unregister_group(event):
        if not is_owner(event): return
        if not event.is_group:
            await event.edit("تو پیوی نزن خو جقی🤦🏻‍♂️.")
            return

        gid = event.chat_id
        removed = False

        # حذف از دیتابیس
        with conn.cursor() as c:
            c.execute("DELETE FROM auto_groups WHERE session_name=%s AND gid=%s;", (session_name, gid))
            if c.rowcount > 0:
                removed = True
            c.execute("DELETE FROM copy_groups WHERE session_name=%s AND gid=%s;", (session_name, gid))
            if c.rowcount > 0:
                removed = True
        conn.commit()

        if removed:
            state["auto_groups"] = db_get_auto_groups(session_name)
            state["copy_groups"] = db_get_copy_groups(session_name)
            save_state()
            await event.edit("گروه از حالت سکوت در اومد 🦦.")
            await send_status()
        else:
            await event.edit("این گروه اصلا سکوت نیست🤨.")