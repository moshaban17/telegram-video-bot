import os
import json
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


# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GH_TOKEN = os.getenv("GH_TOKEN", "").strip()

GITHUB_OWNER = "moshaban17"
GITHUB_REPO = "telegram-video-bot"
WORKFLOW_FILE = "process.yml"
GITHUB_REF = "main"

SETTINGS_FILE = "settings.json"


# =========================
# SETTINGS
# =========================

DEFAULT_SETTINGS = {
    "font_message_id": "",
    "font_size": "28",
    "font_color": "FFFFFF",
    "subtitle_outline": "1",
    "subtitle_box": "0",
    "watermark_message_id": "",
    "watermark_enabled": "0",
    "watermark_position": "bottom_right",
    "watermark_size": "20",
}


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        settings = DEFAULT_SETTINGS.copy()

        if isinstance(data, dict):
            settings.update(data)

        return settings

    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            settings,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================
# GITHUB
# =========================

def workflow_url():
    return (
        f"https://api.github.com/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/"
        f"{WORKFLOW_FILE}/dispatches"
    )


def run_github_workflow(inputs):
    if not GH_TOKEN:
        return False, "GH_TOKEN غير موجود."

    clean_inputs = {}

    for key, value in inputs.items():
        if value is None:
            value = ""

        clean_inputs[str(key)] = str(value)

    payload = {
        "ref": GITHUB_REF,
        "inputs": clean_inputs,
    }

    payload_bytes = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":")
    ).encode("utf-8")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GH_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json; charset=utf-8",
    }

    try:
        response = requests.post(
            workflow_url(),
            headers=headers,
            data=payload_bytes,
            timeout=30,
        )

        if response.status_code in (200, 201, 202, 204):
            return True, ""

        try:
            error_data = response.json()
            message = error_data.get("message", "")
        except Exception:
            message = response.text[:1000]

        return False, (
            f"GitHub HTTP {response.status_code}: "
            f"{message}"
        )

    except UnicodeEncodeError as e:
        return False, (
            "حدث خطأ ترميز أثناء إرسال طلب GitHub: "
            f"{e}"
        )

    except requests.RequestException as e:
        return False, f"خطأ اتصال مع GitHub: {e}"

    except Exception as e:
        return False, f"خطأ غير متوقع: {e}"


# =========================
# USER DATA
# =========================

def get_user_settings(context):
    if "settings" not in context.user_data:
        context.user_data["settings"] = load_settings()

    return context.user_data["settings"]


# =========================
# MAIN MENU
# =========================

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton(
                "📝 حرق ترجمة",
                callback_data="subtitle"
            )
        ],
        [
            InlineKeyboardButton(
                "🔤 إعدادات الخط",
                callback_data="font_settings"
            ),
            InlineKeyboardButton(
                "⚙️ إعدادات الترجمة",
                callback_data="subtitle_settings"
            )
        ],
        [
            InlineKeyboardButton(
                "🖼️ Watermark",
                callback_data="watermark"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    context.user_data["stage"] = None
    context.user_data["video_message_id"] = None
    context.user_data["subtitle_message_id"] = None
    context.user_data["subtitle_type"] = None

    await update.message.reply_text(
        "🎬 اختر العملية:",
        reply_markup=main_menu()
    )


# =========================
# SUBTITLE BURN
# =========================

async def subtitle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["stage"] = "subtitle_video"

    await query.message.reply_text(
        "🎬 أرسل الفيديو أولًا."
    )


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("stage") != "subtitle_video":
        return

    message = update.message

    if not message.video and not message.document:
        await message.reply_text(
            "❌ أرسل الفيديو كفيديو أو كملف."
        )
        return

    context.user_data["video_message_id"] = message.message_id
    context.user_data["stage"] = "subtitle_file"

    await message.reply_text(
        "✅ تم استلام الفيديو.\n\n"
        "📝 أرسل ملف الترجمة SRT أو ASS أو SSA."
    )


async def handle_subtitle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("stage") != "subtitle_file":
        return

    message = update.message

    if not message.document:
        await message.reply_text(
            "❌ أرسل ملف الترجمة كملف."
        )
        return

    filename = message.document.file_name or ""
    lower_name = filename.lower()

    if lower_name.endswith(".srt"):
        subtitle_type = "srt"

    elif lower_name.endswith(".ass"):
        subtitle_type = "ass"

    elif lower_name.endswith(".ssa"):
        subtitle_type = "ssa"

    else:
        await message.reply_text(
            "❌ الملف يجب أن يكون SRT أو ASS أو SSA."
        )
        return

    context.user_data["subtitle_message_id"] = message.message_id
    context.user_data["subtitle_type"] = subtitle_type

    await message.reply_text(
        "⏳ جاري تشغيل حرق الترجمة..."
    )

    await dispatch_burn(update, context)


# =========================
# DISPATCH BURN
# =========================

async def dispatch_burn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = get_user_settings(context)

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

    watermark_enabled = str(
        settings.get("watermark_enabled", "0")
    ).lower()

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
            settings.get("font_message_id", "")
        ),

        "font_size": str(
            settings.get("font_size", "28")
        ),

        "font_color": str(
            settings.get("font_color", "FFFFFF")
        ),

        "subtitle_outline": str(
            settings.get("subtitle_outline", "1")
        ),

        "subtitle_box": str(
            settings.get("subtitle_box", "0")
        ),

        "watermark_message_id": str(
            settings.get("watermark_message_id", "")
            if watermark_enabled == "1"
            else ""
        ),

        "watermark_enabled": watermark_enabled,

        "watermark_position": str(
            settings.get(
                "watermark_position",
                "bottom_right"
            )
        ),

        "watermark_size": str(
            settings.get(
                "watermark_size",
                "20"
            )
        ),
    }

    success, error = run_github_workflow(inputs)

    if success:
        await update.effective_chat.send_message(
            "✅ تم تشغيل GitHub بنجاح.\n"
            "⏳ جاري معالجة الفيديو..."
        )

        context.user_data["stage"] = None

    else:
        await update.effective_chat.send_message(
            f"❌ حدث خطأ أثناء تشغيل GitHub:\n{error}"
        )


# =========================
# FONT SETTINGS
# =========================

async def font_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "📤 رفع خط",
                callback_data="font_upload"
            )
        ],
        [
            InlineKeyboardButton(
                "📐 حجم الخط",
                callback_data="font_size"
            )
        ],
        [
            InlineKeyboardButton(
                "🎨 لون الخط",
                callback_data="font_color"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ رجوع",
                callback_data="back"
            )
        ],
    ]

    await query.message.reply_text(
        "🔤 إعدادات الخط:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def font_upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["stage"] = "font_upload"

    await query.message.reply_text(
        "📤 أرسل ملف الخط TTF أو OTF.\n"
        "ويمكن أيضًا إرسال RAR يحتوي على الخط."
    )


async def handle_font_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("stage") != "font_upload":
        return

    message = update.message

    if not message.document:
        await message.reply_text(
            "❌ أرسل ملف الخط كملف."
        )
        return

    filename = (
        message.document.file_name or ""
    ).lower()

    if not (
        filename.endswith(".ttf")
        or filename.endswith(".otf")
        or filename.endswith(".rar")
    ):
        await message.reply_text(
            "❌ أرسل TTF أو OTF أو RAR."
        )
        return

    settings = get_user_settings(context)

    settings["font_message_id"] = str(
        message.message_id
    )

    save_settings(settings)

    context.user_data["stage"] = None

    await message.reply_text(
        "✅ تم حفظ الخط.\n"
        "سيُستخدم تلقائيًا في عمليات حرق الترجمة القادمة."
    )


# =========================
# SUBTITLE SETTINGS
# =========================

async def subtitle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "📐 حجم الخط",
                callback_data="font_size"
            )
        ],
        [
            InlineKeyboardButton(
                "⬛ الحواف",
                callback_data="outline"
            )
        ],
        [
            InlineKeyboardButton(
                "⬛ صندوق خلفية",
                callback_data="box"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ رجوع",
                callback_data="back"
            )
        ],
    ]

    await query.message.reply_text(
        "⚙️ إعدادات الترجمة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def font_size_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["stage"] = "font_size"

    await query.message.reply_text(
        "📐 أرسل حجم الخط، مثل:\n\n"
        "28\n"
        "30\n"
        "32"
    )


async def outline_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "بدون حواف",
                callback_data="outline_0"
            ),
            InlineKeyboardButton(
                "حواف خفيفة",
                callback_data="outline_1"
            )
        ],
        [
            InlineKeyboardButton(
                "حواف متوسطة",
                callback_data="outline_2"
            )
        ],
    ]

    await query.message.reply_text(
        "⬛ اختر سمك الحواف:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def box_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "بدون صندوق",
                callback_data="box_0"
            )
        ],
        [
            InlineKeyboardButton(
                "صندوق خلف النص",
                callback_data="box_1"
            )
        ],
    ]

    await query.message.reply_text(
        "⬛ صندوق خلف الترجمة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_settings_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stage = context.user_data.get("stage")

    if stage not in (
        "font_size",
        "font_color"
    ):
        return

    text = update.message.text.strip()

    settings = get_user_settings(context)

    if stage == "font_size":
        try:
            size = int(text)

            if size < 10 or size > 100:
                raise ValueError

            settings["font_size"] = str(size)

            save_settings(settings)

            context.user_data["stage"] = None

            await update.message.reply_text(
                f"✅ تم حفظ حجم الخط: {size}"
            )

        except Exception:
            await update.message.reply_text(
                "❌ أرسل رقمًا بين 10 و100."
            )

        return

    if stage == "font_color":
        color = text.replace("#", "").upper()

        if len(color) != 6:
            await update.message.reply_text(
                "❌ اللون يجب أن يكون HEX من 6 أحرف، مثل FFFFFF."
            )
            return

        try:
            int(color, 16)

        except ValueError:
            await update.message.reply_text(
                "❌ قيمة اللون غير صحيحة."
            )
            return

        settings["font_color"] = color

        save_settings(settings)

        context.user_data["stage"] = None

        await update.message.reply_text(
            f"✅ تم حفظ لون الخط: {color}"
        )


async def font_color_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["stage"] = "font_color"

    await query.message.reply_text(
        "🎨 أرسل لون الخط بصيغة HEX.\n\n"
        "مثال:\n"
        "FFFFFF"
    )


# =========================
# WATERMARK
# =========================

async def watermark_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "📤 رفع Watermark",
                callback_data="watermark_upload"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ تعطيل",
                callback_data="watermark_disable"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ رجوع",
                callback_data="back"
            )
        ],
    ]

    await query.message.reply_text(
        "🖼️ إعدادات Watermark:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def watermark_upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["stage"] = "watermark_upload"

    await query.message.reply_text(
        "📤 أرسل صورة الـWatermark أو RAR يحتوي عليها."
    )


async def handle_watermark_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("stage") != "watermark_upload":
        return

    message = update.message

    if not message.document and not message.photo:
        await message.reply_text(
            "❌ أرسل صورة أو ملف RAR."
        )
        return

    if message.document:
        filename = (
            message.document.file_name or ""
        ).lower()

        if not (
            filename.endswith(".rar")
            or filename.endswith(".png")
            or filename.endswith(".jpg")
            or filename.endswith(".jpeg")
            or filename.endswith(".webp")
        ):
            await message.reply_text(
                "❌ أرسل صورة أو ملف RAR."
            )
            return

    settings = get_user_settings(context)

    settings["watermark_enabled"] = "1"
    settings["watermark_message_id"] = str(
        message.message_id
    )

    save_settings(settings)

    context.user_data["stage"] = None

    await message.reply_text(
        "✅ تم حفظ الـWatermark وتفعيله."
    )


# =========================
# DOCUMENT / PHOTO ROUTER
# =========================

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stage = context.user_data.get("stage")

    if stage == "subtitle_video":
        await handle_video(update, context)
        return

    if stage == "subtitle_file":
        await handle_subtitle(update, context)
        return

    if stage == "font_upload":
        await handle_font_upload(update, context)
        return

    if stage == "watermark_upload":
        await handle_watermark_upload(update, context)
        return


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("stage") == "watermark_upload":
        await handle_watermark_upload(update, context)


# =========================
# CALLBACKS
# =========================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "subtitle":
        await subtitle_start(update, context)

    elif data == "font_settings":
        await font_settings(update, context)

    elif data == "subtitle_settings":
        await subtitle_settings(update, context)

    elif data == "watermark":
        await watermark_menu(update, context)

    elif data == "font_upload":
        await font_upload_start(update, context)

    elif data == "font_size":
        await font_size_start(update, context)

    elif data == "font_color":
        await font_color_start(update, context)

    elif data == "outline":
        await outline_start(update, context)

    elif data == "box":
        await box_start(update, context)

    elif data == "watermark_upload":
        await watermark_upload_start(update, context)

    elif data == "watermark_disable":
        settings = get_user_settings(context)

        settings["watermark_enabled"] = "0"

        save_settings(settings)

        await query.answer()

        await query.message.reply_text(
            "✅ تم تعطيل الـWatermark."
        )

    elif data.startswith("outline_"):
        value = data.split("_", 1)[1]

        settings = get_user_settings(context)

        settings["subtitle_outline"] = value

        save_settings(settings)

        await query.answer()

        await query.message.reply_text(
            "✅ تم حفظ إعداد الحواف."
        )

    elif data.startswith("box_"):
        value = data.split("_", 1)[1]

        settings = get_user_settings(context)

        settings["subtitle_box"] = value

        save_settings(settings)

        await query.answer()

        await query.message.reply_text(
            "✅ تم حفظ إعداد الصندوق."
        )

    elif data == "back":
        await query.answer()

        await query.message.reply_text(
            "🎬 القائمة الرئيسية:",
            reply_markup=main_menu()
        )

    else:
        await query.answer()


# =========================
# MAIN
# =========================

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN غير موجود في متغيرات البيئة."
        )

    if not GH_TOKEN:
        print(
            "⚠️ تحذير: GH_TOKEN غير موجود. "
            "البوت سيعمل لكن تشغيل GitHub لن يعمل."
        )

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # Buttons
    app.add_handler(
        CallbackQueryHandler(
            callback_handler
        )
    )

    # Videos
    app.add_handler(
        MessageHandler(
            filters.VIDEO,
            handle_video
        )
    )

    # Documents
    # Router واحد حتى لا يمنع Handler سابق
    # وصول الرسالة إلى المعالج الصحيح.
    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            handle_document
        )
    )

    # Photos
    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            handle_photo
        )
    )

    # Text
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_settings_text
        )
    )

    print("🤖 البوت يعمل...")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
