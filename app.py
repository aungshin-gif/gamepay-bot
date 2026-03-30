import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello Gamepay Hub မှကြိုဆိုပါတယ် 👋\n"
        "Bot အလုပ်လုပ်နေပါတယ်။"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start ကိုနှိပ်ပြီး bot ကိုစသုံးနိုင်ပါတယ်။"
    )

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found. Set it in Render Environment Variables.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    print("Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
