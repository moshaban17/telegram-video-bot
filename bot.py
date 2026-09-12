
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 ابعتلي الفيلم كفيديو أو ملف.\n"
        "الترجمة اختيارية."
    )


async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ استلمت الفيلم.\n"
        "هنضيف هنا اختيارات التحويل بعد تجهيز باقي البوت."
    )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN غير موجود")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, receive_video))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
