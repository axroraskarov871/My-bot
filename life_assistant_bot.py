import os
import logging
import random
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
YOUR_CITY = os.getenv("CITY", "Tashkent")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
# ... pastki qatorlar davom etadi
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

user_data = {}

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"goals": [], "tasks": [], "budget": {"limit": 0, "spent": 0}}
    return user_data[user_id]

SYSTEM_PROMPT = """Sen o'zbek tilida gaplashadigan shaxsiy hayot assistentisan.
Kunlik rejalashtirish, ovqat, pul tejash, ob-havo, life hacklar, motivatsiya sohasida yordam berasan.
Har doim qisqa, aniq va amaliy javob ber."""

def ask_gemini(user_id: int, message: str) -> str:
    try:
        data = get_user(user_id)
        goals_text = ", ".join(data["goals"]) if data["goals"] else "belgilanmagan"
        tasks_text = ", ".join(data["tasks"]) if data["tasks"] else "yo'q"
        full_prompt = f"""{SYSTEM_PROMPT}
Foydalanuvchi ma'lumotlari:
- Maqsadlar: {goals_text}
- Vazifalar: {tasks_text}
- Bugun: {datetime.now().strftime('%A, %d %B %Y, %H:%M')}
Savol: {message}"""
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini xatosi: {e}")
        return f"Xatolik yuz berdi: {str(e)}"

def main_keyboard():
    keyboard = [
        [KeyboardButton("🌤 Ob-havo"), KeyboardButton("👔 Kiyinish")],
        [KeyboardButton("🥗 Ovqat"), KeyboardButton("💰 Pul tejash")],
        [KeyboardButton("📋 Vazifalar"), KeyboardButton("🎯 Maqsadlar")],
        [KeyboardButton("💡 Life hack"), KeyboardButton("🧠 Muammo hal")],
        [KeyboardButton("📊 Hisobot"), KeyboardButton("💬 Suhbat")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"Salom, {name}! 👋\n\nMen sizning shaxsiy hayot assistentingizman.\n\n"
        "Har kuni sizga yordam beraman:\n🌤 Ob-havo & kiyinish\n🥗 Ovqat tavsiyasi\n"
        "💰 Pul tejash\n📋 Vazifa & maqsadlar\n💡 Life hacklar\n🧠 Kunlik muammo hal qilish\n\n"
        "Boshlaylik! Quyidagi tugmalardan foydalaning 👇",
        reply_markup=main_keyboard()
    )

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.args:
        task = " ".join(context.args)
        get_user(user_id)["tasks"].append(task)
        await update.message.reply_text(f"✅ Vazifa qo'shildi: {task}")
    else:
        await update.message.reply_text("Misol: /add_task Kitob o'qish")

async def add_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.args:
        goal = " ".join(context.args)
        get_user(user_id)["goals"].append(goal)
        await update.message.reply_text(f"🎯 Maqsad qo'shildi: {goal}")
    else:
        await update.message.reply_text("Misol: /add_goal 5M so'm jamg'arish")

async def set_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.args:
        try:
            amount = int(context.args[0])
            get_user(user_id)["budget"]["limit"] = amount
            await update.message.reply_text(f"💰 Kunlik byudjet: {amount:,} so'm")
        except:
            await update.message.reply_text("Misol: /budget 100000")

async def spent_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user(user_id)
    if context.args:
        try:
            amount = int(context.args[0])
            data["budget"]["spent"] += amount
            remaining = data["budget"]["limit"] - data["budget"]["spent"]
            msg = f"💸 {amount:,} so'm sarflandi\n📊 Jami: {data['budget']['spent']:,} so'm"
            if data["budget"]["limit"] > 0:
                msg += f"\n✅ Qolgan: {remaining:,} so'm"
            await update.message.reply_text(msg)
        except:
            await update.message.reply_text("Misol: /spent 50000")

async def clear_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_user(update.effective_user.id)["tasks"] = []
    await update.message.reply_text("✅ Vazifalar tozalandi!")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    data = get_user(user_id)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    hour = datetime.now().hour
    meal = "nonushta" if hour < 11 else "tushlik" if hour < 15 else "kechki ovqat"
    month = datetime.now().strftime('%B')
    season = "qish" if datetime.now().month in [12,1,2] else "bahor" if datetime.now().month in [3,4,5] else "yoz" if datetime.now().month in [6,7,8] else "kuz"

    prompts = {
        "🌤 Ob-havo": f"{YOUR_CITY}da {month} oyida ob-havo qanday? Qisqa ayt.",
        "👔 Kiyinish": f"{YOUR_CITY}da {season}da qanday kiyinish kerak? Erkak va ayol uchun.",
        "🥗 Ovqat": f"Bugun {meal} uchun 3 ta sog'lom va arzon tavsiya ber.",
        "💰 Pul tejash": "O'zbekistonda pul tejash bo'yicha 3 ta amaliy maslahat ber.",
        "📋 Vazifalar": f"Mening vazifalarim: {', '.join(data['tasks']) or 'yo`q'}. Qanday samarali bajaraman?",
        "🎯 Maqsadlar": f"Mening maqsadlarim: {', '.join(data['goals']) or 'yo`q'}. Bugun nima qilaman?",
        "💡 Life hack": "Bugun uchun bitta foydali life hack ber.",
        "🧠 Muammo hal": "Bugun uchun bitta amaliy muammo va uning yechimini ber.",
        "📊 Hisobot": f"Maqsadlar: {len(data['goals'])} ta, Vazifalar: {len(data['tasks'])} ta, Sarflangan: {data['budget']['spent']:,} so'm. Qisqa motivatsion xabar yoz.",
    }

    if text == "💬 Suhbat":
        await update.message.reply_text("Xo'sh, nima haqida suhbatlashamiz? Savolingizni yozing!")
        return

    prompt = prompts.get(text, text)
    response = ask_gemini(user_id, prompt)
    await update.message.reply_text(response)

def main():
    print("🚀 Bot ishga tushmoqda...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("add_task", add_task))
    app.add_handler(CommandHandler("add_goal", add_goal))
    app.add_handler(CommandHandler("budget", set_budget))
    app.add_handler(CommandHandler("spent", spent_money))
    app.add_handler(CommandHandler("clear_tasks", clear_tasks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("✅ Bot tayyor!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

