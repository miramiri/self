import asyncio
import openai
from telethon import events

# توکن OpenAI اینجا وارد کن
openai.api_key = "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"

selling_groups = set()
selling_active = True
ad_message = {
    "text": "🔥 فروش کاراکتر ویژه!",
    "price": "100 اکس",
    "discount": "20 اکس"
}


def build_ad_text():
    return f"{ad_message['text']}\n💰 قیمت: {ad_message['price']}\n🔻 تخفیف: {ad_message['discount']}"


def register_sell(client):
    # ثبت گروه (هیچ پیامی نشون نمی‌ده)
    @client.on(events.NewMessage(pattern=r"\.ثبت فروش$"))
    async def register_group(event):
        selling_groups.add(event.chat_id)

    # تغییر متن تبلیغ
    @client.on(events.NewMessage(pattern=r"\.متن تبلیغ (.+)"))
    async def set_ad_text(event):
        ad_message["text"] = event.pattern_match.group(1)

    # تغییر قیمت
    @client.on(events.NewMessage(pattern=r"\.قیمت (.+)"))
    async def set_price(event):
        ad_message["price"] = event.pattern_match.group(1)

    # تغییر تخفیف
    @client.on(events.NewMessage(pattern=r"\.تخفیف (.+)"))
    async def set_discount(event):
        ad_message["discount"] = event.pattern_match.group(1)

    # شروع فروش (تبلیغ هر ۵ دقیقه، بدون پیام اضافی)
    @client.on(events.NewMessage(pattern=r"\.شروع فروش$"))
    async def start_selling(event):
        global selling_active
        selling_active = True
        while selling_active:
            for chat_id in selling_groups:
                await client.send_message(chat_id, build_ad_text())
                await asyncio.sleep(2)
            await asyncio.sleep(300)  # هر ۵ دقیقه

    # توقف دستی (هیچ پیامی نشون نمی‌ده)
    @client.on(events.NewMessage(pattern=r"\.توقف فروش$"))
    async def stop_selling(event):
        global selling_active
        selling_active = False

    # پاسخ‌گویی هوش مصنوعی
    @client.on(events.NewMessage(chats=lambda x: x in selling_groups))
    async def auto_ai_reply(event):
        global selling_active
        if not selling_active:
            return

        user_text = event.raw_text.strip().lower()

        # اگر مشتری گفت "میخرم"
        if "میخرم" in user_text or "خریدارم" in user_text:
            selling_active = False
            await event.reply("🤝 عالیه! بیا پیوی صحبت کنیم.")
            return

        # فرستادن سوال به ChatGPT
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": user_text}]
            )
            answer = response.choices[0].message["content"]
            await event.reply(answer)
        except:
            pass  # اگه خطا داد هیچی نگه
