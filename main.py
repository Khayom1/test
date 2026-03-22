import os
import httpx
import threading
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client

# ========== ВЕБ-СЕРВЕР БАРОИ RAILWAY (HEALTH CHECK) ==========
app_flask = Flask(__name__)

@app_flask.route('/')
def health_check():
    return "Bot is running", 200

def run_flask():
    # Railway ба таври автоматӣ портро дар тағирёбандаи PORT мефиристад
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

# ========== ТАНЗИМОТИ БОТ ==========
# Тавсия мешавад инҳоро дар Railway Variables гузоред
BOT_TOKEN = "8628746700:AAE2ue_5X3WqR8P53rLGwsVlyM6tZT8WiVI"
SUPABASE_URL = "https://dwjgughlyefxkfpqnekc.supabase.co"
SUPABASE_KEY = "sb_publishable_J-gOSzG40A3ulv6Wa6htHw_6f6A6cv7"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

user_photos = {}
WIKI_BASE_URL = "https://www.playdeltaforce.com/act/officialwiki/ru/"

# ========== ФУНКСИЯҲОИ ЁРИДИҲАНДА ==========
async def fetch_wiki(topic: str = ""):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{WIKI_BASE_URL}{topic}" if topic else WIKI_BASE_URL
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.text[:4000]
            return f"❌ Маълумот ёфт нашуд."
    except Exception as e:
        return f"⚠️ Хатогӣ: {e}"

# ========== ФАРМОНҲО ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Delta Force TJ Bot** фаъол шуд!\n\n"
        "/status - Маълумоти шахсӣ\n"
        "/wiki [мавзӯъ] - Маълумот аз Wiki\n"
        "/top - Рӯйхати аъзоён\n"
        "/alive - Санҷиши бот",
        parse_mode="Markdown"
    )

async def alive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = 0
    try:
        res = supabase.table('members').select('id', count='exact').execute()
        count = res.count if res.count else 0
    except: pass
    
    await update.message.reply_text(
        f"🟢 **Бот дар Railway фаъол аст!**\n"
        f"🕐 Вақт: `{datetime.now().strftime('%H:%M:%S')}`\n"
        f"👥 Аъзоён дар база: {count}",
        parse_mode="Markdown"
    )

async def wiki(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Истифода: `/wiki weapons`", parse_mode="Markdown")
        return
    
    topic = context.args[0].lower()
    await update.message.reply_text(f"🔄 Ҷустуҷӯи {topic}...")
    
    try:
        cached = supabase.table("wiki_cache").select("content").eq("topic", topic).execute()
        if cached.data:
            content = cached.data[0]["content"]
        else:
            content = await fetch_wiki(topic)
            supabase.table("wiki_cache").upsert({
                "topic": topic, "content": content, "updated_at": datetime.now().isoformat()
            }).execute()
        
        await update.message.reply_text(f"📖 **Wiki: {topic}**\n\n{content[:3800]}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Хатогӣ: {e}")

async def handle_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.effective_chat.type == 'private': return

    if user_id not in user_photos: user_photos[user_id] = []
    if update.message.photo: user_photos[user_id].append(update.message.photo[-1].file_id)
    
    caption = update.message.caption or ""
    if "#NICK-ID" in caption:
        parts = caption.replace("#NICK-ID", "").strip().split()
        if len(parts) >= 2:
            context.user_data["nickname"], context.user_data["uid"] = parts[0], parts[1]

    if len(user_photos.get(user_id, [])) >= 4:
        nick, uid = context.user_data.get("nickname"), context.user_data.get("uid")
        if nick and uid and nick.startswith("TJ丶"):
            supabase.table("members").upsert({
                "tg_user_id": user_id, "tg_username": update.effective_user.username,
                "nickname": nick, "uid": uid
            }).execute()
            await update.message.reply_text(f"✅ Сабт шуд: {nick}")
        user_photos[user_id] = []
        context.user_data.clear()

# ========== ОҒОЗ ==========
def main():
    # 1. Оғози веб-сервер дар риштаи алоҳида (Background thread)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 2. Танзими бот
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alive", alive))
    app.add_handler(CommandHandler("wiki", wiki))
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.GROUPS, handle_photos))
    
    print("🚀 Бот ва Веб-сервер оғоз шуданд...")
    app.run_polling()

if __name__ == "__main__":
    main()
