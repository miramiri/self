from telethon import events
import random

def register_sargarmi(client, state, GLOBAL_GROUPS, save_state, send_status):
    def is_owner(e): return e.sender_id == state["owner_id"]

    @client.on(events.NewMessage(pattern=r"\.میم$"))
    async def meme(event):
        if not is_owner(event): return
        memes = [
            "😹","😂😂😂","🤡","🐸👉🍵","🗿","🤣","🙃","🤪","😆","😅",
            "😎","😏","🤓","🥸","🥴","🤯","😤","🥱","🤧","😇",
            "👻","👽","🤖","🎃","🐵"
        ]
        await event.edit(f"میم رندوم: {random.choice(memes)}")

    @client.on(events.NewMessage(pattern=r"\.واقعیت$"))
    async def fact(event):
        if not is_owner(event): return
        facts = [
            "🐘 فیل‌ها نمی‌تونن بپرن.","😴 مغز موقع خواب فعال‌تره.",
            "🥶 کوالاها روزی ۲۰ ساعت می‌خوابن.","🐢 لاک‌پشت‌ها از مقعد نفس می‌کشن.",
            "🌋 آذرخش ۵ برابر خورشید داغ‌تره.","🐧 پنگوئن‌ها فقط جنوبگان زندگی می‌کنن.",
            "🦒 زبان زرافه ۴۵ سانتیه.","🐌 حلزون سه سال می‌تونه بخوابه.",
            "🐔 مرغ می‌تونه بدون سر چند روز زنده بمونه.","🐙 اختاپوس سه قلب داره.",
            "🦈 کوسه‌ها هیچوقت سرطان نمی‌گیرن.","🌌 کهکشان راه شیری ۱۰۰ میلیارد ستاره داره.",
            "🌍 زمین روزی ۱ میلی‌متر بزرگتر میشه.","🐝 زنبورها همدیگه رو می‌رقصونن برای مسیر.",
            "🐶 سگ‌ها بیش از ۲۵۰ کلمه می‌فهمن.","🐱 گربه‌ها ۱۰۰ صدا در میارن.",
            "🐴 اسب‌ها نمیتونن استفراغ کنن.","🦆 اردک‌ها خواب نیمکره‌ای دارن.",
            "🦋 پروانه‌ها با پاهاشون مزه رو می‌چشن.","🐊 تمساح‌ها زبانشونو بیرون نمیارن.",
            "🐼 پاندا روزی ۱۲ ساعت بامبو می‌خوره.","🐒 میمون‌ها هم شوخی می‌کنن.",
            "🐀 موش‌ها می‌خندن.","🦜 طوطی‌ها آینه می‌فهمن.",
            "🐬 دلفین‌ها اسم دارن."
        ]
        await event.edit(random.choice(facts))

    @client.on(events.NewMessage(pattern=r"\.انگیزه$"))
    async def motivate(event):
        if not is_owner(event): return
        texts = [
            "🚀 هیچ وقت دیر نیست برای شروع دوباره.","💡 هر روز یه فرصت جدیده.",
            "🔥 تو می‌تونی، فقط شروع کن.","⏳ حتی قدم کوچیک هم پیشرفته.",
            "🏆 موفقیت یعنی ادامه دادن.","🎯 تمرکز کن روی هدفت.",
            "📈 پیشرفت آروم هم پیشرفته.","💎 تو ارزشمندی.",
            "🌟 بهترینت باش.","💪 شکست یعنی تجربه.",
            "🌱 هر روز رشد کن.","🌈 فردا روشن‌تره.",
            "🌞 هر طلوع یعنی امید.","🛠️ هر مشکلی راه حلی داره.",
            "🎶 ادامه بده، دنیا صداتو می‌شنوه.","🦁 شجاع باش.",
            "⚡ شروع کن، بقیه میاد.","🏋️ قوی‌تر از دیروزی.",
            "🔥 درونت آتیش داره.","🌀 تغییر از تو شروع میشه.",
            "📚 یادگیری بی‌پایانه.","🌍 اثر بذار.",
            "🚴 حرکت کن.","🎉 جشن بگیر موفقیتتو.",
            "🥇 تو برنده‌ای."
        ]
        await event.edit(random.choice(texts))

    @client.on(events.NewMessage(pattern=r"\.دیالوگ$"))
    async def dialog(event):
        if not is_owner(event): return
        lines = [
            "🃏 Why so serious?","🎬 I'll be back.","🐴 Say hello to my little friend!",
            "💣 Hasta la vista, baby.","⚡ With great power comes great responsibility.",
            "🌌 May the Force be with you.","🔥 I'm the king of the world!",
            "🕷️ Whatever life holds in store, I will never forget these words.",
            "🦇 I'm Batman.","🤠 You talking to me?",
            "🎭 To be, or not to be.","💔 Here's looking at you, kid.",
            "🌊 Just keep swimming.","🥶 The cold never bothered me anyway.",
            "🛡️ I can do this all day.","👑 Winter is coming.",
            "⚔️ Valar Morghulis.","🚢 I'm the captain now.",
            "🌍 We are Groot.","💀 Say my name.",
            "🔫 Yippee-ki-yay.","🐍 Why did it have to be snakes?",
            "🎩 Elementary, my dear Watson.","📜 Freedom is not free.",
            "💎 Wakanda forever!"
        ]
        await event.edit(random.choice(lines))

    @client.on(events.NewMessage(pattern=r"\.بزن$"))
    async def punch(event):
        if not is_owner(event): return
        if not event.is_reply:
            await event.edit("⚠️ روی کاربر ریپلای کن.")
            return
        user = await (await event.get_reply_message()).get_sender()
        await event.edit(f"👊 {user.first_name} خوردی!")

    @client.on(events.NewMessage(pattern=r"\.بغل$"))
    async def hug(event):
        if not is_owner(event): return
        if not event.is_reply:
            await event.edit("⚠️ روی کاربر ریپلای کن.")
            return
        user = await (await event.get_reply_message()).get_sender()
        await event.edit(f"🤗 {user.first_name} بغل!")

    @client.on(events.NewMessage(pattern=r"\.بپرس (.+)$"))
    async def ask(event):
        if not is_owner(event): return
        answers = [
            "✅ آره","❌ نه","❓ شاید","🤔 معلوم نیست","🌀 دوباره بپرس",
            "🌟 حتما","🙅 اصلا","👌 قطعا","🤷 بستگی داره","💯 صد در صد",
            "😬 فکر نکنم","🥳 آرههه","😢 نه دیگه","😎 معلومه","😴 خوابم میاد، بعد بپرس",
            "😏 شاید شاید","👀 معلوم میشه","🐸 یه قورباغه گفت بله","🦄 چرا که نه؟","🔥 فقط تو می‌تونی جواب بدی",
            "⚡ برق میگه آره","🌈 رنگین‌کمان میگه نه","📱 گوشی میگه خاموشه","🚪 در بسته‌ست","🎲 شانسیه"
        ]
        await event.edit(f"🎱 {random.choice(answers)}")

    @client.on(events.NewMessage(pattern=r"\.اسم$"))
    async def nickname(event):
        if not is_owner(event): return
        names = [
            "🔥 سلطان","🐉 اژدها","👑 پادشاه","🦸 قهرمان","💎 الماس",
            "🦁 شیر","🐺 گرگ","⚡ صاعقه","🌟 ستاره","🎩 جادوگر",
            "🐲 اژدر","🦂 عقرب","🦅 عقاب","🦊 روباه","🐯 ببر",
            "🐼 پاندا","🐻 خرس","🐬 دلفین","🐠 ماهی","🦄 تک‌شاخ",
            "🌙 ماه","☀️ خورشید","🔥 آتیش","🍀 چهاربرگ","🌈 رنگین‌کمان"
        ]
        await event.edit(f"اسم قشنگت: {random.choice(names)}")

    @client.on(events.NewMessage(pattern=r"\.جوک$"))
    async def joke(event):
        if not is_owner(event): return
        jokes = [
            "😂 یه نفر رفت دکتر گفت هرچی شیر می‌خورم سردمه! گفت شیر گاوه نه بخاری!",
            "🤣 طرف می‌گفت من حافظه‌م خیلی خوبه، فقط یادم نمیاد چی بود!",
            "😹 معلم: چرا مشقاتو ننوشتی؟ دانش‌آموز: چون خودکارم جوهر نداشت!",
            "🙃 گفتن چرا دیر اومدی؟ گفت ماشینم پنچر شد... با دوچرخه اومده بود!",
            "🤣 یکی گفت خواب دیدم تکلیفامو نوشتم، پس دیگه لازم نبود بنویسم!",
            "😂 بچه‌ه گفت بابا من بزرگ بشم چی میشم؟ گفت فقیر!",
            "🤣 یکی به دیوار گفت جم شو، گفت مگه دیوارم!",
            "😹 معلم گفت چرا خوابی؟ گفت چشمام تمرین بستن داشتن!",
            "🙃 طرف گفت من از همه باهوش‌ترم، بعد رفت تو دیوار!",
            "🤣 یکی رفت نونوایی گفت نون داری؟ گفت نه، پس چرا باز کردی؟ گفت هوا بخوره!",
            "😂 بچه به باباش: چرا موهام سفید شده؟ گفت چون تو اذیتم کردی! بچه: پس ببین تو مامان‌مو چقدر اذیت کردی!",
            "🤣 یکی گفت من رژیم دارم فقط هوا می‌خورم، بعد دیدن کله‌پاچه دستشه!",
            "😹 معلم گفت ۲+۲؟ گفت پنج! گفت چرا؟ گفت پنج بهتره!",
            "🙃 یه نفر چایی ریخت رو لپ‌تاپش گفت حالا قهوه‌ساز هم شد!",
            "🤣 یکی گفت ماشینم برقیه، بعد دیدن دوچرخه‌ش باتری چراغ داره!",
            "😂 بچه گفت بابا برام آب بیار! گفت از یخچال؟ بچه: نه از دریا!",
            "🤣 یکی رفت پیتزا فروشی گفت برش نزن، من خودم رژیم دارم!",
            "😹 یه نفر افتاد تو چاه گفت وای فای اینجا ضعیفه!",
            "🙃 گفتن چرا تو مدرسه نمیری؟ گفت چون ساختمونه!",
            "🤣 یکی پرسید چند سالته؟ گفت ۲۴، سه سال دیگه ۱۸ میشم!",
            "😂 بچه گفت چرا آسمون آبیه؟ گفت چون قرمزش شسته شده!",
            "🤣 طرف گفت گوشی جدید گرفتم، بعد دیدن خط خونه‌شه!",
            "😹 یکی گفت میرم باشگاه، بعد دیدن روی مبل خوابیده!",
            "🙃 گفت چرا غذا نمیخوری؟ گفت رژیم دارم، دارم نفس می‌کشم!",
            "🤣 یکی گفت منو بلاک نکن، گفت برو کشاورزی!"
        ]
        await event.edit(random.choice(jokes))
