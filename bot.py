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


def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("🔗 تحميل من رابط", callback_data="download"),
            InlineKeyboardButton("🎬 تحويل دقة", callback_data="convert"),
        ],
        [
            InlineKeyboardButton("📝 حرق ترجمة", callback_data="subtitle"),
            InlineKeyboardButton("🎙️ صوت → SRT", callback_data="speech"),
        ],
        [
            InlineKeyboardButton("🔊 إدارة الصوت", callback_data="audio"),
            InlineKeyboardButton("📦 استخراج ترجمة", callback_data="extract"),
        ],
        [
            InlineKeyboardButton("🖼️ Watermark", callback_data="watermark"),
            InlineKeyboardButton("🔗 ملف → رابط", callback_data="file_link"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 أهلاً بك في بوت معالجة الفيديو.\n\n"
        "اختار الوظيفة المطلوبة:",
        reply_markup=main_menu(),
    )


async def menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "download":
        context.user_data["mode"] = "download"

        await query.edit_message_text(
            "🔗 ابعت الآن رابط الفيديو المباشر.\n\n"
            "📌 هيتم تحميله بنفس الدقة الأصلية بدون تحويل."
        )

    elif query.data == "convert":
        context.user_data["mode"] = "convert"

        await query.edit_message_text(
            "🎬 ابعت رابط الفيديو، وبعدها هتختار الدقة."
        )

    elif query.data == "subtitle":
        await query.edit_message_text(
            "📝 وظيفة حرق الترجمة هتتضاف في الخطوة القادمة."
        )

    elif query.data == "speech":
        await query.edit_message_text(
            "🎙️ تحويل الصوت إلى SRT هيتضاف في الخطوة القادمة."
        )

    elif query.data == "audio":
        await query.edit_message_text(
            "🔊 إدارة مسارات الصوت هتتضاف في الخطوة القادمة."
        )

    elif query.data == "extract":
        await query.edit_message_text(
            "📦 استخراج الترجمة المدمجة هيتضاف في الخطوة القادمة."
        )

    elif query.data == "watermark":
        await query.edit_message_text(
            "🖼️ إضافة الـWatermark هتتضاف في الخطوة القادمة."
        )

    elif query.data == "file_link":
        await query.edit_message_text(
            "🔗 تحويل الملف إلى رابط هيتضاف في الخطوة القادمة."
        )


async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    mode = context.user_data.get("mode")

    if mode not in ("download", "convert"):
        await update.message.reply_text(
            "اختار وظيفة من القائمة أولًا:",
            reply_markup=main_menu(),
        )
        return

    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text(
            "❌ ابعت رابط يبدأ بـ http:// أو https://"
        )
        return

    context.user_data["video_url"] = url

    # تحميل من رابط = بدون اختيار دقة
    if mode == "download":
        await start_processing(
            update,
            context,
            resolution="same",
            message=(
                "⏳ جاري تحميل الفيلم...\n\n"
                "🎬 الجودة: الأصلية\n"
                "📥 التحميل على GitHub."
            ),
        )
        return

    # تحويل الدقة = هنا فقط يظهر اختيار الدقة
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


async def start_processing(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    resolution: str,
    message: str,
):
    video_url = context.user_data.get("video_url")

    if not video_url:
        await update.message.reply_text(
            "❌ رابط الفيلم غير موجود. ابعت الرابط من جديد."
        )
        return

    if not GH_TOKEN:
        await update.message.reply_text(
            "❌ GH_TOKEN غير موجود."
        )
        return

    chat_id = update.effective_chat.id

    await update.message.reply_text(message)

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
            await update.message.reply_text(
                "✅ بدأ تحميل الفيلم.\n\n"
                "📤 لما يخلص، النتيجة هتتبعت هنا تلقائيًا."
            )
        else:
            await update.message.reply_text(
                "❌ فشل تشغيل المعالجة.\n"
                f"كود الخطأ: {response.status_code}"
            )

    except Exception as e:
        await update.message.reply_text(
            f"❌ حصل خطأ في الاتصال بـ GitHub:\n{e}"
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

    if not GH_TOKEN:
        await query.message.reply_text(
            "❌ GH_TOKEN غير موجود."
        )
        return

    chat_id = update.effective_chat.id

    await query.edit_message_text(
        f"⏳ جاري تجهيز الفيلم...\n\n"
        f"🎬 الدقة: {resolution}\n"
        f"📥 التحميل والمعالجة على GitHub."
    )

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
                "📤 لما يخلص، النتيجة هتتبعت هنا تلقائيًا."
            )
        else:
            await query.message.reply_text(
                "❌ فشل تشغيل المعالجة.\n"
                f"كود الخطأ: {response.status_code}"
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
        CallbackQueryHandler(
            menu_button,
            pattern=r"^(download|convert|subtitle|speech|audio|extract|watermark|file_link)$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            choose_resolution,
            pattern=r"^res_"
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_text,
        )
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
