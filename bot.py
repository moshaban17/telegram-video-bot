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
BOT_USERNAME = "CinmalekHardsubBot"


# =========================
# MAIN MENU
# =========================

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
            InlineKeyboardButton("👁️ كلام الشاشة → SRT", callback_data="ocr"),
            InlineKeyboardButton("🔊 إدارة الصوت", callback_data="audio"),
        ],
        [
            InlineKeyboardButton("📦 استخراج ترجمة", callback_data="extract"),
            InlineKeyboardButton("🖼️ Watermark", callback_data="watermark"),
        ],
        [
            InlineKeyboardButton("🔗 ملف → رابط", callback_data="file_link"),
            InlineKeyboardButton("🌐 ترجمة SRT", callback_data="translate_srt"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "🎬 اختر الوظيفة المطلوبة:",
        reply_markup=main_menu(),
    )


# =========================
# GITHUB ACTIONS
# =========================

def github_dispatch(
    chat_id,
    operation="video",
    video_url="",
    subtitle_url="",
    resolution="same",
    srt_file_id="",
    telegram_message_id="",
    source_type="url",
    subtitle_type="",
    font_name="Noto Sans",
    font_size="28",
    font_color="white",
    subtitle_box="off",
):
    url = (
        f"https://api.github.com/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/"
        f"{WORKFLOW_FILE}/dispatches"
    )

    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    data = {
        "ref": "main",
        "inputs": {
            "video_url": video_url,
            "subtitle_url": subtitle_url,
            "resolution": resolution,
            "chat_id": str(chat_id),
            "bot_username": BOT_USERNAME,
            "srt_file_id": srt_file_id,
            "telegram_message_id": str(telegram_message_id),
            "source_type": source_type,
            "operation": operation,
            "subtitle_type": subtitle_type,
            "font_name": font_name,
            "font_size": font_size,
            "font_color": font_color,
            "subtitle_box": subtitle_box,
        },
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=30,
    )

    return response


# =========================
# MENU BUTTONS
# =========================

async def menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mode = query.data

    # -------------------------
    # DOWNLOAD
    # -------------------------
    if mode == "download":
        context.user_data.clear()
        context.user_data["mode"] = "download"

        await query.message.reply_text(
            "🔗 ابعت رابط الفيلم المباشر أو ابعت الفيلم هنا."
        )

    # -------------------------
    # CONVERT
    # -------------------------
    elif mode == "convert":
        context.user_data.clear()
        context.user_data["mode"] = "convert"

        await query.message.reply_text(
            "🎬 ابعت الفيلم كفيديو/ملف أو ابعت الرابط المباشر."
        )

    # -------------------------
    # SUBTITLE
    # -------------------------
    elif mode == "subtitle":
        context.user_data.clear()
        context.user_data["mode"] = "subtitle"

        await query.message.reply_text(
            "📝 حرق ترجمة\n\n"
            "1️⃣ ابعت الفيلم كفيديو أو ملف.\n"
            "2️⃣ بعده ابعت ملف الترجمة SRT أو ASS."
        )

    # -------------------------
    # SPEECH
    # -------------------------
    elif mode == "speech":
        context.user_data.clear()
        context.user_data["mode"] = "speech"

        await query.message.reply_text(
            "🎙️ ابعت الفيديو أو ملف الصوت، أو ابعت رابط مباشر."
        )

    # -------------------------
    # OCR
    # -------------------------
    elif mode == "ocr":
        context.user_data.clear()
        context.user_data["mode"] = "ocr"

        keyboard = [
            [
                InlineKeyboardButton("🇬🇧 English", callback_data="ocr_en"),
                InlineKeyboardButton("🇱🇰 Sinhala", callback_data="ocr_si"),
            ],
            [
                InlineKeyboardButton("🇮🇳 Hindi", callback_data="ocr_hi"),
                InlineKeyboardButton("🇮🇳 Malayalam", callback_data="ocr_ml"),
            ],
            [
                InlineKeyboardButton("🇮🇳 Telugu", callback_data="ocr_te"),
                InlineKeyboardButton("🇮🇳 Tamil", callback_data="ocr_ta"),
            ],
            [
                InlineKeyboardButton("🇮🇳 Bengali", callback_data="ocr_bn"),
            ],
        ]

        await query.message.reply_text(
            "👁️ اختر لغة الكلام الظاهر على الشاشة:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # -------------------------
    # TRANSLATE SRT
    # -------------------------
    elif mode == "translate_srt":
        context.user_data.clear()
        context.user_data["mode"] = "translate_srt"

        await query.message.reply_text(
            "🌐 ابعت ملف SRT."
        )

    # -------------------------
    # PLACEHOLDERS
    # -------------------------
    elif mode == "audio":
        await query.message.reply_text(
            "🔊 وظيفة إدارة الصوت هتتضاف في الخطوة القادمة."
        )

    elif mode == "extract":
        await query.message.reply_text(
            "📦 وظيفة استخراج الترجمة هتتضاف في الخطوة القادمة."
        )

    elif mode == "watermark":
        await query.message.reply_text(
            "🖼️ وظيفة الـ Watermark هتتضاف في الخطوة القادمة."
        )

    elif mode == "file_link":
        await query.message.reply_text(
            "🔗 وظيفة ملف → رابط هتتضاف في الخطوة القادمة."
        )


# =========================
# OCR LANGUAGE
# =========================

async def ocr_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.replace("ocr_", "")

    context.user_data["ocr_language"] = lang

    await query.message.reply_text(
        f"👁️ تم اختيار اللغة: {lang}\n\n"
        "ابعت الفيديو كفيديو/ملف أو ابعت الرابط."
    )


# =========================
# TEXT / URL
# =========================

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    mode = context.user_data.get("mode")

    if not mode:
        await update.message.reply_text(
            "اختار وظيفة من القائمة أولًا.",
            reply_markup=main_menu(),
        )
        return

    # =========================
    # SUBTITLE URL FLOW
    # =========================

    if mode == "subtitle":
        # لو المستخدم بعت رابط فيديو
        if not context.user_data.get("video_received"):
            context.user_data["video_url"] = text
            context.user_data["source_type"] = "url"
            context.user_data["video_received"] = True

            await update.message.reply_text(
                "🎬 تم استلام رابط الفيلم.\n\n"
                "📝 الآن ابعت ملف الترجمة SRT أو ASS."
            )
            return

    # =========================
    # NORMAL VIDEO URL
    # =========================

    if mode in ("download", "convert", "ocr", "speech"):

        operation = "video"

        if mode == "ocr":
            operation = "video_ocr"

        elif mode == "speech":
            operation = "audio_srt"

        resolution = "same"

        response = github_dispatch(
            chat_id=update.effective_chat.id,
            operation=operation,
            video_url=text,
            resolution=resolution,
            source_type="url",
        )

        if response.status_code == 204:
            await update.message.reply_text(
                "✅ تم إرسال المهمة إلى GitHub Actions.\n"
                "⏳ جاري المعالجة..."
            )
        else:
            await update.message.reply_text(
                "❌ حصل خطأ أثناء تشغيل المهمة.\n\n"
                f"{response.text[:1000]}"
            )

        return

    await update.message.reply_text(
        "⚠️ ابعت الملف المطلوب لهذه الوظيفة."
    )


# =========================
# VIDEO RECEIVED
# =========================

async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")

    if not mode:
        await update.message.reply_text(
            "اختار وظيفة من القائمة أولًا.",
            reply_markup=main_menu(),
        )
        return

    message_id = update.message.message_id
    chat_id = update.effective_chat.id

    # =========================
    # SUBTITLE
    # =========================

    if mode == "subtitle":

        context.user_data["video_received"] = True
        context.user_data["source_type"] = "telegram"
        context.user_data["telegram_message_id"] = message_id

        await update.message.reply_text(
            "🎬 تم استلام الفيلم.\n\n"
            "📝 الآن ابعت ملف الترجمة SRT أو ASS."
        )

        return

    # =========================
    # NORMAL VIDEO
    # =========================

    operation = "video"

    if mode == "ocr":
        operation = "video_ocr"

    elif mode == "speech":
        operation = "audio_srt"

    elif mode == "download":
        operation = "video"

    elif mode == "convert":
        operation = "video"

    response = github_dispatch(
        chat_id=chat_id,
        operation=operation,
        resolution="same",
        telegram_message_id=message_id,
        source_type="telegram",
    )

    if response.status_code == 204:
        await update.message.reply_text(
            "✅ تم استلام الفيلم.\n"
            "⏳ جاري بدء المعالجة..."
        )
    else:
        await update.message.reply_text(
            "❌ حصل خطأ أثناء تشغيل المهمة.\n\n"
            f"{response.text[:1000]}"
        )


# =========================
# DOCUMENT RECEIVED
# =========================

async def receive_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    if not document:
        return

    filename = document.file_name or ""
    lower_name = filename.lower()

    mode = context.user_data.get("mode")

    if not mode:
        await update.message.reply_text(
            "اختار وظيفة من القائمة أولًا.",
            reply_markup=main_menu(),
        )
        return

    # =========================
    # SUBTITLE BURN
    # =========================

    if mode == "subtitle":

        # فيلم كملف
        video_extensions = (
            ".mp4",
            ".mkv",
            ".avi",
            ".mov",
            ".webm",
            ".m4v",
            ".ts",
            ".mpeg",
            ".mpg",
        )

        if lower_name.endswith(video_extensions):

            context.user_data["video_received"] = True
            context.user_data["source_type"] = "telegram"
            context.user_data["telegram_message_id"] = update.message.message_id

            await update.message.reply_text(
                "🎬 تم استلام الفيلم.\n\n"
                "📝 الآن ابعت ملف الترجمة SRT أو ASS."
            )

            return

        # SRT
        if lower_name.endswith(".srt"):

            if not context.user_data.get("video_received"):
                await update.message.reply_text(
                    "⚠️ ابعت الفيلم أولًا، وبعده ملف SRT."
                )
                return

            context.user_data["subtitle_received"] = True
            context.user_data["subtitle_type"] = "srt"
            context.user_data["srt_file_id"] = document.file_id

            await show_subtitle_settings(update, context)
            return

        # ASS
        if lower_name.endswith(".ass") or lower_name.endswith(".ssa"):

            if not context.user_data.get("video_received"):
                await update.message.reply_text(
                    "⚠️ ابعت الفيلم أولًا، وبعده ملف ASS."
                )
                return

            context.user_data["subtitle_received"] = True
            context.user_data["subtitle_type"] = "ass"
            context.user_data["srt_file_id"] = document.file_id

            await show_ass_settings(update, context)
            return

        await update.message.reply_text(
            "⚠️ الملف غير مدعوم.\n"
            "ابعت SRT أو ASS."
        )

        return

    # =========================
    # TRANSLATE SRT
    # =========================

    if mode == "translate_srt":

        if not lower_name.endswith(".srt"):
            await update.message.reply_text(
                "⚠️ لازم تبعت ملف SRT."
            )
            return

        response = github_dispatch(
            chat_id=update.effective_chat.id,
            operation="translate_srt",
            srt_file_id=document.file_id,
            source_type="telegram",
        )

        if response.status_code == 204:
            await update.message.reply_text(
                "🌐 تم استلام ملف SRT.\n"
                "⏳ جاري ترجمته..."
            )
        else:
            await update.message.reply_text(
                "❌ حصل خطأ أثناء تشغيل الترجمة.\n\n"
                f"{response.text[:1000]}"
            )

        return

    # =========================
    # SPEECH
    # =========================

    if mode == "speech":

        audio_extensions = (
            ".mp3",
            ".wav",
            ".m4a",
            ".aac",
            ".flac",
            ".ogg",
            ".opus",
            ".mp4",
            ".mkv",
            ".avi",
            ".mov",
        )

        if not lower_name.endswith(audio_extensions):
            await update.message.reply_text(
                "⚠️ الملف غير مدعوم."
            )
            return

        response = github_dispatch(
            chat_id=update.effective_chat.id,
            operation="audio_srt",
            telegram_message_id=update.message.message_id,
            source_type="telegram",
        )

        if response.status_code == 204:
            await update.message.reply_text(
                "🎙️ تم استلام الملف.\n"
                "⏳ جاري استخراج الكلام إلى SRT..."
            )
        else:
            await update.message.reply_text(
                "❌ حصل خطأ أثناء تشغيل المهمة.\n\n"
                f"{response.text[:1000]}"
            )

        return

    # =========================
    # DOWNLOAD / CONVERT / OCR
    # =========================

    if mode in ("download", "convert", "ocr"):

        video_extensions = (
            ".mp4",
            ".mkv",
            ".avi",
            ".mov",
            ".webm",
            ".m4v",
            ".ts",
            ".mpeg",
            ".mpg",
        )

        if not lower_name.endswith(video_extensions):
            await update.message.reply_text(
                "⚠️ الملف غير مدعوم."
            )
            return

        operation = "video"

        if mode == "ocr":
            operation = "video_ocr"

        response = github_dispatch(
            chat_id=update.effective_chat.id,
            operation=operation,
            telegram_message_id=update.message.message_id,
            source_type="telegram",
            resolution="same",
        )

        if response.status_code == 204:
            await update.message.reply_text(
                "✅ تم استلام الفيلم.\n"
                "⏳ جاري المعالجة..."
            )
        else:
            await update.message.reply_text(
                "❌ حصل خطأ أثناء تشغيل المهمة.\n\n"
                f"{response.text[:1000]}"
            )

        return


# =========================
# SUBTITLE SETTINGS
# =========================

async def show_subtitle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton("🔤 Noto Sans", callback_data="font_noto"),
            InlineKeyboardButton("🔤 Arial", callback_data="font_arial"),
        ],
        [
            InlineKeyboardButton("📏 صغير", callback_data="size_24"),
            InlineKeyboardButton("📏 متوسط", callback_data="size_28"),
            InlineKeyboardButton("📏 كبير", callback_data="size_32"),
        ],
        [
            InlineKeyboardButton("⚪ أبيض", callback_data="color_white"),
            InlineKeyboardButton("🟡 أصفر", callback_data="color_yellow"),
        ],
        [
            InlineKeyboardButton("⬛ صندوق أسود", callback_data="box_on"),
            InlineKeyboardButton("🚫 بدون صندوق", callback_data="box_off"),
        ],
        [
            InlineKeyboardButton("▶️ حرق الترجمة", callback_data="subtitle_start"),
        ],
    ]

    context.user_data.setdefault("font_name", "Noto Sans")
    context.user_data.setdefault("font_size", "28")
    context.user_data.setdefault("font_color", "white")
    context.user_data.setdefault("subtitle_box", "off")

    await update.message.reply_text(
        "⚙️ إعدادات الترجمة:\n\n"
        "اختار الإعدادات المطلوبة ثم اضغط «▶️ حرق الترجمة».",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_ass_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "▶️ استخدام ASS كما هو",
                callback_data="subtitle_start",
            )
        ]
    ]

    await update.message.reply_text(
        "🎨 ملف ASS يحتوي على تنسيق الترجمة الخاص به.\n\n"
        "لن أغيّر الخط أو الحجم أو اللون أو الصندوق الموجود داخله.\n\n"
        "اضغط للبدء:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# SUBTITLE SETTINGS BUTTONS
# =========================

async def subtitle_settings_button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "font_noto":
        context.user_data["font_name"] = "Noto Sans"

    elif data == "font_arial":
        context.user_data["font_name"] = "Arial"

    elif data.startswith("size_"):
        context.user_data["font_size"] = data.replace("size_", "")

    elif data == "color_white":
        context.user_data["font_color"] = "white"

    elif data == "color_yellow":
        context.user_data["font_color"] = "yellow"

    elif data == "box_on":
        context.user_data["subtitle_box"] = "on"

    elif data == "box_off":
        context.user_data["subtitle_box"] = "off"

    elif data == "subtitle_start":

        if not context.user_data.get("video_received"):
            await query.message.reply_text(
                "⚠️ الفيلم غير موجود."
            )
            return

        if not context.user_data.get("subtitle_received"):
            await query.message.reply_text(
                "⚠️ ملف الترجمة غير موجود."
            )
            return

        response = github_dispatch(
            chat_id=update.effective_chat.id,
            operation="video",
            resolution="same",
            srt_file_id=context.user_data.get("srt_file_id", ""),
            telegram_message_id=context.user_data.get(
                "telegram_message_id",
                "",
            ),
            source_type=context.user_data.get(
                "source_type",
                "telegram",
            ),
            subtitle_type=context.user_data.get(
                "subtitle_type",
                "srt",
            ),
            font_name=context.user_data.get(
                "font_name",
                "Noto Sans",
            ),
            font_size=context.user_data.get(
                "font_size",
                "28",
            ),
            font_color=context.user_data.get(
                "font_color",
                "white",
            ),
            subtitle_box=context.user_data.get(
                "subtitle_box",
                "off",
            ),
        )

        if response.status_code == 204:

            await query.message.reply_text(
                "🔥 تم إرسال مهمة حرق الترجمة.\n"
                "⏳ جاري تجهيز الفيلم..."
            )

            context.user_data.clear()

        else:

            await query.message.reply_text(
                "❌ حصل خطأ أثناء تشغيل المهمة.\n\n"
                f"{response.text[:1000]}"
            )

        return

    await query.message.reply_text(
        "✅ تم حفظ الإعداد."
    )


# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN غير موجود")

    if not GH_TOKEN:
        raise RuntimeError("GH_TOKEN غير موجود")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        CallbackQueryHandler(
            subtitle_settings_button,
            pattern=r"^(font_|size_|color_|box_|subtitle_start)",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            ocr_language,
            pattern=r"^ocr_",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            menu_button,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.VIDEO,
            receive_video,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            receive_document,
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
