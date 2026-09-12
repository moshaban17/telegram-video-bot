import os
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


BOT_TOKEN = os.getenv("BOT_TOKEN")
GH_TOKEN = os.getenv("GH_TOKEN")

GITHUB_OWNER = "moshaban17"
GITHUB_REPO = "telegram-video-bot"
WORKFLOW_FILE = "process.yml"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 ابعتلي رابط الفيلم المباشر.\n\n"
        "بعدها هختار لك الدقة."
    )


async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not (
        url.startswith("http://")
        or url.startswith("https://")
    ):
        await update.message.reply_text(
            "❌ ابعت رابط يبدأ بـ http:// أو https://"
        )
        return

    context.user_data["video_url"] = url

    keyboard = [
        [
            InlineKeyboardButton("نفس الدقة", callback_data="res_same"),
            InlineKeyboardButton("1080p", callback_data="res_1080"),
        ],
        [
            InlineKeyboardButton("720p", callback_data="res_720"),
            InlineKeyboardButton("480p", callback_data="res_480"),
        ],
        [
            InlineKeyboardButton("360p", callback_data="res_360"),
        ],
    ]

    await update.message.reply_text(
        "🎬 اختار الدقة المطلوبة:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def choose_resolution(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    video_url = context.user_data.get("video_url")

    if not video_url:
        await query.edit_message_text(
            "❌ رابط الفيلم غير موجود. ابعت الرابط من جديد."
        )
        return

    resolutions = {
        "res_same": "same",
        "res_1080": "1080p",
        "res_720": "720p",
        "res_480": "480p",
        "res_360": "360p",
    }

    resolution = resolutions.get(query.data)

    if not resolution:
        await query.edit_message_text("❌ اختيار غير صالح.")
        return

    chat_id = update.effective_chat.id

    await query.edit_message_text(
        f"⏳ جاري تجهيز الفيلم...\n\n"
        f"🎬 الدقة: {resolution}\n"
        f"📥 التحميل والمعالجة هتتم على GitHub، مش على موبايلك."
    )

    if not GH_TOKEN:
        await query.message.reply_text(
            "❌ GH_TOKEN غير موجود في بيئة تشغيل البوت."
        )
        return

    api_url = (
        f"https://api.github.com/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/"
        f"{WORKFLOW_FILE}/dispatches"
    )

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GH_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    data = {
        "ref": "main",
        "inputs": {
            "video_url": video_url,
            "subtitle_url": "",
            "resolution": resolution,
            "chat_id": str(chat_id),
        },
    }

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=data,
            timeout=30,
        )

        if response.status_code == 204:
            await query.message.reply_text(
                "✅ بدأ تحميل الفيلم ومعالجته.\n\n"
                "📤 لما يخلص، الفيلم هيتبعت هنا تلقائيًا."
            )
        else:
            await query.message.reply_text(
                "❌ حصل خطأ أثناء تشغيل المعالجة.\n"
                f"كود الخطأ: {response.status_code}\n"
                f"{response.text[:500]}"
            )

    except Exception as e:
        await query.message.reply_text(
            f"❌ حصل خطأ في الاتصال بـ GitHub:\n{e}"
        )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN غير موجود")

    if not GH_TOKEN:
        raise RuntimeError("GH_TOKEN غير موجود")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_link,
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            choose_resolution,
            pattern=r"^res_"
        )
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
