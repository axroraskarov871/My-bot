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

# Gemini modelini sozlash (Eski kutubxonalarda ham ishlovchi eng barqaror variant)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.0-pro")

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

async def ask_gemini(user_id: int, message: str) -> str:
    try:
        data = get_user(user_id)
        goals_text = ", ".join(data["goals"]) if data["goals"] else "belgilanmagan"
        tasks_text = ", ".join(data["tasks"]) if data["tasks"] else "yo'q"
        
        full_prompt = f"{SYSTEM_PROMPT}\n\nFoydalanuvchi maqsadlari: {goals_text}\nVazifalari: {tasks_text}\n\nSavol: {message}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini xatoligi: {e}")
        return f"Xatolik yuz berdi: {e}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user(user_id)
    
    keyboard = [
        [KeyboardButton("🌤 Ob-havo"), KeyboardButton("👔 Kiyinish")],
        [KeyboardButton("🥗 Ovqat"), KeyboardButton("💰 Pul tejash")],
        [KeyboardButton("📋 Vazifalar"), KeyboardButton("🎯 Maqsadlar")],
        [KeyboardButton("💡 Life hack"), KeyboardButton("🧠 Muammo hal")],
        [KeyboardButton("📊 Hisobot"), KeyboardButton("💬 Suhbat")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_text = f"Salom, {update.effective_user.first_name}! 👋\nMen sizning shaxsiy yordamchingizman. Quyidagi tugmalardan foydalaning:"
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task = " ".join(context.args)
    if task:
        get_user(user_id)["tasks"].append(task)
        await update.message.reply_text(f"✅ Vazifa qo'shildi: {task}")
    else:
        await update.message.reply_text("❌ Iltimos, /add_task so'zidan keyin vazifani yozing.")

async def add_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    goal = " ".join(context.args)
    if goal:
        get_user(user_id)["goals"].append(goal)
        await update.message.reply_text(f"🎯 Maqsad qo'shildi: {goal}")
    else:
        await update.message.reply_text("❌ Iltimos, /add_goal so'zidan keyin maqsadni yozing.")

async def set_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        limit = int(context.args[0])
        get_user(user_id)["budget"]["limit"] = limit
        await update.message.reply_text(f"💰 Budjet limiti belgilandi: {limit:,} so'm")
    except:
        await update.message.reply_text("❌ Iltimos, /budget so'zidan keyin faqat raqam yozing.")

async def spent_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        amount = int(context.args[0])
        get_user(user_id)["budget"]["spent"] += amount
        await update.message.reply_text(f"📉 {amount:,} so'm xarajat qayd etildi.")
    except:
        await update.message.reply_text("❌ Iltimos, /spent so'zidan keyin faqat raqam yozing.")

async def clear_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user(user_id)["tasks"] = []
    await update.message.reply_text("🗑 Barcha vazifalar o'chirildi.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    data = get_user(user_id)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    hour = datetime.now().hour
    meal = "nonushta" if hour < 11 else "tushlik" if hour < 15 else "kechki ovqat"
    month = datetime.now().strftime('%B')
    season = "qish" if datetime.now().month in [12, 1, 2] else "bahor" if datetime.now().month in [3, 4, 5] else "yoz" if datetime.now().month in [6, 7, 8] else "kuz"

    prompts = {
        "🌤 Ob-havo": f"{YOUR_CITY}da {month} oyida ob-havo qanday? Qisqa va lo'nda ayt.",
        "👔 Kiyinish": f"{YOUR_CITY}da hozirgi {season} faslida erkaklar uchun qanday kiyinish uslubi mos keladi? Amaliy tavsiya ber.",
        "🥗 Ovqat": f"Bugun {meal} uchun o'zbekona, sog'lom va hamyonbop 3 ta taom variantini yoz.",
        "💰 Pul tejash": "Shaxsiy moliya boshqaruvi va pul tejash bo'yicha eng samarali 3 ta oltin qoidani tushuntir.",
        "📋 Vazifalar": f"Mening vazifalarim: {', '.join(data['tasks']) or 'yo`q'}. Bularni strategik jihatdan qanday rejalashtirib bajarsam bo'ladi?",
        "🎯 Maqsadlar": f"Mening maqsadlarim: {', '.join(data['goals']) or 'yo`q'}. Ushbu maqsadlarga erishish uchun bugun tashlanadigan eng muhim qadam nima?",
        "💡 Life hack": "Samaradorlikni oshirish yoki vaqtni tejashga oid bitta kuchli life hack ulash.",
        "🧠 Muammo hal": "Hayotiy muammolarni bartaraf etishda strategik mental modellar (masalan, teskari fikrlash yoki antifragility) qanday yordam beradi? Qisqa misol bilan tushuntir.",
        "📊 Hisobot": f"Maqsadlar: {len(data['goals'])} ta, Vazifalar: {len(data['tasks'])} ta, Umumiy xarajat: {data['budget']['spent']:,} so'm. Strategik va motivatsion hisobot tayyorla.",
    }

    if text == "💬 Suhbat":
        await update.message.reply_text("Eshityapman, nima mavzuda gaplashamiz? Savolingizni erkin yozishingiz mumkin!")
        return

    prompt = prompts.get(text, text)
    response = await ask_gemini(user_id, prompt)
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
    
    print("✅ Bot muvaffaqiyatli tayyorlandi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
