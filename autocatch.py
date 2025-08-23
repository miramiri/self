import re
import time
import asyncio
from telethon import events

ALLOWED_CMD_PATTERN = re.compile(r'^[\w\s./@#:\-+=!?(),]+$')

def _now_ts():
    return int(time.time())

def register_autocatch(client, state, GLOBAL_GROUPS, save_state, send_status):
    """
    ثبت هندلرهای اتوکچ روی کلاینت
    - auto_groups: فقط اتوکچ (اختصاصی هر اکانت)
    - GLOBAL_GROUPS: گروه‌های کپی عمومی
    """

    if "catch_delay" not in state:
        state["catch_delay"] = 1.0
    if "pending_catches" not in state:
        state["pending_catches"] = []

    # --- تشخیص خودکار owner_id در اولین بار
    async def ensure_owner():
        if "owner_id" not in state or not state["owner_id"]:
            me = await client.get_me()
            state["owner_id"] = me.id
            save_state()
            print(f"✅ owner_id شناسایی شد: {me.id}")

    client.loop.create_task(ensure_owner())

    # --- تغییر سرعت کچ با '.کچ 1.5' و ...
    @client.on(events.NewMessage(pattern=r"\.کچ (\d+(?:\.\d+)?)$"))
    async def set_catch_delay(event):
        if event.sender_id != state.get("owner_id"):
            return
        try:
            delay = float(event.pattern_match.group(1))
        except Exception:
            return
        state["catch_delay"] = delay
        save_state()
        await event.edit(f"⚡ سرعت کچ روی {delay} ثانیه تنظیم شد.")
        await send_status()

    # --- واکنش به پیام Character_Catcher_Bot و فوروارد به کالکت
    @client.on(events.NewMessage(from_users=["Character_Catcher_Bot"]))
    async def check_bot(event):
        gid = event.chat_id

        if gid not in (state.get("auto_groups", []) + GLOBAL_GROUPS):
            return

        text = event.raw_text or ""
        for e in (state.get("stop_emoji") or []):
            if text.startswith(e):
                state["pending_catches"].append({
                    "gid": gid,
                    "users": list(state.get("echo_users", [])),
                    "time": _now_ts()
                })
                state["echo_users"] = []
                save_state()
                await send_status()

                try:
                    await asyncio.sleep(state.get("catch_delay", 1.0))
                    await client.forward_messages("@collect_waifu_cheats_bot", event.message)
                except Exception as ex:
                    print(f"⚠️ خطا در فوروارد به کالکت: {ex}")
                break

    # --- پردازش پاسخ از @collect_waifu_cheats_bot
    @client.on(events.NewMessage(from_users=["collect_waifu_cheats_bot"]))
    async def handle_collect(event):
        if not state["pending_catches"]:
            return

        req = state["pending_catches"].pop(0)
        gid = req["gid"]
        saved_users = req["users"]
        text = (event.raw_text or "").strip()
        acted = False

        # حالت Humanizer
        if "Humanizer:" in text:
            m = re.search(r'Humanizer:\s*([^\r\n]+)', text, re.IGNORECASE)
            if m:
                cmd = m.group(1).strip().strip('`"\'')
                if 0 < len(cmd) <= 200 and ALLOWED_CMD_PATTERN.match(cmd):
                    try:
                        await asyncio.sleep(state.get("catch_delay", 1.0))
                        await client.send_message(gid, cmd)
                        acted = True
                    except Exception as ex:
                        print(f"⚠️ خطا در ارسال Humanizer: {ex}")

        # حالت گرفتن کاراکتر جدید
        if "got a new character" in text.lower():
            try:
                await asyncio.sleep(state.get("catch_delay", 1.0))
                await client.send_message(gid, state.get("funny_text", ""))
            except Exception:
                pass

            for u in saved_users:
                if u not in state["echo_users"]:
                    state["echo_users"].append(u)
                    acted = True

            if state.get("copy_plus_user"):
                target = state["copy_plus_user"]
                if target not in state["echo_users"]:
                    state["echo_users"].append(target)
                    acted = True

        save_state()
        if acted:
            await send_status()