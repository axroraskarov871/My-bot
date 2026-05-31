    text = update.message.text
    data = get_user(user_id)

    # Bot foydalanuvchiga "yozmoqda..." holatini ko'rsatadi
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    hour = datetime.now().hour
    meal = "nonushta" if hour < 11 else "tushlik" if hour < 15 else "kechki ovqat"
    month = datetime.now().strftime('%B')
    season = "qish" if datetime.now().month in [12, 1, 2] else "bahor" if datetime.now().month in [3, 4, 5] else "yoz" if datetime.now().month in [6, 7, 8] else "kuz"

    prompts = {
        "🌤 Ob-havo": f"{YOUR_CITY}da {month} oyida ob-havo qanday? Qisqa ayt.",
        "👔 Kiyinish": f"{YOUR_CITY}da {season}da qanday kiyinish kerak? Faqat erkaklar uchun amaliy tavsiya ber.",
        "🥗 Ovqat": f"Bugun {meal} uchun 3 ta sog'lom va arzon o'zbekona taom tavsiya qil.",
        "💰 Pul tejash": "O'zbekistonda moliyaviy barqarorlik va pul tejash bo'yicha 3 ta amaliy maslahat ber.",
        "📋 Vazifalar": f"Mening vazifalarim: {', '.join(data['tasks']) or 'yo`q'}. Qanday samarali bajaraman?",
        "🎯 Maqsadlar": f"Mening maqsadlarim: {', '.join(data['goals']) or 'yo`q'}. Bugun nima qilaman?",
        "💡 Life hack": "Bugun uchun bitta foydali va samarali life hack ber.",
        "🧠 Muammo hal": "Bugun uchun bitta amaliy muammo va uning yechimini mantiqiy model asosida tushuntir.",
        "📊 Hisobot": f"Maqsadlar: {len(data['goals'])} ta, Vazifalar: {len(data['tasks'])} ta, Sarflangan: {data['budget']['spent']:,} so'm. Qisqa motivatsion xabar yoz.",
    }

    if text == "💬 Suhbat":
        await update.message.reply_text("Xo'sh, nima haqida suhbatlashamiz? Savolingizni yozing!")
        return

    prompt = prompts.get(text, text)
    
    # ask_gemini funksiyasi kodingizda qanday yozilganiga qarab chaqiriladi
    # Agar u asinxron bo'lsa (async def), "await ask_gemini(...)" deb yozish kerak
    response = ask_gemini(user_id, prompt)
    await update.message.reply_text(response)

def main():
    print("🚀 Bot ishga tushmoqda...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Handlers (Buyruqlar va xabarlarni tutib olish)
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("add_task", add_task))
    app.add_handler(CommandHandler("add_goal", add_goal))
    app.add_handler(CommandHandler("budget", set_budget))
    app.add_handler(CommandHandler("spent", spent_money))
    app.add_handler(CommandHandler("clear_tasks", clear_tasks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("✅ Bot tayyor va ishlamoqda!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
