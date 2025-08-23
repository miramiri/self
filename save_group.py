from telethon import events
import json, os


# ---------------- فایل دیتا ----------------
def get_data_file(session_name):
    return f"data_{session_name}.json"


def load_state(session_name):
    file = get_data_file(session_name)
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"owner_id": None, "auto_groups": [], "copy_groups": []}


def save_state(session_name, state):
    file = get_data_file(session_name)
    with open(file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ---------------- ثبت / حذف ----------------
def register_save_group(client, state, GLOBAL_GROUPS, send_status, conn=None, session_name=None):
    def is_owner(e):
        return e.sender_id == state.get("owner_id")

    async def resolve_chat_id(arg, event):
        """تبدیل ورودی (عدد یا @username) به chat_id"""
        if not arg:
            return event.chat_id
        try:
            entity = await client.get_entity(arg)
            return entity.id
        except Exception:
            await event.respond("❌ گروه پیدا نشد.")
            return None

    # --- ثبت فقط برای این اکانت ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت(?:\s+(.+))?$"))
    async def register_group(event):
        if not is_owner(event):
            return

        arg = event.pattern_match.group(1)
        gid = await resolve_chat_id(arg, event)
        if gid is None:
            return

        if gid not in state["auto_groups"]:
            state["auto_groups"].append(gid)
            save_state(session_name, state)

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

            await event.respond(f"✅ گروه {gid} در حالت سکوت قرار گرفت.")
            await send_status()
        else:
            await event.respond(f"گروه {gid} از قبل ساکته😴.")

    # --- ثبت کپی برای همه اکانت‌ها ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت کپی(?:\s+(.+))?$"))
    async def register_copy_group(event):
        if not is_owner(event):
            return

        arg = event.pattern_match.group(1)
        gid = await resolve_chat_id(arg, event)
        if gid is None:
            return

        if gid not in state["copy_groups"]:
            state["copy_groups"].append(gid)
            save_state(session_name, state)

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

            await event.respond(f"✅ گروه {gid} برای کپی روی همه اکانت‌ها ثبت شد.")
            await send_status()
        else:
            await event.respond(f"گروه {gid} از قبل برای کپی ثبت شده بود ✅.")

    # --- حذف گروه ---
    @client.on(events.NewMessage(pattern=r"^\.حذف(?:\s+(.+))?$"))
    async def unregister_group(event):
        if not is_owner(event):
            return

        arg = event.pattern_match.group(1)
        gid = await resolve_chat_id(arg, event)
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
            save_state(session_name, state)
            await event.respond(f"❎ گروه {gid} از حالت سکوت/کپی در اومد.")
            await send_status()
        else:
            await event.respond(f"گروه {gid} اصلاً ثبت نشده بود🤨.")