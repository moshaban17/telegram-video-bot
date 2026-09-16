import os
import json
import requests
from pathlib import Path

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
SETTINGS_FILE = Path("settings.json")

DEFAULT_SETTINGS = {
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


def load_settings():
    if not SETTINGS_FILE.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        data = json.loads(
            SETTINGS_FILE.read_text(encoding="utf-8")
        )
        settings = DEFAULT_SETTINGS.copy()
        settings.update(data)
        return settings
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


def workflow_url():
    return (
        f"https://api.github.com/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/"
        f"{WORKFLOW_FILE}/dispatches"
    )


def start_workflow(inputs):
    if not GH_TOKEN:
        raise RuntimeError("GH_TOKEN غير موجود.")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GH_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }

    payload = {
        "ref": "main",
        "inputs": {
            str(k): str(v)
            for k, v in inputs.items()
        },
    }

    response = requests.post(
        workflow_url(),
        headers=headers,
        json=payload,
        timeout=30,
    )

    if response.status_code not in (200, 201, 204):
        raise RuntimeError(
            f"HTTP {response.status_code}\n"
            f"{response.text[:4000]}"
        )


def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📝 حرق ترجمة",
                callback_data="burn"
            )
        ],
        [
            InlineKeyboardButton(
                "🔤 إعدادات الخط",
                callback_data="font_settings"
            )
        ],
        [
            InlineKeyboardButton(
                "⚙️ إعدادات الترجمة",
                callback_data="subtitle_settings"
            )
        ],
        [
            InlineKeyboardButton(
                "🖼️ العلامة المائية",
                callback_data="watermark_settings"
            )
        ],
    ])


def back_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬅️ القائمة الرئيسية",
                callback_data="home"
            )
        ]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "🎬 بوت معالجة الفيديو\n\n"
        "اختار الوظيفة المطلوبة:",
        reply_markup=main_menu()
    )


async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "home":
        context.user_data.clear()

        await query.edit_message_text(
            "🎬 بوت معالجة الفيديو\n\n"
            "اختار الوظيفة المطلوبة:",
            reply_markup=main_menu()
        )
        return

    if data == "burn":
        context.user_data.clear()
        context.user_data["stage"] = "video"

        await query.edit_message_text(
            "📝 حرق الترجمة\n\n"
            "أرسل الفيديو أولًا كفيديو أو كملف.",
            reply_markup=back_menu()
        )
        return

    if data == "font_settings":
        context.user_data["stage"] = "font"

        settings = load_settings()
        current = settings.get("font_message_id") or "غير مضبوط"

        await query.edit_message_text(
            "🔤 إعداد الخط\n\n"
            f"الحالة: {current}\n\n"
            "أرسل ملف الخط:\n"
            "TTF أو OTF أو RAR",
            reply_markup=back_menu()
        )
        return

    if data == "subtitle_settings":
        settings = load_settings()

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"🔠 الحجم: {settings['font_size']}",
                    callback_data="font_size"
                )
            ],
            [
                InlineKeyboardButton(
                    f"▫️ الحواف: {settings['subtitle_outline']}",
                    callback_data="outline"
                )
            ],
            [
                InlineKeyboardButton(
                    f"⬛ البوكس: {settings['subtitle_box']}",
                    callback_data="box"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ رجوع",
                    callback_data="home"
                )
            ],
        ])

        await query.edit_message_text(
            "⚙️ إعدادات الترجمة:",
            reply_markup=keyboard
        )
        return

    if data == "font_size":
        context.user_data["stage"] = "font_size"

        await query.edit_message_text(
            "🔠 أرسل حجم الخط.\n\n"
            "مثال: 26",
            reply_markup=back_menu()
        )
        return

    if data == "outline":
        context.user_data["stage"] = "outline"

        await query.edit_message_text(
            "▫️ أرسل سمك الحواف.\n\n"
            "مثال:\n"
            "0 = بدون حواف\n"
            "0.5 = حواف خفيفة\n"
            "1 = حواف عادية\n"
            "2 = حواف أكبر",
            reply_markup=back_menu()
        )
        return

    if data == "box":
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⬛ تشغيل",
                    callback_data="box_on"
                ),
                InlineKeyboardButton(
                    "⬜ إيقاف",
                    callback_data="box_off"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ رجوع",
                    callback_data="subtitle_settings"
                )
            ]
        ])

        await query.edit_message_text(
            "⬛ البوكس خلف نص الترجمة فقط:",
            reply_markup=keyboard
        )
        return

    if data in ("box_on", "box_off"):
        settings = load_settings()

        settings["subtitle_box"] = (
            "on"
            if data == "box_on"
            else "off"
        )

        save_settings(settings)

        await query.edit_message_text(
            "✅ تم حفظ إعداد البوكس.",
            reply_markup=back_menu()
        )
        return

    if data == "watermark_settings":
        context.user_data["stage"] = "watermark"

        await query.edit_message_text(
            "🖼️ العلامة المائية\n\n"
            "أرسل صورة PNG/JPG/WEBP أو RAR.\n\n"
            "سيتم حفظها لاستخدامها لاحقًا.",
            reply_markup=back_menu()
        )
        return


async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stage = context.user_data.get("stage")
    text = (update.message.text or "").strip()

    if text.lower() in ("إلغاء", "الغاء", "/cancel"):
        context.user_data.clear()

        await update.message.reply_text(
            "تم الإلغاء.",
            reply_markup=main_menu()
        )
        return

    if stage == "font_size":
        if not text.isdigit():
            await update.message.reply_text(
                "❌ أرسل رقمًا فقط."
            )
            return

        size = int(text)

        if size < 8 or size > 100:
            await update.message.reply_text(
                "❌ الحجم يجب أن يكون بين 8 و100."
            )
            return

        settings = load_settings()
        settings["font_size"] = str(size)
        save_settings(settings)

        context.user_data["stage"] = None

        await update.message.reply_text(
            "✅ تم حفظ حجم الخط.",
            reply_markup=main_menu()
        )
        return

    if stage == "outline":
        try:
            value = float(text)
        except ValueError:
            await update.message.reply_text(
                "❌ أرسل رقمًا مثل 0 أو 0.5 أو 1."
            )
            return

        if value < 0 or value > 10:
            await update.message.reply_text(
                "❌ القيمة يجب أن تكون بين 0 و10."
            )
            return

        settings = load_settings()
        settings["subtitle_outline"] = str(value)
        save_settings(settings)

        context.user_data["stage"] = None

        await update.message.reply_text(
            "✅ تم حفظ الحواف.",
            reply_markup=main_menu()
        )
        return

    await update.message.reply_text(
        "اختار وظيفة من القائمة.",
        reply_markup=main_menu()
    )


async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("stage") != "video":
        return

    context.user_data["video_message_id"] = str(
        update.message.message_id
    )

    context.user_data["stage"] = "subtitle"

    await update.message.reply_text(
        "✅ تم استلام الفيديو.\n\n"
        "الآن أرسل ملف الترجمة SRT أو ASS أو SSA."
    )


async def receive_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.document:
        return

    stage = context.user_data.get("stage")
    document = message.document

    file_name = (
        document.file_name or ""
    ).lower()

    if stage == "font":
        if not file_name.endswith(
            (".ttf", ".otf", ".rar")
        ):
            await message.reply_text(
                "❌ أرسل ملف TTF أو OTF أو RAR."
            )
            return

        settings = load_settings()
        settings["font_message_id"] = str(message.message_id)
        save_settings(settings)

        context.user_data["stage"] = None

        await message.reply_text(
            "✅ تم حفظ الخط بنجاح.\n\n"
            "سيُستخدم تلقائيًا في عمليات حرق الترجمة القادمة.",
            reply_markup=main_menu()
        )
        return

    if stage == "watermark":
        if not file_name.endswith(
            (".png", ".jpg", ".jpeg", ".webp", ".rar")
        ):
            await message.reply_text(
                "❌ أرسل PNG أو JPG أو JPEG أو WEBP أو RAR."
            )
            return

        settings = load_settings()

        settings["watermark_message_id"] = str(
            message.message_id
        )
        settings["watermark_enabled"] = "true"

        save_settings(settings)

        context.user_data["stage"] = None

        await message.reply_text(
            "✅ تم حفظ العلامة المائية.",
            reply_markup=main_menu()
        )
        return

    if stage == "video":
        if file_name.endswith(
            (
                ".mp4",
                ".mkv",
                ".avi",
                ".mov",
                ".webm",
                ".m4v",
                ".ts",
                ".m2ts",
                ".mts",
            )
        ):
            context.user_data["video_message_id"] = str(
                message.message_id
            )

            context.user_data["stage"] = "subtitle"

            await message.reply_text(
                "✅ تم استلام الفيديو.\n\n"
                "الآن أرسل SRT أو ASS أو SSA."
            )
        return

    if stage == "subtitle":
        if file_name.endswith(".srt"):
            subtitle_type = "srt"
        elif file_name.endswith(".ass"):
            subtitle_type = "ass"
        elif file_name.endswith(".ssa"):
            subtitle_type = "ssa"
        else:
            await message.reply_text(
                "❌ يجب أن يكون الملف SRT أو ASS أو SSA."
            )
            return

        context.user_data["subtitle_message_id"] = str(
            message.message_id
        )

        context.user_data["subtitle_type"] = subtitle_type

        await dispatch_burn(update, context)
        return


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("stage") != "watermark":
        return

    settings = load_settings()

    settings["watermark_message_id"] = str(
        update.message.message_id
    )
    settings["watermark_enabled"] = "true"

    save_settings(settings)

    context.user_data["stage"] = None

    await update.message.reply_text(
        "✅ تم حفظ العلامة المائية.",
        reply_markup=main_menu()
    )


async def dispatch_burn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = load_settings()

    video_id = context.user_data.get(
        "video_message_id"
    )

    subtitle_id = context.user_data.get(
        "subtitle_message_id"
    )

    subtitle_type = context.user_data.get(
        "subtitle_type",
        "srt"
    )

    if not video_id or not subtitle_id:
        await update.message.reply_text(
            "❌ بيانات الفيديو أو الترجمة ناقصة."
        )
        context.user_data.clear()
        return

    inputs = {
        "chat_id": str(
            update.effective_chat.id
        ),
        "video_message_id": str(video_id),
        "subtitle_message_id": str(subtitle_id),
        "subtitle_type": str(subtitle_type),

        "font_message_id": str(
            settings.get("font_message_id", "")
        ),

        "font_size": str(
            settings.get("font_size", "26")
        ),

        "font_color": str(
            settings.get("font_color", "white")
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
            settings.get(
                "watermark_message_id",
                ""
            )
        ),

        "watermark_enabled": str(
            settings.get(
                "watermark_enabled",
                "false"
            )
        ),

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

    await update.message.reply_text(
        "⏳ جاري تشغيل GitHub وحرق الترجمة..."
    )

    try:
        start_workflow(inputs)

    except Exception as exc:
        await update.message.reply_text(
            "❌ فشل تشغيل GitHub.\n\n"
            f"{exc}"
        )

        context.user_data.clear()
        return

    context.user_data.clear()

    await update.message.reply_text(
        "✅ تم تشغيل GitHub بنجاح.\n\n"
        "🎬 بدأت معالجة الفيديو وحرق الترجمة.\n"
        "📤 سيصل الفيديو هنا بعد الانتهاء."
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN غير موجود."
        )

    app = (
        Application.builder()
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
            callbacks
        )
    )

    app.add_handler(
        MessageHandler(
            filters.VIDEO & filters.ChatType.PRIVATE,
            receive_video
        )
    )

    app.add_handler(
        MessageHandler(
            filters.Document.ALL &
            filters.ChatType.PRIVATE,
            receive_document
        )
    )

    app.add_handler(
        MessageHandler(
            filters.PHOTO &
            filters.ChatType.PRIVATE,
            receive_photo
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT &
            ~filters.COMMAND &
            filters.ChatType.PRIVATE,
            receive_text
        )
    )

    print("🤖 البوت يعمل...")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
