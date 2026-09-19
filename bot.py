import os
import json
import requests
from pathlib import Path

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
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

SETTINGS_FILE = Path("settings.json")


# =========================================================
# SETTINGS
# =========================================================

DEFAULT_SETTINGS = {
    "font_message_id": "",
    "font_file_id": "",
    "font_size": "26",
    "font_color": "white",
    "subtitle_outline": "0.5",
    "subtitle_box": "off",

    "watermark_message_id": "",
    "watermark_file_id": "",
    "watermark_enabled": False,
    "watermark_position": "top_left",
    "watermark_size": "20",
}


def load_settings():
    if not SETTINGS_FILE.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        data = json.loads(
            SETTINGS_FILE.read_text(
                encoding="utf-8"
            )
        )

        result = DEFAULT_SETTINGS.copy()
        result.update(data)

        return result

    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    SETTINGS_FILE.write_text(
        json.dumps(
            settings,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def get_settings():
    return load_settings()


# =========================================================
# GITHUB
# =========================================================

def workflow_url():
    return (
        f"https://api.github.com/repos/"
        f"{GITHUB_OWNER}/"
        f"{GITHUB_REPO}/"
        f"actions/workflows/"
        f"{WORKFLOW_FILE}/dispatches"
    )


def github_headers():
    return {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }


def dispatch_workflow(inputs):
    if not GH_TOKEN:
        return None, "GH_TOKEN غير موجود."

    payload = {
        "ref": "main",
        "inputs": inputs,
    }

    try:
        response = requests.post(
            workflow_url(),
            headers=github_headers(),
            json=payload,
            timeout=30,
        )

        if response.status_code not in (200, 201, 204):
            return response, response.text

        return response, None

    except Exception as e:
        return None, str(e)


# =========================================================
# TELEGRAM HELPERS
# =========================================================

async def send_menu(update, text="اختر العملية:"):
    keyboard = main_menu()

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=keyboard
        )


def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔗 تحميل من رابط",
                callback_data="download"
            ),
            InlineKeyboardButton(
                "🎬 تحويل دقة",
                callback_data="convert"
            ),
        ],
        [
            InlineKeyboardButton(
                "📝 حرق ترجمة",
                callback_data="subtitle"
            ),
            InlineKeyboardButton(
                "🔊 إدارة الصوت",
                callback_data="audio"
            ),
        ],
        [
            InlineKeyboardButton(
                "📦 استخراج ترجمة",
                callback_data="extract"
            ),
            InlineKeyboardButton(
                "🖼️ Watermark",
                callback_data="watermark"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔗 ملف → رابط",
                callback_data="file_link"
            ),
            InlineKeyboardButton(
                "👁️ كلام الشاشة → SRT",
                callback_data="ocr"
            ),
        ],
    ])


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "🤖 أهلاً بك\n\n"
        "اختر العملية التي تريد تنفيذها:",
        reply_markup=main_menu()
    )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def menu_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    data = query.data

    # -----------------------------------------------------
    # MAIN MENU
    # -----------------------------------------------------

    if data == "main_menu":
        await query.edit_message_text(
            "اختر العملية:",
            reply_markup=main_menu()
        )
        return

    # -----------------------------------------------------
    # DOWNLOAD
    # -----------------------------------------------------

    if data == "download":
        context.user_data["mode"] = "download"

        await query.edit_message_text(
            "🔗 أرسل رابط الفيديو المباشر."
        )
        return

    # -----------------------------------------------------
    # CONVERT
    # -----------------------------------------------------

    if data == "convert":
        context.user_data["mode"] = "convert"

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "نفس الدقة",
                    callback_data="resolution_same"
                ),
                InlineKeyboardButton(
                    "1080p",
                    callback_data="resolution_1080"
                ),
            ],
            [
                InlineKeyboardButton(
                    "720p",
                    callback_data="resolution_720"
                ),
                InlineKeyboardButton(
                    "480p",
                    callback_data="resolution_480"
                ),
            ],
            [
                InlineKeyboardButton(
                    "360p",
                    callback_data="resolution_360"
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ القائمة",
                    callback_data="main_menu"
                )
            ],
        ])

        await query.edit_message_text(
            "🎬 اختر الدقة:",
            reply_markup=keyboard
        )
        return

    # -----------------------------------------------------
    # RESOLUTION
    # -----------------------------------------------------

    if data.startswith("resolution_"):
        resolution = data.replace(
            "resolution_",
            ""
        )

        context.user_data["resolution"] = resolution
        context.user_data["mode"] = "convert"

        await query.edit_message_text(
            f"🎬 الدقة المختارة: {resolution}\n\n"
            "أرسل الفيديو الآن."
        )
        return

    # -----------------------------------------------------
    # SUBTITLE
    # -----------------------------------------------------

        if data == "subtitle":
        context.user_data["mode"] = "subtitle"

        settings = load_settings()

        font_name = "تم رفع خط مخصص" if settings.get("font_message_id") else "Noto Sans Arabic"
        font_color = settings.get("font_color", "white")
        font_size = settings.get("font_size", "26")
        box = settings.get("subtitle_box", "off")
        watermark = settings.get("watermark_enabled", False)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "➕ إضافة / تغيير الخط",
                callback_data="font_upload"
            )],
            [InlineKeyboardButton(
                f"🎨 لون الخط: {font_color}",
                callback_data="font_color_settings"
            )],
            [InlineKeyboardButton(
                f"🔠 حجم الخط: {font_size}",
                callback_data="font_size_settings"
            )],
            [InlineKeyboardButton(
                "🖤 Outline: 0.5 (ثابت)",
                callback_data="outline_fixed"
            )],
            [InlineKeyboardButton(
                f"⬛ Box: {'تشغيل' if box == 'on' else 'إيقاف'}",
                callback_data="toggle_box"
            )],
            [InlineKeyboardButton(
                f"🖼️ العلامة المائية: {'تشغيل' if watermark else 'إيقاف'}",
                callback_data="toggle_watermark"
            )],
            [InlineKeyboardButton(
                "▶️ بدء الحرق",
                callback_data="burn_ready"
            )],
            [InlineKeyboardButton(
                "⬅️ القائمة",
                callback_data="main_menu"
            )],
        ])

        await query.edit_message_text(
            "📝 إعدادات حرق الترجمة\n\n"
            f"الخط: {font_name}\n"
            f"حجم الخط: {font_size}\n"
            f"لون الخط: {font_color}\n"
            "Outline: 0.5\n"
            f"Box: {'تشغيل' if box == 'on' else 'إيقاف'}\n"
            f"العلامة المائية: {'تشغيل' if watermark else 'إيقاف'}\n\n"
            "أرسل الفيديو ثم ملف الترجمة، أو اضبط الإعدادات أولًا.",
            reply_markup=keyboard
        )
        return

    # -----------------------------------------------------
    # FONT SETTINGS
    # -----------------------------------------------------

    if data == "font_settings":
    context.user_data["waiting_for"] = "font"

    settings = get_settings()

    await query.edit_message_text(
        "➕ إضافة / تغيير الخط\n\n"
        f"الخط الحالي: "
        f"{'محفوظ' if settings.get('font_message_id') else 'الافتراضي'}\n\n"
        "📁 أرسل ملف الخط الآن.\n\n"
        "الصيغ المدعومة:\n"
        "• TTF\n"
        "• OTF\n"
        "• RAR"
    )
    return

    # -----------------------------------------------------
    # WATERMARK
    # -----------------------------------------------------

    if data == "watermark":
        context.user_data["mode"] = "watermark"

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⚙️ إعدادات العلامة المائية",
                    callback_data="watermark_settings"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ القائمة",
                    callback_data="main_menu"
                )
            ],
        ])

        await query.edit_message_text(
            "🖼️ العلامة المائية\n\n"
            "يمكنك حفظ صورة أو RAR يحتوي على صورة "
            "لاستخدامها أثناء حرق الترجمة.",
            reply_markup=keyboard
        )
        return

    if data == "watermark_settings":
        context.user_data["waiting_for"] = "watermark"

        settings = get_settings()

        await query.edit_message_text(
            "🖼️ إعدادات العلامة المائية\n\n"
            f"الحالة: "
            f"{'مفعلة' if settings.get('watermark_enabled') else 'متوقفة'}\n"
            f"المكان: {settings.get('watermark_position', 'top_left')}\n"
            f"الحجم: {settings.get('watermark_size', '20')}%\n\n"
            "أرسل صورة PNG/JPG/WEBP أو RAR يحتوي على صورة."
        )
        return

    # -----------------------------------------------------
    # OCR
    # -----------------------------------------------------

    if data == "ocr":
        context.user_data["mode"] = "ocr"

        await query.edit_message_text(
            "👁️ كلام الشاشة → SRT\n\n"
            "أرسل الفيديو."
        )
        return

    # -----------------------------------------------------
    # OTHER CURRENT FUNCTIONS
    # -----------------------------------------------------

    if data == "audio":
        await query.edit_message_text(
            "🔊 إدارة الصوت\n\n"
            "هذه الوظيفة محفوظة في القائمة وسيتم ربط "
            "إدارة المسارات الصوتية في مرحلة المعالجة التالية.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ القائمة",
                        callback_data="main_menu"
                    )
                ]
            ])
        )
        return

    if data == "extract":
        await query.edit_message_text(
            "📦 استخراج ترجمة\n\n"
            "هذه الوظيفة محفوظة في القائمة وسيتم ربط "
            "استخراج المسارات المضمنة في مرحلة المعالجة التالية.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ القائمة",
                        callback_data="main_menu"
                    )
                ]
            ])
        )
        return

    if data == "file_link":
        await query.edit_message_text(
            "🔗 ملف → رابط\n\n"
            "هذه الوظيفة محفوظة في القائمة وسيتم ربط "
            "خدمة رفع الملفات في مرحلة المعالجة التالية.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ القائمة",
                        callback_data="main_menu"
                    )
                ]
            ])
        )
        return

    # -----------------------------------------------------
    # BURN READY
    # -----------------------------------------------------

    if data == "burn_ready":
        mode = context.user_data.get("mode")

        if mode != "subtitle":
            context.user_data["mode"] = "subtitle"

        video_id = context.user_data.get(
            "video_message_id"
        )

        subtitle_id = context.user_data.get(
            "subtitle_message_id"
        )

        if not video_id:
            await query.edit_message_text(
                "❌ أرسل الفيديو أولاً."
            )
            return

        if not subtitle_id:
            await query.edit_message_text(
                "❌ أرسل ملف الترجمة أولاً."
            )
            return

        await start_burn(
            update,
            context
        )
        return


# =========================================================
# TEXT HANDLER
# =========================================================

async def receive_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text.strip()

    mode = context.user_data.get("mode")

    # -----------------------------------------------------
    # DOWNLOAD
    # -----------------------------------------------------

    if mode == "download":
        if not (
            text.startswith("http://")
            or text.startswith("https://")
        ):
            await update.message.reply_text(
                "❌ أرسل رابطًا صحيحًا يبدأ بـ http:// أو https://"
            )
            return

        context.user_data["video_url"] = text

        inputs = {
            "chat_id": str(update.effective_chat.id),
            "video_message_id": "",
            "subtitle_message_id": "",
            "subtitle_type": "srt",
            "font_message_id": "",
            "font_size": "26",
            "font_color": "white",
            "subtitle_outline": "0.5",
            "subtitle_box": "off",
            "watermark_message_id": "",
            "watermark_enabled": "false",
            "watermark_position": "top_left",
            "watermark_size": "20",
        }

        # هذه العملية تحتاج workflow مستقل للتحميل.
        await update.message.reply_text(
            "🔗 تم استلام الرابط.\n\n"
            "وظيفة التحميل من الرابط محفوظة، "
            "وسنربطها بالـWorkflow الخاص بها بعد تثبيت نظام الحرق."
        )
        return

    await update.message.reply_text(
        "اختر العملية من القائمة.",
        reply_markup=main_menu()
    )


# =========================================================
# VIDEO HANDLER
# =========================================================

async def receive_video(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.message

    mode = context.user_data.get("mode")

    context.user_data["video_message_id"] = (
        message.message_id
    )

    # -----------------------------------------------------
    # OCR
    # -----------------------------------------------------

    if mode == "ocr":
        await message.reply_text(
            "👁️ تم استلام الفيديو.\n\n"
            "وظيفة OCR محفوظة وسيتم تشغيلها "
            "بـWorkflow المعالجة الخاص بها."
        )
        return

    # -----------------------------------------------------
    # SUBTITLE
    # -----------------------------------------------------

    if mode == "subtitle":
        await message.reply_text(
            "🎬 تم استلام الفيديو.\n\n"
            "الآن أرسل ملف الترجمة SRT أو ASS أو SSA."
        )
        return

    # -----------------------------------------------------
    # CONVERT
    # -----------------------------------------------------

    if mode == "convert":
        resolution = context.user_data.get(
            "resolution",
            "same"
        )

        await message.reply_text(
            f"🎬 تم استلام الفيديو.\n\n"
            f"الدقة المطلوبة: {resolution}\n\n"
            "وظيفة التحويل محفوظة وسيتم تشغيلها "
            "بـWorkflow الخاص بالتحويل."
        )
        return

    await message.reply_text(
        "📹 تم استلام الفيديو.\n\n"
        "اختر العملية من القائمة."
    )


# =========================================================
# DOCUMENT HANDLER
# =========================================================

async def receive_document(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.message
    document = message.document

    mode = context.user_data.get("mode")

    file_name = (
        document.file_name or ""
    ).lower()

    # -----------------------------------------------------
    # FONT
    # -----------------------------------------------------

    if context.user_data.get("waiting_for") == "font":
        if not (
            file_name.endswith(".ttf")
            or file_name.endswith(".otf")
            or file_name.endswith(".rar")
        ):
            await message.reply_text(
                "❌ أرسل TTF أو OTF أو RAR يحتوي على الخط."
            )
            return

        settings = get_settings()

        settings["font_message_id"] = str(
            message.message_id
        )

        settings["font_file_id"] = (
            document.file_id
        )

        save_settings(settings)

        context.user_data["waiting_for"] = None

        await message.reply_text(
            "✅ تم حفظ الخط.\n\n"
            "يمكن إعادة استخدامه لاحقًا أثناء حرق الترجمة."
        )
        return

    # -----------------------------------------------------
    # WATERMARK
    # -----------------------------------------------------

    if context.user_data.get("waiting_for") == "watermark":
        if not (
            file_name.endswith(".png")
            or file_name.endswith(".jpg")
            or file_name.endswith(".jpeg")
            or file_name.endswith(".webp")
            or file_name.endswith(".rar")
        ):
            await message.reply_text(
                "❌ أرسل PNG أو JPG أو JPEG أو WEBP أو RAR."
            )
            return

        settings = get_settings()

        settings["watermark_message_id"] = str(
            message.message_id
        )

        settings["watermark_file_id"] = (
            document.file_id
        )

        settings["watermark_enabled"] = True

        save_settings(settings)

        context.user_data["waiting_for"] = None

        await message.reply_text(
            "✅ تم حفظ العلامة المائية.\n\n"
            "يمكن إعادة استخدامها لاحقًا."
        )
        return

    # -----------------------------------------------------
    # SUBTITLE
    # -----------------------------------------------------

    if mode == "subtitle":
        if file_name.endswith(".srt"):
            subtitle_type = "srt"

        elif file_name.endswith(".ass"):
            subtitle_type = "ass"

        elif file_name.endswith(".ssa"):
            subtitle_type = "ssa"

        else:
            await message.reply_text(
                "❌ ملف الترجمة يجب أن يكون SRT أو ASS أو SSA."
            )
            return

        context.user_data["subtitle_message_id"] = (
            message.message_id
        )

        context.user_data["subtitle_type"] = (
            subtitle_type
        )

        await message.reply_text(
            "✅ تم استلام الترجمة.\n\n"
            f"النوع: {subtitle_type.upper()}\n\n"
            "اضغط «بدء الحرق» من القائمة."
        )

        await message.reply_text(
            "📝 جاهز للحرق:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "▶️ بدء الحرق",
                        callback_data="burn_ready"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⚙️ إعدادات الخط",
                        callback_data="font_settings"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🖼️ العلامة المائية",
                        callback_data="watermark_settings"
                    )
                ],
            ])
        )
        return

    await message.reply_text(
        "📁 تم استلام الملف.\n\n"
        "اختر العملية المناسبة من القائمة."
    )


# =========================================================
# BURN
# =========================================================

async def start_burn(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    settings = get_settings()

    chat_id = update.effective_chat.id

    video_message_id = context.user_data.get(
        "video_message_id",
        ""
    )

    subtitle_message_id = context.user_data.get(
        "subtitle_message_id",
        ""
    )

    subtitle_type = context.user_data.get(
        "subtitle_type",
        "srt"
    )

    font_message_id = settings.get(
        "font_message_id",
        ""
    )

    watermark_message_id = settings.get(
        "watermark_message_id",
        ""
    )

    watermark_enabled = (
        "true"
        if settings.get("watermark_enabled")
        else "false"
    )

    inputs = {
        "chat_id": str(chat_id),

        "video_message_id": str(
            video_message_id
        ),

        "subtitle_message_id": str(
            subtitle_message_id
        ),

        "subtitle_type": str(
            subtitle_type
        ),

        "font_message_id": str(
            font_message_id
        ),

        "font_size": str(
            settings.get(
                "font_size",
                "26"
            )
        ),

        "font_color": str(
            settings.get(
                "font_color",
                "white"
            )
        ),

        "subtitle_outline": str(
            settings.get(
                "subtitle_outline",
                "0.5"
            )
        ),

        "subtitle_box": str(
            settings.get(
                "subtitle_box",
                "off"
            )
        ),

        "watermark_message_id": str(
            watermark_message_id
        ),

        "watermark_enabled": watermark_enabled,

        "watermark_position": str(
            settings.get(
                "watermark_position",
                "top_left"
            )
        ),

        "watermark_size": str(
            settings.get(
                "watermark_size",
                "20"
            )
        ),
    }

    response, error = dispatch_workflow(
        inputs
    )

    if response is None:
        text = (
            "❌ فشل تشغيل GitHub Actions.\n\n"
            f"{error}"
        )

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=main_menu()
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=main_menu()
            )

        return

    if response.status_code not in (
        200,
        201,
        204,
    ):
        text = (
            "❌ GitHub رفض تشغيل الـWorkflow.\n\n"
            f"HTTP {response.status_code}\n\n"
            f"{response.text}"
        )

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=main_menu()
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=main_menu()
            )

        return

    text = (
        "🚀 بدأ حرق الترجمة.\n\n"
        f"🎬 الفيديو: {video_message_id}\n"
        f"📝 الترجمة: {subtitle_message_id}\n"
        f"📄 النوع: {subtitle_type.upper()}\n\n"
        "سيتم إرسال الفيديو هنا بعد انتهاء المعالجة."
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=main_menu()
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=main_menu()
        )


# =========================================================
# MAIN
# =========================================================

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN غير موجود.")
        return

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            menu_button
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_text
        )
    )

    app.add_handler(
        MessageHandler(
            filters.VIDEO,
            receive_video
        )
    )

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
