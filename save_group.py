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
register_group_manager(client, state, GLOBAL_GROUPS, save_state, send_status)
    state = load_state(session_name)

    def is_owner(e):
        return e.sender_id == state.get("owner_id")

    # --- ثبت فقط برای این اکانت ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت$"))
    async def register_group(event):
        if not is_owner(event): return
        if not event.is_group:
            await event.edit("❌ فقط در گروه کار می‌کند.")
            return
        
        gid = event.chat_id
        if gid not in state["auto_groups"]:
            state["auto_groups"].append(gid)
            save_state(session_name, state)
            await event.edit("✅ گروه فقط برای این اکانت ثبت شد.")
        else:
            await event.edit("ℹ️ این گروه قبلاً ثبت شده بود.")

    # --- ثبت کپی برای همه اکانت‌ها ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت کپی$"))
    async def register_copy_group(event):
        if not is_owner(event): return
        if not event.is_group:
            await event.edit("میگم کصخلی میگی نه😂")
            return
        
        gid = event.chat_id
        updated = False
        for sname, cstate in all_sessions.items():
            if gid not in cstate["copy_groups"]:
                cstate["copy_groups"].append(gid)
                save_state(sname, cstate)
                updated = True

        if updated:
            await event.edit("بریم رو کار حملهههههه")
        else:
            await event.edit("")

    # --- حذف گروه ---
    @client.on(events.NewMessage(pattern=r"^\.حذف$"))
    async def unregister_group(event):
        if not is_owner(event): return
        if not event.is_group:
            await event.edit("❌ فقط در گروه کار می‌کند.")
            return
        
        gid = event.chat_id
        removed = False
        if gid in state["auto_groups"]:
            state["auto_groups"].remove(gid)
            removed = True
        if gid in state["copy_groups"]:
            state["copy_groups"].remove(gid)
            removed = True
        if removed:
            save_state(session_name, state)
            await event.edit("⛔ گروه حذف شد.")
        else:
            await event.edit("ℹ️ این گروه قبلاً ثبت نشده بود.")