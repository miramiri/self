# -*- coding: utf-8 -*-
from telethon import events, Button
import asyncio

def register_selfi3_cmds(client, state, GLOBAL_GROUPS, save_state, send_status, session_name):
    # ---------- کپی ----------
    @client.on(events.NewMessage(pattern=r".کپی$"))
    async def enable_copy(event):
        if event.sender_id != state["owner_id"]: return
        if not event.is_reply:
            await event.edit("❌ روی پیام ریپلای کن!")
            return
        reply = await event.get_reply_message()
        user = await reply.get_sender()
        if user.id not in state["echo_users"]:
            state["echo_users"].append(user.id)
            state["last_user"] = user.id
            state["last_group"] = event.chat_id
            save_state()
            await event.edit(f"✅ کپی برای {user.first_name} فعال شد.")
        else:
            await event.edit("ℹ️ قبلاً فعال بود.")
        await send_status()

    # ---------- کپی خاموش ----------
    @client.on(events.NewMessage(pattern=r".کپی خاموش$"))
    async def disable_copy(event):
        if event.sender_id != state["owner_id"]: return
        if not event.is_reply:
            await event.edit("❌ روی پیام ریپلای کن!")
            return
        reply = await event.get_reply_message()
        user = await reply.get_sender()
        if user.id in state["echo_users"]:
            state["echo_users"].remove(user.id)
            save_state()
            await event.edit(f"⛔ کپی برای {user.first_name} خاموش شد.")
        else:
            await event.edit("ℹ️ این کاربر فعال نبود.")
        await send_status()

    # ---------- کپی پلاس ----------
    @client.on(events.NewMessage(pattern=r"^\.کپی پلاس$"))
    async def copy_plus(event):
        if event.sender_id != state["owner_id"]: return
        if not event.is_reply:
            await event.edit("❌ روی پیام ریپلای کن!")
            return
        reply = await event.get_reply_message()
        user = await reply.get_sender()
        state["copy_plus_user"] = user.id
        save_state()
        await event.edit(
            f"✨ کپی پلاس فعال شد برای {getattr(user, 'first_name', 'کاربر')}\n"
            f"هر وقت اتوکچ قطع شد، دوباره براش فعال میشه.",
            buttons=[[Button.inline("❌ حذف کپی پلاس", b"del_copy_plus")]]
        )
        await send_status()

    @client.on(events.CallbackQuery(pattern=b"del_copy_plus"))
    async def del_copy_plus(event):
        if event.sender_id != state["owner_id"]: return
        state["copy_plus_user"] = None
        save_state()
        await event.edit("❌ کپی پلاس حذف شد.")
        await send_status()

    # ---------- ریست دیتا ----------
    @client.on(events.NewMessage(pattern=r"^\.ریست دیتا$"))
    async def reset_data(event):
        if event.sender_id != state["owner_id"]: return
        status_msg_id_keep = state.get("status_msg_id")
        state.clear()
        state.update({
            "owner_id": event.sender_id,
            "echo_users": [],
            "enabled": True,
            "delay": 2.0,
            "stop_emoji": ["⚜", "💮", "⚡", "❓"],
            "last_user": None,
            "last_group": None,
            "funny_text": "مگه نیما فشاری 😂",
            "status_msg_id": status_msg_id_keep,
            "auto_groups": [],
            "copy_plus_user": None,
            "copy_groups": []
        })
        save_state()
        await event.reply("♻️ فایل دیتا ریست شد.")
        await send_status()

    # ---------- دستور .ست ----------
    @client.on(events.NewMessage(pattern=r"^\.ست حذف همه$"))
    async def clear_stop_emoji(event):
        if event.sender_id != state["owner_id"]: return
        state["stop_emoji"] = []
        save_state()
        await event.edit("🧹 ایموجی‌های قطع‌کننده حذف شد.")
        await send_status()

    @client.on(events.NewMessage(pattern=r"^\.ست$"))
    async def show_stop_emoji(event):
        if event.sender_id != state["owner_id"]: return
        cur_emojis = ", ".join(state["stop_emoji"]) if state["stop_emoji"] else "هیچ"
        await event.edit(f"⛔ ایموجی‌های فعلی: {cur_emojis}\n"
                          f"برای تنظیم چندتا باهم: `.ست 😀 💮 ⚡️`")

    @client.on(events.NewMessage(pattern=r"^\.ست (.+)$"))
    async def set_stop_emoji(event):
        if event.sender_id != state["owner_id"]: return
        args = event.pattern_match.group(1).strip()
        tokens = [tok for tok in args.split() if tok]
        seen, emojis = set(), []
        for t in tokens:
            if t not in seen:
                seen.add(t)
                emojis.append(t)
        if len(emojis) > 10:
            emojis = emojis[:10]
        state["stop_emoji"] = emojis
        save_state()
        cur_emojis = ", ".join(state["stop_emoji"]) if state["stop_emoji"] else "هیچ"
        await event.edit(f"✅ ایموجی‌های قطع‌کننده تنظیم شد: {cur_emojis}")
        await send_status()

    # ---------- دستور تاخیر ----------
    @client.on(events.NewMessage(pattern=r"^\.(\d+(?:\.\d+)?)$"))
    async def set_delay(event):
        if event.sender_id != state["owner_id"]: return
        try:
            delay = float(event.pattern_match.group(1))
        except ValueError:
            await event.edit("❌ عدد درست وارد کن.")
            return

        state["delay"] = max(0.0, delay)
        save_state()

        if delay == 0:
            await event.edit("⏱️ تاخیر روی 0 (درجا) تنظیم شد.")
        else:
            await event.edit(f"⏱️ تاخیر روی {delay} ثانیه تنظیم شد.")
        await send_status()

    # ---------- موتور کپی گروه ----------
    @client.on(events.NewMessage)
    async def copy_groups_handler(event):
        if not state.get("enabled", True):
            return
        if event.chat_id not in state.get("copy_groups", []):
            return
        if event.sender_id not in state.get("echo_users", []):
            return
        await asyncio.sleep(state.get("delay", 2.0))
        try:
            if event.media:
                await client.send_file(event.chat_id, event.media, caption=event.text)
            else:
                await client.send_message(event.chat_id, event.text)
        except Exception as e:
            print(f"❌ خطا در کپی پیام در {event.chat_id}: {e}")
