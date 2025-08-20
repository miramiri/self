# autocatch.py
import re
import time
import asyncio
from telethon import events

ALLOWED_CMD_PATTERN = re.compile(r'^[\w\s./@#:\-+=!?(),]+$')

def _now_ts():
    return int(time.time())

def register_autocatch(client, state, GLOBAL_GROUPS, save_state, send_status):
    """
    هندلرهای اتوکچ:
      - .کچ <عدد> : تاخیر مخصوص اتوکچ (اعشاری)
      - Copy Plus: بعد از کچ موفق، حتماً .کپی به آخرین پیام کاربر هدف ریپلای می‌شود
      - دیباگ: لاگ در همه مراحل
    """

    # --- دستور .کچ برای تنظیم تاخیر اتوکچ
    @client.on(events.NewMessage(pattern=r'^\.کچ\s+([\d.]+)$'))
    async def set_catch_delay(event):
        if event.sender_id != state.get("owner_id"):
            return
        try:
            delay = float(event.pattern_match.group(1))
            state["catch_delay"] = delay
            save_state()
            await event.edit(f"⏱️ تاخیر اتوکچ روی {delay} ثانیه تنظیم شد")
        except ValueError:
            await event.edit("❌ عدد معتبر نیست")

    # --- ذخیره آخرین پیام کاربر copy_plus_user
    @client.on(events.NewMessage)
    async def track_copy_plus(event):
        target = state.get("copy_plus_user")
        if target and event.sender_id == target:
            print(f"📩 پیام جدید از copy_plus_user ذخیره شد: chat={event.chat_id}, msg={event.id}")
            state["last_copy_plus_msg"] = (event.chat_id, event.id)
            save_state()

    # --- واکنش به پیام Character_Catcher_Bot و فوروارد به کالکت
    @client.on(events.NewMessage(from_users=["Character_Catcher_Bot"]))
    async def check_bot(event):
        gid = event.chat_id

        # فقط گروه‌های ثبت‌شده
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
                    # تاخیر قبل از فوروارد اگر تنظیم شده
                    delay = state.get("catch_delay", 0)
                    if delay > 0:
                        await asyncio.sleep(delay)

                    await client.forward_messages("@collect_waifu_cheats_bot", event.message)
                except Exception as ex:
                    print(f"⚠️ خطا در فوروارد به کالکت: {ex}")
                break

    # --- پردازش پاسخ از @collect_waifu_cheats_bot
    @client.on(events.NewMessage(from_users=["collect_waifu_cheats_bot"]))
    async def handle_collect(event):
        if not state.get("awaiting_collect", False):
            print("ℹ️ handle_collect رد شد: awaiting_collect=False")
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
                            await client.send_message(gid, cmd)
                            state["last_humanizer_cmd"] = cmd
                            state["last_humanizer_ts"] = now
                            acted = True
                        except Exception as ex:
                            print(f"⚠️ خطا در ارسال Humanizer: {ex}")

        # حالت گرفتن کاراکتر جدید (موفق)
        if "got a new character" in text.lower():
            if state.get("last_user"):
                try:
                    funny = state.get("funny_text", "")
                    if funny:
                        await client.send_message(gid, funny)
                except Exception:
                    pass

                # اگر گروه در copy_groups بود → دوباره کپی فعال بشه
                if gid in state.get("copy_groups", []):
                    if state["last_user"] not in state.get("echo_users", []):
                        state["echo_users"].append(state["last_user"])
                        acted = True

                # --- Copy Plus: تلاش برای اجرای .کپی روی آخرین پیام کاربر هدف
                if state.get("copy_plus_user"):
                    try:
                        last = state.get("last_copy_plus_msg")
                        print(f"🔍 بررسی Copy Plus | last={last} | gid={gid}")

                        if last and last[0] == gid:  # مطمئن بشیم همون گروهه
                            await client.send_message(gid, ".کپی", reply_to=last[1])
                            print("✅ شرط Copy Plus برقرار شد و .کپی ارسال شد")
                            acted = True
                        else:
                            print(f"❌ شرط Copy Plus برقرار نشد | last={last} | gid={gid}")
                    except Exception as ex:
                        print(f"⚠️ خطا در اجرای Copy Plus: {ex}")

        # پایان چرخه
        state["awaiting_collect"] = False
        state["saved_echo_users"] = []
        save_state()
        if acted:
            await send_status()
