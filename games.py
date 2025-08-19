from telethon import events
import random, asyncio

def register_games(client, state, GLOBAL_GROUPS, save_state, send_status):
    def is_owner(e): return e.sender_id == state["owner_id"]

    # 🎲 حدس عدد
    @client.on(events.NewMessage(pattern=r"\.حدس عدد$"))
    async def guess_number(event):
        if not is_owner(event): return
        number = random.randint(1, 10)
        await event.edit(f"🤔 یک عدد بین 1 تا 10 حدس بزن!")
        await asyncio.sleep(2)
        await event.edit(f"🎯 عدد انتخاب شده: {number}")

    # ✊ سنگ کاغذ قیچی
    @client.on(events.NewMessage(pattern=r"\.سنگ کاغذ قیچی$"))
    async def rps(event):
        if not is_owner(event): return
        choices = ["✊ سنگ", "✋ کاغذ", "✌️ قیچی"]
        await event.edit(f"🎮 نتیجه: {random.choice(choices)}")

    # 🎲 تاس معمولی
    @client.on(events.NewMessage(pattern=r"\.تاس$"))
    async def dice(event):
        if not is_owner(event): return
        await event.edit(f"🎲 تاس: {random.randint(1,6)}")

    # 🎲 تاس با عدد مشخص
    @client.on(events.NewMessage(pattern=r"\.تاس (\d)$"))
    async def dice_until_target(event):
        if not is_owner(event): return
        try:
            target = int(event.pattern_match.group(1))
            if target < 1 or target > 6:
                await event.edit("❌ لطفا عددی بین 1 تا 6 وارد کنید.")
                return
        except:
            await event.edit("❌ خطا در ورودی. فقط عدد 1 تا 6 مجازه.")
            return

        msg = event
        while True:
            dice = random.randint(1, 6)
            await msg.edit(f"🎲 تاس انداختی: {dice}")
            if dice == target:
                break
            await asyncio.sleep(0)

    # 🍀 شانس
    @client.on(events.NewMessage(pattern=r"\.شانس$"))
    async def luck(event):
        if not is_owner(event): return
        await event.edit(f"🍀 شانس امروزت: {random.randint(1,100)}٪")

    # 🧩 معما
    @client.on(events.NewMessage(pattern=r"\.معما$"))
    async def puzzle(event):
        if not is_owner(event): return
        riddles = [
            "🧩 چیزی که هرچی ازش برمی‌داری بزرگ‌تر می‌شه؟ (سوراخ)",
            "🧩 اون چیه که همیشه میاد ولی هیچ وقت نمی‌رسه؟ (فردا)",
            "🧩 چه چیزی مال توئه ولی بیشتر بقیه استفاده می‌کنن؟ (اسم)",
            "🧩 چه چیزی پره ولی وزن نداره؟ (حباب)",
            "🧩 اون چیه که می‌شکنه ولی صدا نداره؟ (قول)",
            "🧩 اون چیه که همه می‌خورن اما غذا نیست؟ (زمان)",
            "🧩 اون چیه که خشک می‌کنه ولی خودش خیس می‌شه؟ (حوله)",
            "🧩 چه چیزی یک بار تو دقیقه، دو بار تو لحظه میاد ولی هیچ وقت تو هزار سال نمیاد؟ (حرف م)",
            "🧩 اون چیه که هرچی بیشتر داشته باشی کمتر می‌بینی؟ (تاریکی)",
            "🧩 اون چیه که هیچ وقت سوال نمی‌پرسه ولی همیشه جواب می‌گیره؟ (تلفن)"
        ]
        await event.edit(random.choice(riddles))
