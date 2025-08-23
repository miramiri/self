from telethon import events
import json, os
import re

# ---------------- فایل دیتا ----------------
def get_data_file(session_name):
    return f"data_{session_name}.json"


def load_state(session_name):
    file = get_data_file(session_name)
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"owner_id": None, "auto_groups": [], "copy_groups": []}


def save_state(session_name, state):
    file = get_data_file(session_name)
    with open(file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ---------------- ثبت / حذف ----------------
def register_save_group(client, state, groups, save_state, send_status, conn=None, session_name=None):
    def is_owner(e):
        return e.sender_id == state.get("owner_id")

    # --- ثبت فقط برای این اکانت ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت$"))
    async def register_group(event):
        if not is_owner(event): 
            return
        if not event.is_group:
            await event.edit("کص زن جقیت کنم فقط تو گروه کار می‌کنه🤦🏻‍♂️.")
            return

        gid = event.chat_id
        if gid not in state["auto_groups"]:
            state["auto_groups"].append(gid)
            save_state()
            if conn and session_name:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO auto_groups (session_name, gid)
                        VALUES (%s, %s)
                        ON CONFLICT (session_name, gid) DO NOTHING;
                    """, (session_name, gid))
            await event.edit("گروه در حالت سکوت قرار گرفت 😴.")
        else:
            await event.edit("این گروه ساکته😴.")

    # --- ثبت کپی برای همه اکانت‌ها ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت کپی$"))
    async def register_copy_group(event):
        if not is_owner(event): 
            return
        if not event.is_group:
            await event.edit("خو جقی برو تو گروه بزن🤦🏻‍♂️.")
            return

        gid = event.chat_id
        if gid not in groups:
            groups.append(gid)
            save_state()
            if conn and session_name:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO copy_groups (session_name, gid)
                        VALUES (%s, %s)
                        ON CONFLICT (session_name, gid) DO NOTHING;
                    """, (session_name, gid))
            await event.edit("کی دست کرد تو شورت معلم❤️‍🔥🦦")
            await send_status()
        else:
            await event.edit("خو ی بار دست کردی تو شورت معلم بسه دیگه چیو دقیقا میخوای؟🤦🏻‍♂️.")

    # --- حذف گروه ---
    @client.on(events.NewMessage(pattern=r"^\.حذف$"))
    async def unregister_group(event):
        if not is_owner(event): 
            return
        if not event.is_group:
            await event.edit("تو پیوی نزن خو جقی🤦🏻‍♂️.")
            return

        gid = event.chat_id
        removed = False
        if gid in state["auto_groups"]:
            state["auto_groups"].remove(gid)
            removed = True
        if gid in groups:
            groups.remove(gid)
            removed = True
        if removed:
            save_state()
            if conn and session_name:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM auto_groups WHERE session_name = %s AND gid = %s;", (session_name, gid))
                    cur.execute("DELETE FROM copy_groups WHERE session_name = %s AND gid = %s;", (session_name, gid))
            await event.edit("این گروه اصلا سکوت نیست🤨.")
            await send_status()
        else:
            await event.edit("گروه از حالت سکوت در اومد 🦦.")
    # --- ثبت گروه با یوزرنیم ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت یوزر (.+)$"))
    async def save_group_username(event):
        if not event.is_private:
            try:
                username = event.pattern_match.group(1).strip()
                entity = await client.get_entity(username)
                gid = entity.id
                gname = getattr(entity, "title", username)

                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO groups (session_name, gid) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                        (session_name, gid)
                    )
                await event.reply(f"✅ [{gname}] ثبت شد")

            except Exception as e:
                await event.reply(f"❌ خطا در ثبت: {e}")

    # --- ثبت گروه با آیدی ---
    @client.on(events.NewMessage(pattern=r"^\.ثبت آیدی (\d+)$"))
    async def save_group_id(event):
        if not event.is_private:
            try:
                gid = int(event.pattern_match.group(1))
                entity = await client.get_entity(gid)
                gname = getattr(entity, "title", str(gid))

                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO groups (session_name, gid) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                        (session_name, gid)
                    )
                await event.reply(f"✅ [{gname}] ثبت شد")

            except Exception as e:
                await event.reply(f"❌ خطا در ثبت: {e}")

    # --- حذف گروه با یوزرنیم یا آیدی ---
    @client.on(events.NewMessage(pattern=r"^\.حذف (.+)$"))
    async def delete_group(event):
        if not event.is_private:
            try:
                target = event.pattern_match.group(1).strip()

                # اگر عدد بود → آیدی
                if target.isdigit():
                    gid = int(target)
                    entity = await client.get_entity(gid)
                else:
                    entity = await client.get_entity(target)
                    gid = entity.id

                gname = getattr(entity, "title", target)

                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM groups WHERE session_name = %s AND gid = %s;",
                        (session_name, gid)
                    )
                await event.reply(f"❌ [{gname}] حذف شد")

            except Exception as e:
                await event.reply(f"❌ خطا در حذف: {e}")