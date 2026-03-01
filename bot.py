import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# .env ফাইল থেকে ডেটা লোড করা
load_dotenv()

# ভেরিয়েবলগুলো সেট করা
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Gemini কনফিগারেশন
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest') # স্টেবল ভার্সন

# ইউজার চ্যাট মেমরি
chat_sessions = {}

# লগিং সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_sessions[user_id] = model.start_chat(history=[])
    await update.message.reply_text("বট সচল হয়েছে! এখন প্রশ্ন করুন।")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in chat_sessions:
        chat_sessions[user_id] = model.start_chat(history=[])

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Gemini থেকে রেসপন্স নেওয়া
        response = chat_sessions[user_id].send_message(user_text)
        
        await update.message.reply_text(response.text)
        
    except Exception as e:
        logging.error(f"Error: {e}")
        # যদি ৪২৯ এরর আসে (লিমিট শেষ), তবে ইউজারকে জানানো
        if "429" in str(e):
            await update.message.reply_text("দুঃখিত, ফ্রি লিমিট শেষ। কিছুক্ষণ পর চেষ্টা করুন।")
        else:
            await update.message.reply_text("সাময়িক সমস্যা হচ্ছে।")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("বটটি রান হচ্ছে...")

    application.run_polling()
