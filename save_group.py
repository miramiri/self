from telethon import events
import os
import psycopg2
from psycopg2.extras import Json

# ---------------- اتصال به دیتابیس ----------------
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PUBLIC_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL/DATABASE_PUBLIC_URL is not set")

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS sessions (
    session_name TEXT PRIMARY KEY,
    state JSONB
);
""")
conn.commit()

# ---------------- مدیریت state ----------------
def default_state():
    return {"owner_id": None, "auto_groups": [], "copy_groups": []}

def load_state(session_name):
    cur.execute("SELECT state FROM sessions WHERE session_name=%s;", (session_name,))
    row = cur.fetchone()
    return row[0] if row else default_state()

def save_state(session_name, state):
    cur.execute("""
    INSERT INTO sessions (session_name, state)
    VALUES (%s, %s)
    ON CONFLICT (session_name) DO UPDATE SET state = EXCLUDED.state;
    """, (session_name, Json(state)))
    conn.commit()

# ---------------- ثبت / حذف ----------------
def register_save_group(client, state, groups, save_state, send_status):
    def is_owner(e):
        return e.sender_id == state.get("owner_id")

    # --- ثبت عادی فقط داخل گروه ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت$"))
    async def register_group_normal(event):
        if not is_owner(event): return
        if not event.is_group:
            await event.edit("❌ فقط داخل گروه میشه استفاده کرد.")
            return

        gid = event.chat_id
        if gid not in state["auto_groups"]:
            state["auto_groups"].append(gid)
            save_state()
            await event.edit(f"گروه {gid} ثبت شد 😴.")
        else:
            await event.edit("این گروه قبلاً ثبت شده 😴.")

    # --- ثبت با آیدی یا یوزرنیم ---
    @client.on(events.NewMessage(pattern=r"^\.سبت (.+)$"))
    async def register_group_with_id(event):
        if not is_owner(event): return

        arg = event.pattern_match.group(1)
        try:
            if arg.isdigit():
                gid = int(arg)
            else:
                entity = await client.get_entity(arg)
                gid = entity.id
        except Exception as e:
            await event.edit(f"❌ خطا در دریافت گروه/یوزر: {e}")
            return

        if gid not in state["auto_groups"]:
            state["auto_groups"].append(gid)
            save_state()
            await event.edit(f"گروه/چت {gid} ثبت شد 😴.")
        else:
            await event.edit("این گروه/چت قبلاً ثبت شده 😴.")

    # --- ثبت کپی برای همه اکانت‌ها ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت کپی$"))
    async def register_copy_group(event):
        if not is_owner(event): return
        if not event.is_group:
            await event.edit("خو جقی برو تو گروه بزن🤦🏻‍♂️.")
            return
        
        gid = event.chat_id
        if gid not in groups:
            groups.append(gid)
            save_state()
            await event.edit("کی دست کرد تو شورت معلم❤️‍🔥🦦")
            await send_status()
        else:
            await event.edit("خو ی بار دست کردی تو شورت معلم بسه دیگه چیو دقیقا میخوای؟🤦🏻‍♂️.")

    # --- حذف گروه ---
    @client.on(events.NewMessage(pattern=r"^\.حذف$"))
    async def unregister_group(event):
        if not is_owner(event): return
        if not event.is_group:
            await event.edit("تو پیوی نزن خو جقی🤦🏻‍♂️.")
            return
        
        gid = event.chat_id
        removed = False
        if gid in state["auto_groups"]:
            state["auto_groups"].remove(gid)
            removed = True
        if gid in groups:
            groups.remove(gid)
            removed = True
        if removed:
            save_state()
            await event.edit("گروه از حالت سکوت در اومد 🦦.")
            await send_status()
        else:
            await event.edit("این گروه اصلا سکوت نیست🤨.")