from telethon import events
from telethon.utils import get_peer_id
from telethon.tl.types import PeerChannel, PeerChat
import json
import os
from typing import Any, Dict, List, Optional, Callable

# ---------------- فایل دیتا (فایل JSON به‌عنوان فallback) ----------------
def get_data_file(session_name: Optional[str]) -> Optional[str]:
    if not session_name:
        return None
    return f"data_{session_name}.json"


def load_state(session_name: Optional[str]) -> Dict[str, Any]:
    file = get_data_file(session_name)
    if file and os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"owner_id": None, "auto_groups": [], "copy_groups": []}


def save_state(session_name: Optional[str], state: Dict[str, Any]) -> None:
    file = get_data_file(session_name)
    if not file:
        return
    with open(file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ---------------- ابزار تبدیل ورودی به chat_id ----------------
async def _resolve_chat_id(client, event, arg: Optional[str]) -> Optional[int]:
    """
    ورودی می‌تواند:
      - خالی (یعنی همین گروه جاری)
      - t.me/<username> یا t.me/c/<id>
      - @username
      - آیدی عددی (مثبت/منفی) باشد
    """
    if not arg or not str(arg).strip():
        return event.chat_id

    text = str(arg).strip()

    # t.me links
    if "t.me/" in text:
        text = text.split("t.me/", 1)[1].strip().strip("/")
        if text.lower().startswith("c/"):
            parts = text.split("/")
            if len(parts) >= 2 and parts[1].isdigit():
                text = "-100" + parts[1]

    # username
    if text.startswith("@") or any(c.isalpha() for c in text):
        try:
            entity = await client.get_entity(text)
            return get_peer_id(entity)
        except Exception:
            await event.edit("❌ گروه با این یوزرنیم پیدا نشد.")
            return None

    # numeric
    try:
        val = int(text)
    except ValueError:
        await event.edit("❌ ورودی نامعتبر. از @username یا آیدی عددی (-100...) استفاده کن.")
        return None

    # اگر منفی/قدیمی بود
    if val <= 0:
        # تلاش برای پیدا کردن در دیالوگ‌ها
        async for d in client.iter_dialogs():
            if get_peer_id(d.entity) == val:
                return val
        abs_id = int(str(val)[4:]) if str(val).startswith("-100") else abs(val)
        try:
            entity = await client.get_entity(PeerChannel(abs_id))
            return get_peer_id(entity)
        except Exception:
            try:
                entity = await client.get_entity(PeerChat(abs_id))
                return get_peer_id(entity)
            except Exception:
                await event.edit("❌ گروه با این آیدی پیدا نشد. مطمئن شو عضو اون گروهی.")
                return None

    # اگر مثبت بود
    async for d in client.iter_dialogs():
        if getattr(d.entity, "id", None) == val:
            return get_peer_id(d.entity)

    try:
        entity = await client.get_entity(val)
        return get_peer_id(entity)
    except Exception:
        await event.edit("❌ چیزی با این ID پیدا نشد.")
        return None


# ---------------- توابع کمکی دیتابیس ----------------
def create_tables(conn) -> None:
    """
    جداول موردنیاز:
      - auto_groups(session_name TEXT, gid BIGINT)  PK(session_name, gid)
      - copy_groups(gid BIGINT)                    PK(gid)
    برای PostgreSQL:
      BIGINT استفاده شود و ON CONFLICT پشتیبانی می‌شود.
    """
    if not conn:
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS auto_groups (
                session_name TEXT NOT NULL,
                gid BIGINT NOT NULL,
                PRIMARY KEY (session_name, gid)
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS copy_groups (
                gid BIGINT PRIMARY KEY
            );
            """
        )
    conn.commit()


def db_insert_auto(conn, session_name: str, gid: int) -> None:
    if not (conn and session_name):
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO auto_groups (session_name, gid)
            VALUES (%s, %s)
            ON CONFLICT (session_name, gid) DO NOTHING;
            """,
            (session_name, gid),
        )
    conn.commit()


def db_insert_copy(conn, gid: int) -> None:
    if not conn:
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO copy_groups (gid)
            VALUES (%s)
            ON CONFLICT (gid) DO NOTHING;
            """,
            (gid,),
        )
    conn.commit()


def db_delete_auto(conn, session_name: Optional[str], gid: int) -> int:
    if not (conn and session_name):
        return 0
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM auto_groups WHERE session_name=%s AND gid=%s;",
            (session_name, gid),
        )
        deleted = cur.rowcount
    conn.commit()
    return deleted


def db_delete_copy(conn, gid: int) -> int:
    if not conn:
        return 0
    with conn.cursor() as cur:
        cur.execute("DELETE FROM copy_groups WHERE gid=%s;", (gid,))
        deleted = cur.rowcount
    conn.commit()
    return deleted


# ---------------- ثبت / حذف ----------------
def register_save_group(
    client,
    state: Dict[str, Any],
    GLOBAL_GROUPS: Optional[Dict[str, List[int]]],
    send_status: Callable[[], Any],
    conn: Optional[Any] = None,
    session_name: Optional[str] = None,
):
    """
    state نمونه:
      { "owner_id": 123, "auto_groups": [..], "copy_groups": [..] }
    GLOBAL_GROUPS: دیکشنری مشترک بین اکانت‌ها مثل {"copy_groups": [..]}
    conn: اتصال دیتابیس (مثلاً psycopg2)
    """
    # اطمینان از وجود کلیدها
    state.setdefault("auto_groups", [])
    state.setdefault("copy_groups", [])
    if isinstance(GLOBAL_GROUPS, dict):
        GLOBAL_GROUPS.setdefault("copy_groups", [])

    def is_owner(e) -> bool:
        return e.sender_id == state.get("owner_id")

    # --- ثبت فقط برای این اکانت (در همان گروه جاری) ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت$"))
    async def register_group_here(event):
        if not is_owner(event):
            return
        if not event.is_group:
            await event.edit("این دستور فقط داخل گروه کار می‌کند.")
            return

        gid = event.chat_id
        if gid not in state["auto_groups"]:
            state["auto_groups"].append(gid)
            save_state(session_name, state)
            db_insert_auto(conn, session_name or "", gid)

            await event.edit(f"✅ گروه {gid} در حالت سکوت قرار گرفت.")
            await send_status()
        else:
            await event.edit(f"ℹ️ گروه {gid} از قبل ثبت شده بود.")

    # --- ثبت با یوزرنیم یا آیدی برای این اکانت ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت یوزر(?:\s+(.+))$"))
    async def register_group_by_username(event):
        if not is_owner(event):
            return

        arg = event.pattern_match.group(1)
        gid = await _resolve_chat_id(client, event, arg)
        if gid is None:
            return

        if gid not in state["auto_groups"]:
            state["auto_groups"].append(gid)
            save_state(session_name, state)
            db_insert_auto(conn, session_name or "", gid)

            await event.edit(f"✅ گروه {gid} در حالت سکوت قرار گرفت (ثبت با یوزر/آیدی).")
            await send_status()
        else:
            await event.edit(f"ℹ️ گروه {gid} از قبل ثبت شده بود.")

    # --- ثبت کپی برای همه اکانت‌ها (گروه جاری) ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت کپی$"))
    async def register_copy_group(event):
        if not is_owner(event):
            return
        if not event.is_group:
            await event.edit("این دستور را داخل گروه بزن جقی.")
            return

        gid = event.chat_id

        changed = False
        # در state محلی
        if gid not in state["copy_groups"]:
            state["copy_groups"].append(gid)
            changed = True

        # در GLOBAL_GROUPS مشترک
        if isinstance(GLOBAL_GROUPS, dict):
            if gid not in GLOBAL_GROUPS["copy_groups"]:
                GLOBAL_GROUPS["copy_groups"].append(gid)
                changed = True

        if changed:
            save_state(session_name, state)
            db_insert_copy(conn, gid)
            await event.edit(f"✅ گروه {gid} برای کپی روی همه اکانت‌ها ثبت شد.")
            await send_status()
        else:
            await event.edit(f"ℹ️ گروه {gid} از قبل در لیست کپی بود.")

    # --- حذف گروه (از سکوت/کپی)؛ ورودی اختیاری یوزرنیم/آیدی ---
    @client.on(events.NewMessage(pattern=r"^\.حذف(?:\s+(.+))?$"))
    async def unregister_group(event):
        if not is_owner(event):
            return

        arg = event.pattern_match.group(1)
        gid = await _resolve_chat_id(client, event, arg)
        if gid is None:
            return

        removed = False
        if gid in state["auto_groups"]:
            state["auto_groups"].remove(gid)
            db_delete_auto(conn, session_name, gid)
            removed = True

        if gid in state["copy_groups"]:
            state["copy_groups"].remove(gid)
            removed = True

        if isinstance(GLOBAL_GROUPS, dict) and gid in GLOBAL_GROUPS["copy_groups"]:
            GLOBAL_GROUPS["copy_groups"].remove(gid)
            removed = True

        # از دیتابیس copy_groups نیز حذف شود (در صورت تمایل می‌توان شرط گذاشت)
        if removed:
            db_delete_copy(conn, gid)
            save_state(session_name, state)
            await event.edit(f"❎ گروه {gid} از حالت سکوت/کپی خارج شد.")
            await send_status()
        else:
            await event.edit(f"ℹ️ گروه {gid} اصلاً ثبت نشده بود.")