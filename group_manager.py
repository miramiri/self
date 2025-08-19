from telethon import events

# وضعیت خوشامدگویی در state ذخیره میشه
WELCOME_KEY = "welcome_message"

def register_group_manager(client, state, GLOBAL_GROUPS, save_state, send_status):
    def is_owner(e): return e.sender_id == state["owner_id"]

    # 🔇 سکوت
    @client.on(events.NewMessage(pattern=r"\.سکوت$"))
    async def mute_tool(event):
        if not is_owner(event): return
        await event.edit("🔇 حالت سکوت فعال شد.")

    # 🔊 حذف سکوت
    @client.on(events.NewMessage(pattern=r"\.حذف سکوت$"))
    async def unmute_tool(event):
        if not is_owner(event): return
        await event.edit("🔊 سکوت برداشته شد.")

    # 👋 تنظیم پیام خوشامدگویی
    @client.on(events.NewMessage(pattern=r"\.تنظیم خوشامد (.+)$"))
    async def set_welcome(event):
        if not is_owner(event): return
        msg = event.pattern_match.group(1)
        state[WELCOME_KEY] = msg
        save_state()
        await event.edit(f"✅ پیام خوشامدگویی تنظیم شد: {msg}")

    # 👋 نمایش پیام خوشامدگویی فعلی
    @client.on(events.NewMessage(pattern=r"\.خوشامدگویی$"))
    async def show_welcome(event):
        if not is_owner(event): return
        msg = state.get(WELCOME_KEY, "پیام خوشامدگویی هنوز تنظیم نشده.")
        await event.edit(f"👋 پیام خوشامدگویی: {msg}")
