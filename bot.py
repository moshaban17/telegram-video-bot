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
            InlineKeyboardButton("🌐 ترجمة SRT", callback_data="translate_srt"),
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

    elif query.data == "translate_srt":
        context.user_data["mode"] = "translate_srt"

        await query.edit_message_text(
            "🌐 ترجمة SRT إلى العربية الفصحى\n\n"
            "📄 ابعت الآن ملف SRT.\n\n"
            "سيتم الحفاظ على:\n"
            "• أرقام الترجمة\n"
            "• التوقيتات\n"
            "• ترتيب السطور\n"
            "• تنسيق HTML مثل <i> و <font>\n"
            "• رموز ♪ و ♫"
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


async def receive_document(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
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
        "🤖 جاري إرساله للترجمة بالذكاء الاصطناعي...\n"
        "📝 الترجمة ستكون إلى العربية الفصحى."
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
                "📤 لما تخلص، هيرجع لك الملف العربي هنا تلقائيًا."
            )
        else:
            await update.message.reply_text(
                "❌ فشل تشغيل الترجمة.\n"
                f"كود الخط
