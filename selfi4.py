
# -*- coding: utf-8 -*-
from telethon import events

def register_text_styles(client, state, save_state):

    # لیست استایل‌ها
    STYLES = {
        1: lambda t: f"**{t}**",             # بولد
        2: lambda t: f"__{t}__",             # زیرخط
        3: lambda t: f"~~{t}~~",             # خط‌خورده
        4: lambda t: f"`{t}`",               # کد تک‌خطی
        5: lambda t: f"```{t}```",           # بلاک‌کد
        6: lambda t: f"**__{t}__**",         # بولد + زیرخط
    }

    # دستور نمایش لیست استایل‌ها
    @client.on(events.NewMessage(pattern=r"^\.لیست متن$"))
    async def show_styles(event):
        if event.sender_id != state["owner_id"]: return
        txt = "📑 لیست استایل‌های موجود:\n\n"
        txt += "\n".join([f"{i}. {STYLES[i]('نمونه متن')}" for i in STYLES])
        txt += "\n\nبا دستور `.متن <شماره>` استایل رو انتخاب کن."
        await event.reply(txt, parse_mode="md")

    # دستور انتخاب استایل
    @client.on(events.NewMessage(pattern=r"^\.متن (\d+)$"))
    async def set_style(event):
        if event.sender_id != state["owner_id"]: return
        num = int(event.pattern_match.group(1))
        if num not in STYLES:
            await event.reply("❌ شماره اشتباهه.")
            return
        state["text_style"] = num
        save_state()
        await event.reply(f"✅ استایل شماره {num} فعال شد.")

    # هندل پیام‌ها برای اعمال استایل روی متن فقط
    @client.on(events.NewMessage)
    async def apply_style(event):
        if event.sender_id != state["owner_id"]: return
        if not state.get("text_style"): return
        if event.raw_text.startswith("."): return  # دستورات رو تغییر نده
        if not event.raw_text: return  # فقط متن → نه مدیا
        try:
            style_fn = STYLES.get(state["text_style"])
            if style_fn:
                new_text = style_fn(event.raw_text)
                await event.edit(new_text, parse_mode="md")
        except Exception as e:
            print(f"⚠️ خطا در apply_style: {e}")
