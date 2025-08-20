
    # 🧩 معما (سوال و جواب)
    @client.on(events.NewMessage(pattern=r"\.معما$"))
    async def puzzle(event):
        if not is_owner(event): return
        riddle = random.choice(riddles)
        active_riddles[event.sender_id] = riddle
        await event.edit(riddle["q"] + "\n📝 برای جواب دادن بزن `.جواب <متن>`")

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
