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
    - auto_groups: فقط اتوکچ
    - copy_groups: اتوکچ + کپی
    """

    # مقدار پیش‌فرض سرعت کچ
    if "catch_delay" not in state:
        state["catch_delay"] = 1.0

    # --- تغییر سرعت کچ با '.کچ 1.5' و ...
    @client.on(events.NewMessage(pattern=r"\.کچ (\d+(?:\.\d+)?)$"))
    async def set_catch_delay(event):
        if event.sender_id != state.get("owner_id"): return
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

        # فقط گروه‌هایی که ثبت شده‌اند
        if gid not in (state.get("auto_groups", []) + state.get("copy_groups", [])):
            return

        text = event.raw_text or ""
        emojis = state.get("stop_emoji") or []

        for e in emojis:
            if text.startswith(e):
                # اتوکچ فعال
                if not state.get("awaiting_collect", False):
                    prev_list = list(state.get("echo_users", []))
                    state["saved_echo_users"] = prev_list
                    state["last_user"] = prev_list[-1] if prev_list else None
                    state["last_group"] = gid
                    state["echo_users"] = []           # توقف موقت کپی
                    state["awaiting_collect"] = True   # منتظر پاسخ کالکت
                    state["last_collect_trigger"] = _now_ts()
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
        if not state.get("awaiting_collect", False):
            return

        text = (event.raw_text or "").strip()
        gid = state.get("last_group")
        if not gid:
            state["awaiting_collect"] = False
            save_state()
            return

        acted = False

        # حالت Humanizer
        if "Humanizer:" in text:
            m = re.search(r'Humanizer:\s*([^\r\n]+)', text, re.IGNORECASE)
            if m:
                cmd = m.group(1).strip().strip('`"\'')
                if 0 < len(cmd) <= 200 and ALLOWED_CMD_PATTERN.match(cmd):
                    last_cmd = state.get("last_humanizer_cmd")
                    last_ts = state.get("last_humanizer_ts", 0)
                    now = _now_ts()
                    if cmd != last_cmd or (now - last_ts) > 5:
                        try:
                            await asyncio.sleep(state.get("catch_delay", 1.0))
                            await client.send_message(gid, cmd)
                            state["last_humanizer_cmd"] = cmd
                            state["last_humanizer_ts"] = now
                            acted = True
                        except Exception as ex:
                            print(f"⚠️ خطا در ارسال Humanizer: {ex}")

        # حالت گرفتن کاراکتر جدید
        if "got a new character" in text.lower():
            if state.get("last_user"):
                try:
                    await asyncio.sleep(state.get("catch_delay", 1.0))
                    await client.send_message(gid, state.get("funny_text", ""))
                except Exception:
                    pass

                # اگر گروه در copy_groups بود → دوباره کپی فعال بشه
                if gid in state.get("copy_groups", []):
                    prev_list = state.get("saved_echo_users", [])
                    for u in prev_list:
                        if u not in state["echo_users"]:
                            state["echo_users"].append(u)
                            acted = True

                # اگر کپی پلاس فعال بود → مستقیم یوزر دوباره اضافه بشه
                if state.get("copy_plus_user"):
                    target = state["copy_plus_user"]
                    if target not in state["echo_users"]:
                        state["echo_users"].append(target)
                        acted = True

        # پایان چرخه
        state["awaiting_collect"] = False
        state["saved_echo_users"] = []
        save_state()
        if acted:
            await send_status()