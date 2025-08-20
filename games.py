from telethon import events
import random, asyncio

# لیست معماها (سوال و جواب جدا)
riddles = [
    {"q": "🧩 چیزی که هرچی ازش برمی‌داری بزرگ‌تر می‌شه؟", "a": "سوراخ"},
    {"q": "🧩 اون چیه که همیشه میاد ولی هیچ وقت نمی‌رسه؟", "a": "فردا"},
    {"q": "🧩 چه چیزی مال توئه ولی بیشتر بقیه استفاده می‌کنن؟", "a": "اسم"},
    {"q": "🧩 چه چیزی پره ولی وزن نداره؟", "a": "حباب"},
    {"q": "🧩 اون چیه که می‌شکنه ولی صدا نداره؟", "a": "قول"},
    {"q": "🧩 اون چیه که همه می‌خورن اما غذا نیست؟", "a": "زمان"},
    {"q": "🧩 اون چیه که خشک می‌کنه ولی خودش خیس می‌شه؟", "a": "حوله"},
    {"q": "🧩 چه چیزی یک بار تو دقیقه، دو بار تو لحظه میاد ولی هیچ وقت تو هزار سال نمیاد؟", "a": "حرف م"},
    {"q": "🧩 اون چیه که هرچی بیشتر داشته باشی کمتر می‌بینی؟", "a": "تاریکی"},
    {"q": "🧩 اون چیه که هیچ وقت سوال نمی‌پرسه ولی همیشه جواب می‌گیره؟", "a": "تلفن"}
]

# وضعیت معماها
active_riddles = {}


def register_games(client, state, GLOBAL_GROUPS, save_state, send_status):
    def is_owner(e): 
        return e.sender_id == state["owner_id"]

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
        user_choice = random.choice(choices)
        bot_choice = random.choice(choices)
        result = "😐 مساوی شد!"
        if (user_choice == "✊ سنگ" and bot_choice == "✌️ قیچی") or \
           (user_choice == "✋ کاغذ" and bot_choice == "✊ سنگ") or \
           (user_choice == "✌️ قیچی" and bot_choice == "✋ کاغذ"):
            result = "✅ تو بردی!"
        elif user_choice != bot_choice:
            result = "❌ ربات برد!"
        await event.edit(f"🎮 انتخاب تو: {user_choice}\n🤖 انتخاب ربات: {bot_choice}\n{result}")

    # 🎲 تاس
    @client.on(events.NewMessage(pattern=r"\.تاس( \d+)?$"))
    async def dice(event):
        if not is_owner(event): return
        arg = event.pattern_match.group(1)
        if arg:
            max_num = int(arg.strip())
            if max_num <= 1:
                await event.edit("❌ عدد باید بیشتر از 1 باشه.")
                return
            result = 0
            while result != max_num:
                result = random.randint(1, max_num)
                msg = await event.respond("🎲")
                await asyncio.sleep(1)
                if result != max_num:
                    await msg.delete()
            await event.respond(f"🎯 عدد {max_num} اومد!")
        else:
            result = random.randint(1, 6)
            await event.respond("🎲")
            await event.respond(str(result))

    # 🍀 شانس
    @client.on(events.NewMessage(pattern=r"\.شانس$"))
    async def luck(event):
        if not is_owner(event): return
        await event.edit(f"🍀 شانس امروزت: {random.randint(1,100)}٪")

    # 🧩 معما (سوال)
    @client.on(events.NewMessage(pattern=r"\.معما$"))
    async def puzzle(event):
        if not is_owner(event): return
        riddle = random.choice(riddles)
        active_riddles[event.sender_id] = riddle
        await event.edit(riddle["q"] + "\n📝 برای جواب دادن بزن `.جواب <متن>`")

    # 🧩 جواب معما
    @client.on(events.NewMessage(pattern=r"\.جواب (.+)$"))
    async def puzzle_answer(event):
        if not is_owner(event): return
        if event.sender_id not in active_riddles:
            await event.edit("❌ اول باید یک معما بپرسی (`.معما`).")
            return
        user_answer = event.pattern_match.group(1).strip()
        correct = active_riddles[event.sender_id]["a"]
        if user_answer == correct:
            await event.edit(f"✅ درست گفتی! جواب: {correct}")
        else:
            await event.edit("❌ نه درست نیست، دوباره امتحان کن!")
