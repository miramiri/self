from telethon import events
from telethon.utils import get_peer_id
from telethon.tl.types import PeerChannel, PeerChat
import json
import os
from typing import Any, Dict, List, Optional, Callable


# ---------------- فایل دیتا ----------------
def get_data_file(session_name: str) -> str:
    return f"data_{session_name}.json"


def load_state(session_name: str) -> Dict[str, Any]:
    file = get_data_file(session_name)
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"owner_id": None, "auto_groups": [], "copy_groups": []}


def save_state(session_name: str, state: Dict[str, Any]) -> None:
    file = get_data_file(session_name)
    with open(file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ---------------- ابزار تبدیل ورودی به chat_id ----------------
async def _resolve_chat_id(client, event, arg: Optional[str]) -> Optional[int]:
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
        try:
            entity = await client.get_entity(text)
            return get_peer_id(entity)
        except Exception:
            await event.edit("❌ گروه با این یوزرنیم پیدا نشد.")
            return None

    try:
        val = int(text)
    except ValueError:
        await event.edit("❌ ورودی نامعتبر. از @username یا آیدی عددی (-100...) استفاده کن.")
        return None

    if val <= 0:
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

    async for d in client.iter_dialogs():
        if getattr(d.entity, "id", None) == val:
            return get_peer_id(d.entity)

    try:
        entity = await client.get_entity(val)
        return get_peer_id(entity)
    except Exception:
        await event.edit("❌ چیزی با این ID پیدا نشد.")
        return None


# ---------------- ثبت / حذف ----------------
def register_save_group(
    client,
    state: Dict[str, Any],
    GLOBAL_GROUPS: Optional[Dict[str, List[int]]],
    send_status: Callable[[], Any],
    conn: Optional[Any] = None,
    session_name: Optional[str] = None,
):
    def is_owner(e) -> bool:
        return e.sender_id == state.get("owner_id")

    # --- ثبت فقط برای این اکانت (فقط داخل گروه) ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت$"))
    async def register_group_here(event):
        if not is_owner(event):
            return
        if not event.is_group:
            await event.edit("❌ فقط داخل گروه میشه این دستور رو زد.")
            return

        gid = event.chat_id
        if gid not in state["auto_groups"]:
            state["auto_groups"].append(gid)
            save_state(session_name, state)  # type: ignore[arg-type]

            if conn and session_name:
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

            await event.edit(f"✅ گروه {gid} در حالت سکوت قرار گرفت.")
            await send_status()
        else:
            await event.edit(f"گروه {gid} از قبل ساکته😴.")

    # --- ثبت با یوزرنیم یا آیدی ---
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
            save_state(session_name, state)  # type: ignore[arg-type]

            if conn and session_name:
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

            await event.edit(f"✅ گروه {gid} در حالت سکوت قرار گرفت (ثبت با یوزر).")
            await send_status()
        else:
            await event.edit(f"گروه {gid} از قبل ساکته😴.")

    # --- ثبت کپی برای همه اکانت‌ها ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت کپی(?:\s+(.+))?$"))
    async def register_copy_group(event):
        if not is_owner(event):
            return

        arg = event.pattern_match.group(1)
        gid = await _resolve_chat_id(client, event, arg)
        if gid is None:
            return

        if gid not in state["copy_groups"]:
            state["copy_groups"].append(gid)
            save_state(session_name, state)  # type: ignore[arg-type]

            if conn and session_name:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO copy_groups (session_name, gid)
                        VALUES (%s, %s)
                        ON CONFLICT (session_name, gid) DO NOTHING;
                        """,
                        (session_name, gid),
                    )
                conn.commit()

            if GLOBAL_GROUPS is not None:
                GLOBAL_GROUPS.setdefault("copy_groups", [])
                if gid not in GLOBAL_GROUPS["copy_groups"]:
                    GLOBAL_GROUPS["copy_groups"].append(gid)

            await event.edit(f"✅ گروه {gid} برای کپی روی همه اکانت‌ها ثبت شد.")
            await send_status()
        else:
            await event.edit(f"این گروه {gid} از قبل برای کپی ثبت شده بود ✅.")

    # --- حذف گروه ---
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
            removed = True
        if gid in state["copy_groups"]:
            state["copy_groups"].remove(gid)
            removed = True
        if GLOBAL_GROUPS and "copy_groups" in GLOBAL_GROUPS and gid in GLOBAL_GROUPS["copy_groups"]:
            GLOBAL_GROUPS["copy_groups"].remove(gid)
            removed = True

        if removed:
            save_state(session_name, state)  # type: ignore[arg-type]
            await event.edit(f"❎ گروه {gid} از حالت سکوت/کپی در اومد.")
            await send_status()
        else:
            await event.edit(f"گروه {gid} اصلاً ثبت نشده بود🤨.")