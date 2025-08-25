import asyncio
from datetime import datetime
from telethon import events
from telethon.tl.functions.account import UpdateProfileRequest

# 📌 جدول ۵۰ فونت
FONTS = {
    1: lambda t: t,
    2: lambda t: t.translate(str.maketrans("0123456789:", "⓿①②③④⑤⑥⑦⑧⑨:")),
    3: lambda t: t.translate(str.maketrans("0123456789:", "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿:")),
    4: lambda t: t.translate(str.maketrans("0123456789:", "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡:")),
    5: lambda t: t.translate(str.maketrans("0123456789:", "０１２３４５６７８９：")),
    6: lambda t: t.translate(str.maketrans("0123456789:", "⓪①②③④⑤⑥⑦⑧⑨：")),
    7: lambda t: t.translate(str.maketrans("0123456789:", "❶❷❸❹❺❻❼❽❾⓿:")),
    8: lambda t: t.translate(str.maketrans("0123456789:", "➀➁➂➃➄➅➆➇➈➉:")),
    9: lambda t: t.translate(str.maketrans("0123456789:", "➊➋➌➍➎➏➐➑➒⓿:")),
    10: lambda t: t.translate(str.maketrans("0123456789:", "⓵⓶⓷⓸⓹⓺⓻⓼⓽⓿:")),
    11: lambda t: t.translate(str.maketrans("0123456789:", "🄌➊➋➌➍➎➏➐➑➒:")),
    12: lambda t: t.translate(str.maketrans("0123456789:", "🄍➀➁➂➃➄➅➆➇➈:")),
    13: lambda t: t.translate(str.maketrans("0123456789:", "⁰¹²³⁴⁵⁶⁷⁸⁹:")),
    14: lambda t: t.translate(str.maketrans("0123456789:", "₀₁₂₃₄₅₆₇₈₉:")),
    15: lambda t: t.replace(":", "꞉"),
    16: lambda t: t.replace(":", "ː"),
    17: lambda t: t.replace(":", "∶"),
    18: lambda t: t.replace(":", "⍛"),
    19: lambda t: t.replace(":", "ꗇ"),
    20: lambda t: t.replace(":", "⫶"),
    21: lambda t: t.replace(":", "⸳"),
    22: lambda t: t.replace(":", "⦙"),
    23: lambda t: t.replace(":", "𐄁"),
    24: lambda t: t.replace(":", "⸲"),
    25: lambda t: t.replace(":", "﹕"),
    26: lambda t: t.replace("0", "⭕"),
    27: lambda t: t.replace("1", "❶"),
    28: lambda t: t.replace("2", "❷"),
    29: lambda t: t.replace("3", "❸"),
    30: lambda t: t.replace("4", "❹"),
    31: lambda t: t.replace("5", "❺"),
    32: lambda t: t.replace("6", "❻"),
    33: lambda t: t.replace("7", "❼"),
    34: lambda t: t.replace("8", "❽"),
    35: lambda t: t.replace("9", "❾"),
    36: lambda t: " ".join(list(t)),
    37: lambda t: t[::-1],
    38: lambda t: f"【{t}】",
    39: lambda t: f"『{t}』",
    40: lambda t: f"〘{t}〙",
    41: lambda t: f"《{t}》",
    42: lambda t: f"〔{t}〕",
    43: lambda t: f"⦅{t}⦆",
    44: lambda t: f"✦{t}✦",
    45: lambda t: f"❖{t}❖",
    46: lambda t: f"✧{t}✧",
    47: lambda t: f"✪{t}✪",
    48: lambda t: f"◉{t}◉",
    49: lambda t: f"✷{t}✷",
    50: lambda t: f"✺{t}✺",
}

def register_clock(client, state, save_state):
    if "clock_font" not in state:
        state["clock_font"] = 1
    if "clock_on" not in state:
        state["clock_on"] = False

    async def update_clock():
        while True:
            try:
                if state.get("clock_on", False):
                    now = datetime.now().strftime("%H:%M")
                    font_fn = FONTS.get(state["clock_font"], FONTS[1])
                    styled_time = font_fn(now)
                    await client(UpdateProfileRequest(last_name=f"⏰ {styled_time}"))
                await asyncio.sleep(60)
            except Exception as e:
                print(f"⚠️ خطا در آپدیت ساعت: {e}")
                await asyncio.sleep(60)

    client.loop.create_task(update_clock())

    # --- لیست فونت‌ها
    @client.on(events.NewMessage(pattern=r"^\.لیست ساعت$"))
    async def list_fonts(event):
        sample = datetime.now().strftime("%H:%M")
        msg = "📑 لیست فونت‌های ساعت:\n\n"
        for i, fn in FONTS.items():
            msg += f"{i}. {fn(sample)}\n"
        await event.edit(msg)

    # --- تغییر فونت
    @client.on(events.NewMessage(pattern=r"^\.ساعت (\d+)$"))
    async def set_font(event):
        try:
            num = int(event.pattern_match.group(1))
            if num in FONTS:
                state["clock_font"] = num
                save_state()
                await event.edit(f"✅ فونت ساعت روی {num} تنظیم شد.")
            else:
                await event.edit("❌ فونت نامعتبره.")
        except Exception:
            await event.edit("❌ عدد درست بده.")

    # --- روشن
    @client.on(events.NewMessage(pattern=r"^\.ساعت روشن$"))
    async def clock_on(event):
        state["clock_on"] = True
        save_state()
        await event.edit("✅ ساعت روی پروفایل فعال شد.")

    # --- خاموش
    @client.on(events.NewMessage(pattern=r"^\.ساعت خاموش$"))
    async def clock_off(event):
        state["clock_on"] = False
        save_state()
        try:
            await client(UpdateProfileRequest(last_name=""))  # پاک کردن فامیل
        except Exception as e:
            print(f"⚠️ خطا در پاک کردن ساعت: {e}")
        await event.edit("❌ ساعت خاموش شد و از پروفایل پاک شد.")