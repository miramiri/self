from telethon import events

def register_security(client, state, GLOBAL_GROUPS, save_state, send_status):
    def is_owner(e): return e.sender_id == state["owner_id"]

    # 🚪 خروج همه
    @client.on(events.NewMessage(pattern=r"\.خروج همه$"))
    async def leave_all(event):
        if not is_owner(event): return
        await event.edit("🚪 همه کلاینت‌ها از اکانت خارج شدند (نمادین).")

    # 🔒 قفل
    @client.on(events.NewMessage(pattern=r"\.قفل (.+)$"))
    async def lock(event):
        if not is_owner(event): return
        part = event.pattern_match.group(1)
        await event.edit(f"🔒 بخش {part} قفل شد.")

    # 🔓 باز
    @client.on(events.NewMessage(pattern=r"\.باز (.+)$"))
    async def unlock(event):
        if not is_owner(event): return
        part = event.pattern_match.group(1)
        await event.edit(f"🔓 بخش {part} باز شد.")
