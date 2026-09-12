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
        [
            InlineKeyboardButton(
                "🌐 ترجمة SRT",
                callback_data="translate_srt"
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def start(update, context):
    await update.message.reply_text(
        "🎬 أهلاً بك في بوت معالجة الفيديو.\n\n"
        "اختار الوظيفة المطلوبة:",
        reply_markup=main_menu(),
    )


async def menu_button(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "download":
        context.user_data["mode"] = "download"

        await query.edit_message_text(
            "🔗 ابعت الآن رابط الفيديو المباشر."
        )

    elif query.data == "convert":
        context.user_data["mode"] = "convert"

        await query.edit_message_text(
            "🎬 ابعت رابط الفيديو، وبعدها هتختار الدقة."
        )

    elif query.data == "translate_srt":
        context.user_data["mode"] = "translate_srt"

        await query.edit_message_text(
            "🌐 ترجمة SRT إلى العربية الفصحى\n\n"
            "📄 ابعت الآن ملف SRT."
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


async def receive_text(update, context):
    text = (update.message.text or "").strip()
    mode = context.user_data.get("mode")

    # =========================
    # VIDEO URL
    # =========================

    if mode in ("download", "convert"):

        if not (
            text.startswith("http://")
            or text.startswith("https://")
        ):
            await update.message.reply_text(
                "❌ ابعت رابط فيديو مباشر يبدأ بـ http:// أو https://"
            )
            return

        if not GH_TOKEN:
            await update.message.reply_text(
                "❌ GH_TOKEN غير موجود في Termux."
            )
            return

        chat_id = update.effective_chat.id

        if mode == "download":
            resolution = "same"
        else:
            resolution = "same"

        await update.message.reply_text(
            "⏳ تم استلام الرابط.\n\n"
            "🚀 جاري إرسال الرابط إلى GitHub لمعالجة الفيديو..."
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
                "video_url": text,
                "subtitle_url": "",
                "resolution": resolution,
                "chat_id": str(chat_id),
                "srt_file_id": "",
                "operation": "video",
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
                    "✅ تم تشغيل المعالجة.\n\n"
                    "📥 GitHub بدأ تحميل الفيديو.\n"
                    "📤 بعد الانتهاء سيصل الفيديو هنا تلقائيًا."
                )

            else:

                await update.message.reply_text(
                    "❌ فشل تشغيل المعالجة.\n\n"
                    f"كود الخطأ: {response.status_code}\n"
                    f"{response.text[:500]}"
                )

        except Exception as e:

            await update.message.reply_text(
                "❌ حدث خطأ أثناء تشغيل GitHub:\n"
                f"{str(e)}"
            )

        return

    # =========================
    # OTHER TEXT
    # =========================

    await update.message.reply_text(
        "اختار وظيفة من القائمة أولًا:",
        reply_markup=main_menu(),
    )


async def receive_document(update, context):
    mode = context.user_data.get("mode")

    if mode != "translate_srt":
        await update.message.reply_text(
            "اختار وظيفة من القائمة أولًا:",
            reply_markup=main_menu(),
        )
        return

    document = update.message.document

    if not document:
        return

    file_name = document.file_name or ""

    if not file_name.lower().endswith(".srt"):
        await update.message.reply_text(
            "❌ لازم تبعت ملف بصيغة SRT."
        )
        return

    if not GH_TOKEN:
        await update.message.reply_text(
            "❌ GH_TOKEN غير موجود."
        )
        return

    file_id = document.file_id
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        "⏳ تم استلام ملف SRT.\n\n"
        "🤖 جاري إرسال الملف للترجمة..."
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
            "video_url": "",
            "subtitle_url": "",
            "resolution": "same",
            "chat_id": str(chat_id),
            "srt_file_id": file_id,
            "operation": "translate_srt",
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
                "✅ بدأت ترجمة ملف SRT.\n\n"
                "📤 عند انتهاء الترجمة سيعود الملف هنا."
            )

        else:

            await update.message.reply_text(
                "❌ فشل تشغيل الترجمة.\n"
                f"كود الخطأ: {response.status_code}\n"
                f"{response.text[:500]}"
            )

    except Exception as e:

        await update.message.reply_text(
            "❌ حدث خطأ:\n"
            f"{str(e)}"
        )


def main():

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN غير موجود.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(menu_button)
    )

    # استقبال الروابط والنصوص
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_text
        )
    )

    # استقبال ملفات SRT
    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            receive_document
        )
    )

    print("🤖 البوت يعمل...")

    app.run_polling()


if __name__ == "__main__":
    main()
