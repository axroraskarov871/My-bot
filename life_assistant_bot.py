# ============================================================
# SHAXSIY HAYOT ASSISTENTI BOT
# Gemini AI + Telegram
# ============================================================
# O'rnatish: pip install python-telegram-bot google-generativeai python-dotenv requests
# Ishga tushirish: python life_assistant_bot.py
# ============================================================

import os
import logging
import json
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

# ============================================================
# SOZLAMALAR — shu yerga o'z tokenlaringizni kiriting
# ============================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "BU_YERGA_TELEGRAM_TOKENINGIZ")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "BU_YERGA_GEMINI_API_KEYINGIZ")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")  # openweathermap.org dan bepul oling
YOUR_CITY = os.getenv("CITY", "Tashkent")  # Shahringizni yozing

# ============================================================
# GEMINI SOZLASH
# ============================================================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================
# FOYDALANUVCHI MA'LUMOTLARINI SAQLASH (xotira)
# ============================================================
user_data = {}  # {user_id: {goals, tasks, budget, notes, chat_history}}

def get_user(user_id):
    """Foydalanuvchi ma'lumotlarini olish yoki yaratish"""
    if user_id not in user_data:
        user_data[user_id] = {
            "goals": [],
            "tasks": [],
            "budget": {"limit": 0, "spent": 0},
            "notes": [],
            "chat_history": [],
            "profile": {}
        }
    return user_data[user_id]

# ============================================================
# GEMINI BILAN SUHBAT
# ============================================================

SYSTEM_PROMPT = """Sen o'zbek tilida gaplashadigan shaxsiy hayot assistentisan.
Foydalanuvchiga quyidagi sohalarda yordam berasan:
- Kunlik rejalashtirish va maqsadlar
- Sog'lom ovqatlanish tavsiyalari
- Pul tejash va moliyaviy maslahatlar
- Ob-havo asosida kiyinish tavsiyasi
- Hayotiy life hacklar va foydali ma'lumotlar
- Sotuvchilik va biznes maslahatlari
- Kunlik muammo hal qilish (growth mindset)
- Motivatsiya va ruhiy ko'tarinkilik

Har doim:
- Qisqa, aniq va amaliy javob ber
- O'zbek tilida gapir
- Ijobiy va motivatsion bo'l
- Amaliy maslahat ber
"""

def ask_gemini(user_id: int, message: str, context_info: str = "") -> str:
    """Gemini dan javob olish"""
    try:
        data = get_user(user_id)
        
        # Kontekst ma'lumotlarini qo'shish
        goals_text = ", ".join(data["goals"]) if data["goals"] else "belgilanmagan"
        tasks_text = ", ".join(data["tasks"]) if data["tasks"] else "yo'q"
        
        full_prompt = f"""{SYSTEM_PROMPT}

Foydalanuvchi ma'lumotlari:
- Maqsadlar: {goals_text}
- Bugungi vazifalar: {tasks_text}
- Bugun: {datetime.now().strftime('%A, %d %B %Y, %H:%M')}
{context_info}

Foydalanuvchi: {message}"""

        response = model.generate_content(full_prompt)
        return response.text
        
    except Exception as e:
        logger.error(f"Gemini xatosi: {e}")
        return "Uzr, hozir javob bera olmayapman. Qayta urinib ko'ring."

# ============================================================
# KEYBOARD (tugmalar)
# ============================================================

def main_keyboard():
    """Asosiy menyu tugmalari"""
    keyboard = [
        [KeyboardButton("🌤 Ob-havo"), KeyboardButton("👔 Kiyinish")],
        [KeyboardButton("🥗 Ovqat"), KeyboardButton("💰 Pul tejash")],
        [KeyboardButton("📋 Vazifalar"), KeyboardButton("🎯 Maqsadlar")],
        [KeyboardButton("💡 Life hack"), KeyboardButton("🧠 Muammo hal")],
        [KeyboardButton("📊 Hisobot"), KeyboardButton("💬 Suhbat")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ============================================================
# HANDLERLAR
# ============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start"""
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    get_user(user_id)  # Yaratish
    
    text = f"""Salom, {name}! 👋

Men sizning shaxsiy hayot assistentingizman.

Har kuni sizga yordam beraman:
🌤 Ob-havo & kiyinish
🥗 Ovqat tavsiyasi  
💰 Pul tejash
📋 Vazifa & maqsadlar
💡 Life hacklar
🧠 Kunlik muammo hal qilish

Boshlaylik! Quyidagi tugmalardan foydalaning 👇"""
    
    await update.message.reply_text(text, reply_markup=main_keyboard())


async def handle_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ob-havo ma'lumoti"""
    user_id = update.effective_user.id
    
    # Agar OpenWeather API key bo'lsa — real ob-havo
    if WEATHER_API_KEY:
        try:
            import requests
            url = f"http://api.openweathermap.org/data/2.5/weather?q={YOUR_CITY}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
            r = requests.get(url, timeout=5)
            data = r.json()
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            
            weather_info = f"Hozirgi ob-havo {YOUR_CITY}da: {temp}°C, {desc}, namlik {humidity}%"
            
            prompt = f"{weather_info}\n\nBu ob-havo asosida bugun qanday kiyinish kerak? Qisqa va amaliy maslahat ber."
            response = ask_gemini(user_id, prompt)
            await update.message.reply_text(f"🌤 {weather_info}\n\n👔 {response}")
            
        except Exception as e:
            await update.message.reply_text(
                "Ob-havo ma'lumotini ololmadim. Shahringizni va ob-havoni yozing, maslahat beraman!"
            )
    else:
        # API key yo'q bo'lsa Gemini dan so'rash
        prompt = f"Bugun {YOUR_CITY}da taxminiy ob-havo qanday bo'lishi mumkin ({datetime.now().strftime('%B')})? Va qanday kiyinish kerak?"
        response = ask_gemini(user_id, prompt)
        await update.message.reply_text(f"🌤 {response}\n\n💡 *Real ob-havo uchun openweathermap.org dan bepul API key oling*")


async def handle_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ovqat tavsiyasi"""
    user_id = update.effective_user.id
    hour = datetime.now().hour
    
    if hour < 11:
        meal = "nonushta"
    elif hour < 15:
        meal = "tushlik"
    else:
        meal = "kechki ovqat"
    
    prompt = f"Bugun {meal} uchun sog'lom, arzon va o'zbek mahsulotlaridan tayyorlanadigan 3 ta tavsiya ber. Kaloriyasini ham yoz."
    response = ask_gemini(user_id, prompt)
    await update.message.reply_text(f"🥗 Bugungi {meal} tavsiyasi:\n\n{response}")


async def handle_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pul tejash"""
    user_id = update.effective_user.id
    data = get_user(user_id)
    
    spent = data["budget"]["spent"]
    limit = data["budget"]["limit"]
    
    prompt = f"""Pul tejash bo'yicha bugungi amaliy maslahat ber.
Agar limit belgilangan bo'lsa: {limit} so'm, sarflangan: {spent} so'm.
O'zbekistonda amalda ishlatiladigan 3 ta konkret life hack ber."""
    
    response = ask_gemini(user_id, prompt)
    
    budget_text = ""
    if limit > 0:
        remaining = limit - spent
        budget_text = f"\n💳 Bugun sarflangan: {spent:,} so'm\n✅ Qolgan: {remaining:,} so'm\n\n"
    
    await update.message.reply_text(f"💰 Pul tejash maslahati:\n{budget_text}{response}")


async def handle_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Vazifalar"""
    user_id = update.effective_user.id
    data = get_user(user_id)
    
    if data["tasks"]:
        tasks_text = "\n".join([f"☐ {t}" for t in data["tasks"]])
        prompt = f"Menda bugun quyidagi vazifalar bor:\n{tasks_text}\n\nBularni qanday tartibda va samarali bajarishim mumkin? Qisqa maslahat ber."
        response = ask_gemini(user_id, prompt)
        await update.message.reply_text(
            f"📋 Bugungi vazifalaringiz:\n{tasks_text}\n\n💡 Maslahat:\n{response}\n\n"
            f"Vazifa qo'shish uchun: /add_task [vazifa nomi]\n"
            f"Tozalash uchun: /clear_tasks"
        )
    else:
        await update.message.reply_text(
            "📋 Hali vazifa yo'q.\n\nQo'shish uchun:\n/add_task Kitob o'qish\n/add_task Sport qilish"
        )


async def handle_goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maqsadlar"""
    user_id = update.effective_user.id
    data = get_user(user_id)
    
    if data["goals"]:
        goals_text = "\n".join([f"🎯 {g}" for g in data["goals"]])
        prompt = f"Mening maqsadlarim:\n{goals_text}\n\nBugun shu maqsadlarga yaqinlashish uchun nima qilishim mumkin? 3 ta konkret qadam ber."
        response = ask_gemini(user_id, prompt)
        await update.message.reply_text(
            f"🎯 Maqsadlaringiz:\n{goals_text}\n\n✅ Bugungi qadamlar:\n{response}\n\n"
            f"Maqsad qo'shish: /add_goal [maqsad]"
        )
    else:
        await update.message.reply_text(
            "🎯 Hali maqsad belgilanmagan.\n\nQo'shish uchun:\n/add_goal 3 oy ichida 5M so'm jamg'arish\n/add_goal Ingliz tilini o'rganish"
        )


async def handle_lifehack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kunlik life hack"""
    user_id = update.effective_user.id
    
    categories = [
        "vaqtni boshqarish va produktivlik",
        "sog'liq va energiya",
        "pul tejash va moliya",
        "o'rganish va rivojlanish",
        "muloqot va munosabatlar",
        "ish va karyer"
    ]
    category = random.choice(categories)
    
    prompt = f"{category} bo'yicha bugun bitta ajoyib va kam ma'lum life hack ber. Amaliy va O'zbekistonda qo'llanishi mumkin bo'lsin."
    response = ask_gemini(user_id, prompt)
    await update.message.reply_text(f"💡 Bugungi Life Hack ({category}):\n\n{response}")


async def handle_problem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kunlik muammo hal qilish"""
    user_id = update.effective_user.id
    
    prompt = f"""Bugun {datetime.now().strftime('%A')} kuni uchun bitta amaliy muammo yoki vaziyat ber va uni qanday hal qilish kerakligini tushuntir.
Bu inson o'sishiga yordam bersin. Growth mindset asosida yondashuv qo'lla.
Misol: "Tanqidga qanday munosabatda bo'lish kerak?" kabi mavzu."""
    
    response = ask_gemini(user_id, prompt)
    await update.message.reply_text(f"🧠 Bugungi muammo & yechim:\n\n{response}")


async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kunlik hisobot"""
    user_id = update.effective_user.id
    data = get_user(user_id)
    
    goals = len(data["goals"])
    tasks = len(data["tasks"])
    spent = data["budget"]["spent"]
    limit = data["budget"]["limit"]
    
    report = f"""📊 Sizning hisobotingiz:

🎯 Maqsadlar: {goals} ta
📋 Bugungi vazifalar: {tasks} ta
💰 Sarflangan: {spent:,} so'm"""
    
    if limit > 0:
        report += f"\n💳 Kunlik limit: {limit:,} so'm"
        report += f"\n✅ Qolgan: {(limit-spent):,} so'm"
    
    prompt = f"Foydalanuvchining bugungi holati: {goals} maqsad, {tasks} vazifa. Qisqa motivatsion xabar yoz va bugun yana nima qilishi mumkinligini ayt."
    motivation = ask_gemini(user_id, prompt)
    
    await update.message.reply_text(f"{report}\n\n💬 {motivation}")


async def handle_dress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kiyinish tavsiyasi"""
    user_id = update.effective_user.id
    month = datetime.now().month
    
    if month in [12, 1, 2]:
        season = "qish"
    elif month in [3, 4, 5]:
        season = "bahor"
    elif month in [6, 7, 8]:
        season = "yoz"
    else:
        season = "kuz"
    
    prompt = f"{season} mavsumida {YOUR_CITY}da bugun qanday kiyinish kerak? Erkaklar va ayollar uchun alohida maslahat ber. Amaliy va oddiy."
    response = ask_gemini(user_id, prompt)
    await update.message.reply_text(f"👔 Bugungi kiyinish tavsiyasi ({season}):\n\n{response}")


# ============================================================
# MAXSUS BUYRUQLAR
# ============================================================

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/add_task"""
    user_id = update.effective_user.id
    data = get_user(user_id)
    
    if context.args:
        task = " ".join(context.args)
        data["tasks"].append(task)
        await update.message.reply_text(f"✅ Vazifa qo'shildi: {task}\n\nJami vazifalar: {len(data['tasks'])} ta")
    else:
        await update.message.reply_text("Vazifa nomini yozing:\n/add_task Kitob o'qish")


async def add_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/add_goal"""
    user_id = update.effective_user.id
    data = get_user(user_id)
    
    if context.args:
        goal = " ".join(context.args)
        data["goals"].append(goal)
        await update.message.reply_text(f"🎯 Maqsad qo'shildi: {goal}\n\nJami maqsadlar: {len(data['goals'])} ta")
    else:
        await update.message.reply_text("Maqsadni yozing:\n/add_goal 3 oy ichida 5M so'm jamg'arish")


async def set_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/budget"""
    user_id = update.effective_user.id
    data = get_user(user_id)
    
    if context.args:
        try:
            amount = int(context.args[0])
            data["budget"]["limit"] = amount
            await update.message.reply_text(f"💰 Kunlik byudjet belgilandi: {amount:,} so'm")
        except:
            await update.message.reply_text("Miqdorni to'g'ri yozing:\n/budget 100000")
    else:
        await update.message.reply_text("Kunlik byudjetni yozing:\n/budget 100000")


async def spent_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/spent"""
    user_id = update.effective_user.id
    data = get_user(user_id)
    
    if context.args:
        try:
            amount = int(context.args[0])
            data["budget"]["spent"] += amount
            remaining = data["budget"]["limit"] - data["budget"]["spent"]
            
            msg = f"💸 {amount:,} so'm sarflandi\n📊 Jami sarflangan: {data['budget']['spent']:,} so'm"
            if data["budget"]["limit"] > 0:
                msg += f"\n✅ Qolgan: {remaining:,} so'm"
                if remaining < 0:
                    msg += f"\n⚠️ Limitdan {abs(remaining):,} so'm oshib ketdi!"
            
            await update.message.reply_text(msg)
        except:
            await update.message.reply_text("Miqdorni to'g'ri yozing:\n/spent 50000")


async def clear_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/clear_tasks"""
    user_id = update.effective_user.id
    get_user(user_id)["tasks"] = []
    await update.message.reply_text("✅ Vazifalar tozalandi!")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Oddiy matn — Gemini ga yuborish"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Tugma bosilsa
    if text == "🌤 Ob-havo":
        await handle_weather(update, context)
    elif text == "👔 Kiyinish":
        await handle_dress(update, context)
    elif text == "🥗 Ovqat":
        await handle_food(update, context)
    elif text == "💰 Pul tejash":
        await handle_money(update, context)
    elif text == "📋 Vazifalar":
        await handle_tasks(update, context)
    elif text == "🎯 Maqsadlar":
        await handle_goals(update, context)
    elif text == "💡 Life hack":
        await handle_lifehack(update, context)
    elif text == "🧠 Muammo hal":
        await handle_problem(update, context)
    elif text == "📊 Hisobot":
        await handle_report(update, context)
    elif text == "💬 Suhbat":
        await update.message.reply_text("Xo'sh, nima haqida suhbatlashamiz? Savolingizni yozing!")
    else:
        # Erkin suhbat
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        response = ask_gemini(user_id, text)
        await update.message.reply_text(response)


# ============================================================
# ASOSIY FUNKSIYA
# ============================================================

def main():
    print("🚀 Shaxsiy Hayot Assistenti ishga tushmoqda...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Buyruqlar
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("add_task", add_task))
    app.add_handler(CommandHandler("add_goal", add_goal))
    app.add_handler(CommandHandler("budget", set_budget))
    app.add_handler(CommandHandler("spent", spent_money))
    app.add_handler(CommandHandler("clear_tasks", clear_tasks))
    
    # Matn xabarlari
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("✅ Bot tayyor! Telegramda /start bosing")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
