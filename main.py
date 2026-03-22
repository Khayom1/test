import os
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client

# Мутағйирҳои муҳит (дар Railway гузошта мешаванд)
BOT_TOKEN = os.getenv("8628746700:AAE2ue_5X3WqR8P53rLGwsVlyM6tZT8WiVI")
SUPABASE_URL = os.getenv("dwjgughlyefxkfpqnekc")
SUPABASE_KEY = os.getenv("sb_publishable_J-gOSzG40A3ulv6Wa6htHw_6f6A6cv7")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Захираи муваққатӣ барои скриншотҳо
user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 **Delta Force Tajikistan Bot**\n\n"
        "Барои сабти ном дар клан:\n"
        "1. Номи бозигари худро ба **TJ丶Ном** иваз кунед\n"
        "2. 4 скриншотро якҷоя фиристед:\n"
        "   • Профиль\n"
        "   • Операции\n"
        "   • Сражения\n"
        "   • Сведения\n\n"
        "3. Дар матни паём нависед:\n"
        "`#NICK-ID TJ丶Ном ва id`\n\n"
        "Мисол:\n"
        "`#NICK-ID TJ丶Alex 1234567897284692`",
        parse_mode="Markdown"
    )

async def handle_screenshots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Танҳо дар гурӯҳ кор мекунад
    if chat_id > 0:
        return
    
    # Инициализатсияи маълумоти корбар
    if user_id not in user_data_store:
        user_data_store[user_id] = {
            "photos": [],
            "nickname": None,
            "uid": None
        }
    
    # Захираи фото
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        user_data_store[user_id]["photos"].append(file_id)
        
        # Захира дар Supabase
        supabase.table("screenshots").insert({
            "tg_user_id": user_id,
            "file_id": file_id,
            "screenshot_type": f"photo_{len(user_data_store[user_id]['photos'])}"
        }).execute()
    
    # Санҷиши матн
    caption = update.message.caption or ""
    if "#NICK-ID" in caption:
        parts = caption.replace("#NICK-ID", "").strip().split()
        if len(parts) >= 2:
            user_data_store[user_id]["nickname"] = parts[0]
            user_data_store[user_id]["uid"] = parts[1]
    
    # Агар 4 фото ҷамъ шуд
    if len(user_data_store[user_id]["photos"]) >= 4:
        nickname = user_data_store[user_id]["nickname"]
        uid = user_data_store[user_id]["uid"]
        
        if not nickname or not uid:
            await update.message.reply_text(
                "❌ **Хатогӣ!**\n\n"
                "Формати матн нодуруст аст.\n"
                "Лутфан нависед: `#NICK-ID TJ丶Ном 123456789`",
                parse_mode="Markdown"
            )
            user_data_store[user_id] = {"photos": [], "nickname": None, "uid": None}
            return
        
        # Санҷиши теги TJ丶
        if not nickname.startswith("TJ丶"):
            await update.message.reply_text(
                "⚠️ **Номи бозингар нодуруст!**\n\n"
                f"Номи шумо: `{nickname}`\n"
                "Бояд бо `TJ丶` оғоз шавад.\n\n"
                "Номи худро дар бозӣ тағйир диҳед ва дубора сабти ном кунед.",
                parse_mode="Markdown"
            )
            user_data_store[user_id] = {"photos": [], "nickname": None, "uid": None}
            return
        
        # Санҷиш, ки оё корбар аллакай сабт шудааст
        existing = supabase.table("members").select("*").eq("tg_user_id", user_id).execute()
        if existing.data:
            await update.message.reply_text(
                f"✅ **Шумо аллакай сабт шудаед!**\n\n"
                f"Ном: `{existing.data[0]['nickname']}`\n"
                f"UID: `{existing.data[0]['uid']}`",
                parse_mode="Markdown"
            )
        else:
            # Сабти корбар
            supabase.table("members").insert({
                "tg_user_id": user_id,
                "tg_username": update.effective_user.username,
                "nickname": nickname,
                "uid": uid,
                "screenshots_received": True,
                "status": "active",
                "last_activity": datetime.now().isoformat()
            }).execute()
            
            await update.message.reply_text(
                f"✅ **Сабти ном муваффақ!**\n\n"
                f"Хуш омадед, {nickname}!\n"
                f"UID: `{uid}`\n\n"
                f"Акнун шумо аъзои расмии клан ҳастед.",
                parse_mode="Markdown"
            )
        
        # Тоза кардани маълумоти муваққатӣ
        user_data_store[user_id] = {"photos": [], "nickname": None, "uid": None}

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    result = supabase.table("members").select("*").eq("tg_user_id", user_id).execute()
    
    if not result.data:
        await update.message.reply_text(
            "❌ Шумо ҳанӯз сабти ном накардаед.\n"
            "Барои сабти ном фармони /start-ро истифода баред."
        )
        return
    
    member = result.data[0]
    await update.message.reply_text(
        f"📊 **Маълумоти шумо**\n\n"
        f"👤 Ном: `{member['nickname']}`\n"
        f"🆔 UID: `{member['uid']}`\n"
        f"📅 Санаи сабт: `{member['joined_at'][:10]}`\n"
        f"✅ Вазъият: `{member['status']}`",
        parse_mode="Markdown"
    )

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Барои версияи сода, танҳо рӯйхати аъзоён
    result = supabase.table("members").select("nickname, uid").eq("status", "active").execute()
    
    if not result.data:
        await update.message.reply_text("Ҳанӯз аъзое нест.")
        return
    
    text = "🏆 **Рӯйхати аъзоёни клан**\n\n"
    for i, member in enumerate(result.data[:10], 1):
        text += f"{i}. {member['nickname']} (`{member['uid']}`)\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.GROUPS, handle_screenshots))
    
    print("🤖 Бот ба кор оғоз кард...")
    app.run_polling()

if __name__ == "__main__":
    main()
