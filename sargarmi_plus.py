from telethon import events
import random

def register_sargarmi_plus(client, state, GLOBAL_GROUPS, save_state, send_status):
    def is_owner(e): return e.sender_id == state["owner_id"]

    # 🎲 سرگرمی فان بیشتر
    @client.on(events.NewMessage(pattern=r"\.سرگرمی فان$"))
    async def fun(event):
        if not is_owner(event): return
        funs = [
            "🎉 امروز خیلی باحال می‌گذره!",
            "🤣 یه کاری کن همه بخندن!",
            "🎶 آهنگ گوش کن، انرژی بگیر!",
            "🌈 رنگی رنگی باش!",
            "🍕 پیتزا همیشه حالتو خوب می‌کنه!",
            "🐱 ویدیو گربه‌ها رو نگاه کن، ضد غم.",
            "😎 مثبت باش، دنیا قشنگ‌تر میشه.",
            "🚀 تخیلتو پرواز بده!",
            "📺 یه فیلم کمدی ببین.",
            "🎮 یه گیم بزن، ریلکس شی."
        ]
        await event.edit(random.choice(funs))

    # 📝 تست شخصیت
    @client.on(events.NewMessage(pattern=r"\.تست شخصیت$"))
    async def personality(event):
        if not is_owner(event): return
        tests = [
            "🦁 شخصیتت مثل شیر قویه.",
            "🦉 خیلی عاقل و باهوشی.",
            "🐱 مهربون و دوست‌داشتنی.",
            "🐢 صبور و آروم.",
            "🐉 پرانرژی و شجاع.",
            "🦊 زرنگ و باهوش.",
            "🐧 اجتماعی و بامزه.",
            "🐺 مستقل و جسور.",
            "🐬 خونگرم و خوشحال.",
            "🐦 آزاد مثل پرنده."
        ]
        await event.edit(random.choice(tests))

    # 🧠 معماهای سخت‌تر
    @client.on(events.NewMessage(pattern=r"\.معمای سخت$"))
    async def hard_riddle(event):
        if not is_owner(event): return
        riddles = [
            "🧠 من زنده نیستم اما رشد می‌کنم، ریه ندارم اما هوا می‌خوام. (آتش)",
            "🧠 هرچی بیشتر برداری بزرگ‌تر می‌شم. (چاله)",
            "🧠 بدون دهان حرف می‌زنم، بدون گوش می‌شنوم. (اکو)",
            "🧠 تو یه خونه پر از آیینه باشی، کجا می‌تونی قایم شی؟ (هیچ‌جا)",
            "🧠 اون چیه که همیشه جلوته ولی دیده نمی‌شه؟ (آینده)",
            "🧠 چه چیزی پر از سوراخه ولی آب رو نگه می‌داره؟ (اسفنج)",
            "🧠 اون چیه که از همه بزرگ‌تره اما وزن نداره؟ (سایه)",
            "🧠 چیزی که هیچ‌وقت برنمی‌گرده؟ (زمان)",
            "🧠 اون چیه که شکسته بشه بهتر کار می‌کنه؟ (تخم‌مرغ)",
            "🧠 چه چیزی رو هرچی بیشتر داشته باشی سبک‌تر می‌شی؟ (دانش)"
        ]
        await event.edit(random.choice(riddles))
