from telethon import events
from telethon.utils import get_peer_id
from telethon.tl.types import PeerChannel, PeerChat

# --- تبدیل ورودی به chat_id ---
async def _resolve_chat_id(client, event, arg: str):
    if not arg or not str(arg).strip():
        return event.chat_id
    text = str(arg).strip()
    if "t.me/" in text:
        text = text.split("t.me/", 1)[1].strip().strip("/")
        if text.lower().startswith("c/"):
            parts = text.split("/")
            if len(parts) >= 2 and parts[1].isdigit():
                text = "-100" + parts[1]
    if text.startswith("@") or any(c.isalpha() for c in text):
        entity = await client.get_entity(text)
        return get_peer_id(entity)
    return int(text)

# --- دستورات اصلی ---
def register_save_group(client, state, save_state, send_status, conn, session_name):
    def is_owner(e): return e.sender_id == state.get("owner_id")

    # .ثبت
    @client.on(events.NewMessage(pattern=r"^\.ثبت$"))
    async def register_group(event):
        if not is_owner(event) or not event.is_group: return
        gid = event.chat_id
        with conn.cursor() as cur:
            cur.execute("INSERT INTO auto_groups (session_name, gid) VALUES (%s,%s) ON CONFLICT DO NOTHING;", (session_name, gid))
        await event.edit("گروه ثبت شد.")
        await send_status()

    # .ثبت یوزر
    @client.on(events.NewMessage(pattern=r"^\.ثبت یوزر(?:\s+(.+))$"))
    async def register_group_user(event):
        if not is_owner(event): return
        gid = await _resolve_chat_id(client, event, event.pattern_match.group(1))
        if not gid: return
        with conn.cursor() as cur:
            cur.execute("INSERT INTO auto_groups (session_name, gid) VALUES (%s,%s) ON CONFLICT DO NOTHING;", (session_name, gid))
        await event.edit("گروه ثبت شد (یوزر).")
        await send_status()

    # .ثبت کپی
    @client.on(events.NewMessage(pattern=r"^\.ثبت کپی$"))
    async def register_copy(event):
        if not is_owner(event) or not event.is_group: return
        gid = event.chat_id
        with conn.cursor() as cur:
            cur.execute("INSERT INTO copy_groups (session_name, gid) VALUES (%s,%s) ON CONFLICT DO NOTHING;", (session_name, gid))
        await event.edit("گروه ثبت شد (کپی).")
        await send_status()

    # .حذف
    @client.on(events.NewMessage(pattern=r"^\.حذف$"))
    async def unregister(event):
        if not is_owner(event) or not event.is_group: return
        gid = event.chat_id
        removed = False
        with conn.cursor() as cur:
            cur.execute("DELETE FROM auto_groups WHERE session_name=%s AND gid=%s;", (session_name, gid))
            if cur.rowcount: removed = True
            cur.execute("DELETE FROM copy_groups WHERE session_name=%s AND gid=%s;", (session_name, gid))
            if cur.rowcount: removed = True
        await event.edit("حذف شد." if removed else "یافت نشد.")
        await send_status()
