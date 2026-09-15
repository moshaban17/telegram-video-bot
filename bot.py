import os
import json
from pathlib import Path
import requests

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


def main_menu():
    keyboard = [
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
                "🎙️ صوت → SRT",
                callback_data="speech"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔊 إدارة الصوت",
                callback_data="audio"
            ),
            InlineKeyboardButton(
                "📦 استخراج ترجمة",
                callback_data="extract"
            ),
        ],
        [
            InlineKeyboardButton(
                "🖼️ Watermark",
                callback_data="watermark"
            ),
            InlineKeyboardButton(
                "🔗 ملف → رابط",
                callback_data="file_link"
            ),
        ],
        [
            InlineKeyboardButton(
                "👁️ كلام الشاشة → SRT",
                callback_data="ocr"
            ),
        ],
        [
            InlineKeyboardButton(
                "🌐 ترجمة SRT",
                callback_data="translate_srt"
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.clear()

    await update.message.reply_text(
        "🎬 أهلاً بك في بوت معالجة الفيديو.\n\n"
        "اختار الوظيفة المطلوبة:",
        reply_markup=main_menu(),
    )


async def menu_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    if query.data == "ocr":
        context.user_data["mode"] = "ocr"
        await query.edit_message_text(
            "👁️ كلام الشاشة → SRT\n\n"
            "🔗 ابعت الآن رابط الفيديو المباشر."
        )

    elif query.data.startswith("res_"):

        resolution = query.data.replace("res_", "", 1)
        video_url = context.user_data.get("video_url")

        if not video_url:
            await query.edit_message_text(
                "❌ لم يتم العثور على رابط الفيديو.\n\n"
                "ابدأ من جديد من القائمة."
            )
            return

        if not GH_TOKEN:
            await query.edit_message_text(
                "❌ GH_TOKEN غير موجود."
            )
            return

        chat_id = update.effective_chat.id

        await query.edit_message_text(
            f"✅ تم اختيار الدقة: {resolution}\n\n"
            "🚀 جاري تشغيل GitHub لمعالجة الفيديو..."
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
                    "✅ بدأ تحميل الفيديو.\n\n"
                    "📥 GitHub يقوم الآن بمعالجة الفيديو.\n"
                    "📤 عند الانتهاء سيصل الناتج هنا."
                )
            else:
                await query.message.reply_text(
                    "❌ فشل تشغيل GitHub.\n\n"
                    f"كود الخطأ: {response.status_code}\n"
                    f"{response.text[:500]}"
                )

        except Exception as e:
            await query.message.reply_text(
                "❌ حدث خطأ أثناء تشغيل GitHub:\n\n"
                f"{e}"
            )

        return

    elif query.data == "download":

        context.user_data["mode"] = "download"

        await query.edit_message_text(
            "🔗 ابعت الآن رابط الفيديو المباشر."
        )

    elif query.data == "convert":

        context.user_data["mode"] = "convert"

        await query.edit_message_text(
            "🎬 ابعت رابط الفيديو."
        )

    elif query.data == "translate_srt":

        context.user_data["mode"] = "translate_srt"

        await query.edit_message_text(
            "🌐 ترجمة SRT إلى العربية الفصحى\n\n"
            "📄 ابعت الآن ملف SRT."
        )

    elif query.data == "subtitle":

        context.user_data["mode"] = "subtitle"

        keyboard = [
            [
                InlineKeyboardButton("🔤 الخط", callback_data="burn_font"),
                InlineKeyboardButton("🔠 حجم الخط", callback_data="burn_size"),
            ],
            [
                InlineKeyboardButton("🎨 لون الترجمة", callback_data="burn_color"),
                InlineKeyboardButton("⬛ البوكس", callback_data="burn_box"),
            ],
            [
                InlineKeyboardButton("▫️ الحواف", callback_data="burn_outline"),
                InlineKeyboardButton("🖼️ العلامة المائية", callback_data="burn_watermark"),
            ],
            [
                InlineKeyboardButton("🎬 ابدأ الحرق", callback_data="burn_start"),
            ],
        ]

        await query.edit_message_text(
            "📝 إعدادات حرق الترجمة\n\n"
            "⚙️ اختار الإعداد الذي تريد تغييره:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "burn_font":

        context.user_data["waiting_for_font"] = True

        await query.edit_message_text(
            "🔤 إعداد الخط\n\n"
            "📎 ابعت الآن ملف الخط TTF أو OTF أو RAR."
        )
        return

    elif query.data == "burn_size":

        keyboard = [
            [
                InlineKeyboardButton("20", callback_data="burn_size_20"),
                InlineKeyboardButton("24", callback_data="burn_size_24"),
                InlineKeyboardButton("26", callback_data="burn_size_26"),
            ],
            [
                InlineKeyboardButton("28", callback_data="burn_size_28"),
                InlineKeyboardButton("32", callback_data="burn_size_32"),
                InlineKeyboardButton("36", callback_data="burn_size_36"),
            ],
            [
                InlineKeyboardButton("40", callback_data="burn_size_40"),
            ],
            [
                InlineKeyboardButton("⬅️ رجوع", callback_data="subtitle"),
            ],
        ]

        await query.edit_message_text(
            "🔠 حجم الخط\n\n"
            "اختار حجم الخط:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    elif query.data.startswith("burn_size_"):

        size = query.data.replace("burn_size_", "")

        settings_path = Path("settings.json")
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
            except Exception:
                settings = {}
        else:
            settings = {}

        settings["font_size"] = size

        settings_path.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2)
        )

        context.user_data["font_size"] = size

        await query.answer(f"✅ تم اختيار حجم {size}")

        await query.edit_message_text(
            f"🔠 تم حفظ حجم الخط: {size}\n\n"
            "⬅️ ارجع إلى إعدادات حرق الترجمة.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ رجوع",
                        callback_data="subtitle"
                    )
                ]
            ]),
        )
        return

    elif query.data == "burn_color":

        keyboard = [
            [
                InlineKeyboardButton("⚪ أبيض", callback_data="burn_color_white"),
                InlineKeyboardButton("🟡 أصفر", callback_data="burn_color_yellow"),
            ],
            [
                InlineKeyboardButton("🔵 سماوي", callback_data="burn_color_cyan"),
                InlineKeyboardButton("🟢 أخضر", callback_data="burn_color_green"),
            ],
            [
                InlineKeyboardButton("🔴 أحمر", callback_data="burn_color_red"),
            ],
            [
                InlineKeyboardButton("⬅️ رجوع", callback_data="subtitle"),
            ],
        ]

        await query.edit_message_text(
            "🎨 لون الترجمة\n\n"
            "اختار لون الترجمة:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    elif query.data.startswith("burn_color_"):

        color = query.data.replace("burn_color_", "")

        settings_path = Path("settings.json")
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
            except Exception:
                settings = {}
        else:
            settings = {}

        settings["font_color"] = color

        settings_path.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2)
        )

        context.user_data["font_color"] = color

        await query.answer("✅ تم حفظ لون الترجمة")

        await query.edit_message_text(
            f"🎨 تم حفظ لون الترجمة: {color}\n\n"
            "⬅️ ارجع إلى إعدادات حرق الترجمة.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ رجوع",
                        callback_data="subtitle"
                    )
                ]
            ]),
        )
        return

    elif query.data == "burn_box":

        keyboard = [
            [
                InlineKeyboardButton("⬛ تشغيل البوكس", callback_data="burn_box_on"),
                InlineKeyboardButton("⬜ إيقاف البوكس", callback_data="burn_box_off"),
            ],
            [
                InlineKeyboardButton("⬅️ رجوع", callback_data="subtitle"),
            ],
        ]

        await query.edit_message_text(
            "⬛ البوكس\n\n"
            "البوكس يظهر خلف نص SRT فقط ويختفي مع اختفاء السطر.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    elif query.data in ("burn_box_on", "burn_box_off"):

        box = "on" if query.data == "burn_box_on" else "off"

        settings_path = Path("settings.json")
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
            except Exception:
                settings = {}
        else:
            settings = {}

        settings["subtitle_box"] = box

        settings_path.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2)
        )

        context.user_data["subtitle_box"] = box

        await query.answer("✅ تم حفظ إعداد البوكس")

        await query.edit_message_text(
            f"⬛ البوكس: {'تشغيل' if box == 'on' else 'إيقاف'}",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ رجوع",
                        callback_data="subtitle"
                    )
                ]
            ]),
        )
        return

    elif query.data == "burn_outline":

        keyboard = [
            [
                InlineKeyboardButton("بدون حواف", callback_data="burn_outline_0"),
                InlineKeyboardButton("0.5", callback_data="burn_outline_0.5"),
            ],
            [
                InlineKeyboardButton("1", callback_data="burn_outline_1"),
                InlineKeyboardButton("2", callback_data="burn_outline_2"),
            ],
            [
                InlineKeyboardButton("⬅️ رجوع", callback_data="subtitle"),
            ],
        ]

        await query.edit_message_text(
            "▫️ حواف الترجمة\n\n"
            "اختار سمك الحواف:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    elif query.data.startswith("burn_outline_"):

        outline = query.data.replace("burn_outline_", "")

        settings_path = Path("settings.json")
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
            except Exception:
                settings = {}
        else:
            settings = {}

        settings["subtitle_outline"] = outline

        settings_path.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2)
        )

        context.user_data["subtitle_outline"] = outline

        await query.answer("✅ تم حفظ الحواف")

        await query.edit_message_text(
            f"▫️ تم حفظ الحواف: {outline}",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ رجوع",
                        callback_data="subtitle"
                    )
                ]
            ]),
        )
        return

    elif query.data == "burn_watermark":

        keyboard = [
            [
                InlineKeyboardButton(
                    "📎 رفع/تغيير العلامة",
                    callback_data="wm_upload"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📍 الموضع والحجم",
                    callback_data="watermark_settings"
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ رجوع",
                    callback_data="subtitle"
                ),
            ],
        ]

        await query.edit_message_text(
            "🖼️ إعدادات العلامة المائية\n\n"
            "📎 يمكنك رفع أو تغيير العلامة المائية.\n"
            "📍 ويمكنك تحديد موضعها وحجمها.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    elif query.data == "wm_upload":

        context.user_data["waiting_for_watermark"] = True

        await query.edit_message_text(
            "📎 أرسل الآن ملف العلامة المائية.\n\n"
            "المسموح: PNG / JPG / JPEG / WEBP / RAR\n\n"
            "⚠️ أرسل PNG كـ «ملف» للحفاظ على الشفافية."
        )
        return

    elif query.data == "watermark_settings":

        keyboard = [
            [
                InlineKeyboardButton("↖️ أعلى اليسار", callback_data="wm_pos_top_left"),
                InlineKeyboardButton("↗️ أعلى اليمين", callback_data="wm_pos_top_right"),
            ],
            [
                InlineKeyboardButton("↙️ أسفل اليسار", callback_data="wm_pos_bottom_left"),
                InlineKeyboardButton("↘️ أسفل اليمين", callback_data="wm_pos_bottom_right"),
            ],
            [
                InlineKeyboardButton("📏 الحجم", callback_data="wm_size"),
            ],
            [
                InlineKeyboardButton("🟢 تشغيل", callback_data="wm_enable"),
                InlineKeyboardButton("🔴 إيقاف", callback_data="wm_disable"),
            ],
            [
                InlineKeyboardButton("⬅️ رجوع", callback_data="burn_watermark"),
            ],
        ]

        await query.edit_message_text(
            "📍 إعدادات العلامة المائية\n\n"
            "اختر الموضع أو الحجم أو تشغيل/إيقاف العلامة.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    elif query.data in ("wm_enable", "wm_disable"):

        enabled = query.data == "wm_enable"
        settings_path = Path("settings.json")

        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
            except Exception:
                settings = {}
        else:
            settings = {}

        settings["watermark_enabled"] = enabled

        settings_path.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2)
        )

        context.user_data["watermark_enabled"] = enabled

        await query.answer(
            "✅ تم تشغيل العلامة المائية"
            if enabled else
            "✅ تم إيقاف العلامة المائية"
        )

        await query.edit_message_text(
            "🖼️ العلامة المائية\n\n"
            + ("🟢 الحالة: تشغيل" if enabled else "🔴 الحالة: إيقاف"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⬅️ رجوع",
                    callback_data="watermark_settings"
                )]
            ]),
        )
        return

    elif query.data.startswith("wm_pos_"):

        position = query.data.replace("wm_pos_", "", 1)
        settings_path = Path("settings.json")

        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
            except Exception:
                settings = {}
        else:
            settings = {}

        settings["watermark_position"] = position

        settings_path.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2)
        )

        context.user_data["watermark_position"] = position

        await query.answer("✅ تم حفظ الموضع")
        await query.edit_message_text(
            "✅ تم حفظ موضع العلامة المائية.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⬅️ رجوع",
                    callback_data="watermark_settings"
                )]
            ]),
        )
        return

    elif query.data == "wm_size":

        keyboard = [
            [
                InlineKeyboardButton("10%", callback_data="wm_size_10"),
                InlineKeyboardButton("15%", callback_data="wm_size_15"),
            ],
            [
                InlineKeyboardButton("20%", callback_data="wm_size_20"),
                InlineKeyboardButton("25%", callback_data="wm_size_25"),
            ],
            [
                InlineKeyboardButton("30%", callback_data="wm_size_30"),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ رجوع",
                    callback_data="watermark_settings"
                ),
            ],
        ]

        await query.edit_message_text(
            "📏 اختر حجم العلامة المائية:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    elif query.data.startswith("wm_size_"):

        size = query.data.replace("wm_size_", "", 1)
        settings_path = Path("settings.json")

        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
            except Exception:
                settings = {}
        else:
            settings = {}

        settings["watermark_size"] = size

        settings_path.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2)
        )

        context.user_data["watermark_size"] = size

        await query.answer("✅ تم حفظ الحجم")
        await query.edit_message_text(
            f"✅ تم حفظ حجم العلامة المائية: {size}%",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⬅️ رجوع",
                    callback_data="watermark_settings"
                )]
            ]),
        )
        return

    elif query.data == "burn_start":

        await query.message.reply_text(
            "🟢 تم الوصول إلى burn_start\n\n"
            f"video_received = {context.user_data.get('video_received')}\n"
            f"subtitle_received = {context.user_data.get('subtitle_received')}\n"
            f"video_message_id = {context.user_data.get('video_message_id')}\n"
            f"subtitle_message_id = {context.user_data.get('subtitle_message_id')}"
        )

        if not context.user_data.get("video_received"):
            await query.answer(
                "❌ الفيديو غير محفوظ في الجلسة الحالية.",
                show_alert=True
            )
            return

        if not context.user_data.get("subtitle_received"):
            await query.answer(
                "❌ الترجمة غير محفوظة في الجلسة الحالية.",
                show_alert=True
            )
            return

        if not context.user_data.get("video_message_id"):
            await query.answer(
                "❌ لم يتم حفظ رقم رسالة الفيديو.",
                show_alert=True
            )
            return

        if not context.user_data.get("subtitle_message_id"):
            await query.answer(
                "❌ لم يتم حفظ رقم رسالة الترجمة.",
                show_alert=True
            )
            return

        await query.answer("⏳ جاري التشغيل...")

        await query.message.reply_text(
            "🎬 جاري تجهيز عملية حرق الترجمة...\n\n"
            "🚀 سيتم تشغيل GitHub لمعالجة الفيلم."
        )

        if False:
            await query.answer("❌ ابعت الفيلم أولًا.", show_alert=True)
            return

        if not context.user_data.get("subtitle_received"):
            await query.answer("❌ ابعت ملف الترجمة أولًا.", show_alert=True)
            return

        video_message_id = context.user_data.get("video_message_id")
        subtitle_message_id = context.user_data.get("subtitle_message_id")

        settings_path = Path("settings.json")
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
            except Exception:
                settings = {}
        else:
            settings = {}

        watermark_enabled = settings.get("watermark_enabled", False)

        await query.answer()

        await query.edit_message_text(
            "🎬 جاري تجهيز عملية حرق الترجمة...\n\n"
            "🚀 سيتم تشغيل GitHub لمعالجة الفيلم."
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
                "chat_id": str(update.effective_chat.id),
                "telegram_message_id": str(video_message_id or ""),
                "telegram_message_date": str(context.user_data.get("video_message_date", "")),
                "subtitle_message_id": str(subtitle_message_id or ""),
                "subtitle_message_date": str(context.user_data.get("subtitle_message_date", "")),
                "subtitle_type": context.user_data.get(
                    "subtitle_type",
                    settings.get("subtitle_type", "srt")
                ),
                "font_message_id": str(
                    settings.get("font_message_id", "")
                ),
                "font_size": str(
                    settings.get("font_size", "26")
                ),
                "font_color": settings.get(
                    "font_color", "white"
                ),
                "subtitle_outline": str(
                    settings.get("subtitle_outline", "0.5")
                ),
                "subtitle_box": settings.get(
                    "subtitle_box", "off"
                ),
                "watermark_message_id": str(
                    settings.get("watermark_message_id", "")
                    if watermark_enabled else ""
                ),
                "watermark_position": settings.get(
                    "watermark_position", "top_left"
                ),
                "watermark_size": str(
                    settings.get("watermark_size", "20")
                ),
                "watermark_enabled": str(
                    watermark_enabled
                ).lower(),
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
                    "✅ تم تشغيل GitHub بنجاح.\n\n"
                    "🎬 جاري حرق الترجمة بالإعدادات المحفوظة.\n"
                    "📤 سيصل الفيديو هنا بعد الانتهاء."
                )
            else:
                await query.message.reply_text(
                    "❌ فشل تشغيل GitHub.\n\n"
                    f"كود الخطأ: {response.status_code}\n"
                    f"{response.text[:500]}"
                )

        except Exception as e:
            await query.message.reply_text(
                f"❌ حدث خطأ أثناء تشغيل GitHub:\n\n{e}"
            )

        return

    elif query.data == "speech":
        context.user_data["mode"] = "speech"

        await query.edit_message_text(
            "🎙️ ابعت الفيديو أو الملف الصوتي لتحويل الكلام إلى SRT."
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


async def receive_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    text = (update.message.text or "").strip()

    mode = context.user_data.get("mode")

    if mode not in ("download", "convert"):

        await update.message.reply_text(
            "اختار وظيفة من القائمة أولًا:",
            reply_markup=main_menu(),
        )

        return

    if not (
        text.startswith("http://")
        or text.startswith("https://")
    ):

        await update.message.reply_text(
            "❌ الرابط غير صحيح.\n\n"
            "ابعت رابط الفيديو المباشر."
        )

        return

    if not GH_TOKEN:

        await update.message.reply_text(
            "❌ GH_TOKEN غير موجود."
        )

        return

    context.user_data["video_url"] = text

    keyboard = [
        [
            InlineKeyboardButton("نفس الدقة", callback_data="res_same"),
            InlineKeyboardButton("1080p", callback_data="res_1080p"),
        ],
        [
            InlineKeyboardButton("720p", callback_data="res_720p"),
            InlineKeyboardButton("480p", callback_data="res_480p"),
        ],
        [
            InlineKeyboardButton("360p", callback_data="res_360p"),
        ],
    ]

    await update.message.reply_text(
        "✅ تم استلام الرابط.\n\n"
        "🎬 اختار الدقة المطلوبة:",
        reply_markup=InlineKeyboardMarkup(keyboard),
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
            "video_url": text,
            "subtitle_url": "",
            "resolution": "same",
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
                "✅ بدأ تحميل الفيديو من الرابط.\n\n"
                "📥 GitHub يقوم الآن بتحميل الفيديو.\n"
                "📤 بعد الانتهاء سيصل الفيديو هنا."
            )

        else:

            await update.message.reply_text(
                "❌ فشل تشغيل GitHub.\n\n"
                f"كود الخطأ: {response.status_code}\n"
                f"{response.text[:500]}"
            )

    except Exception as e:

        await update.message.reply_text(
            "❌ حدث خطأ أثناء تشغيل GitHub:\n\n"
            f"{e}"
        )


async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")

    await update.message.reply_text(
        f"🔎 وضع التشغيل الحالي: {mode}"
    )

    if mode == "subtitle":
        context.user_data["video_message_id"] = update.message.message_id
        context.user_data["video_message_date"] = update.message.date.isoformat()
        context.user_data["video_received"] = True
        await update.message.reply_text("✅ تم استلام الفيلم.\n\n📝 الآن ابعت ملف الترجمة SRT أو ASS.")
        return

    if mode not in ("download", "convert", "ocr", "speech", "subtitle"):
        await update.message.reply_text(
            "اختار وظيفة من القائمة أولًا:",
            reply_markup=main_menu(),
        )
        return

    if not GH_TOKEN:
        await update.message.reply_text("❌ GH_TOKEN غير موجود.")
        return

    chat_id = update.effective_chat.id
    message_id = update.message.message_id

    if mode == "ocr":
        operation = "video_ocr"
    elif mode == "speech":
        operation = "audio_srt"
    else:
        operation = "video"

    await update.message.reply_text(
        "⏳ تم استلام الفيديو.\n\n"
        "🚀 جاري تشغيل GitHub لمعالجة الفيديو..."
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
            "srt_file_id": "",
            "telegram_message_id": str(message_id),
            "source_type": "telegram",
            "operation": operation,
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
                "✅ بدأ GitHub معالجة الفيديو.\n\n"
                "📥 سيتم تحميل الفيديو من تيليجرام.\n"
                "📤 وبعد الانتهاء سيصل الناتج هنا."
            )
        else:
            await update.message.reply_text(
                "❌ فشل تشغيل GitHub.\n\n"
                f"كود الخطأ: {response.status_code}\n"
                f"{response.text[:500]}"
            )

    except Exception as e:
        await update.message.reply_text(
            f"❌ حدث خطأ أثناء تشغيل GitHub:\n\n{e}"
        )


async def receive_document(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    mode = context.user_data.get("mode")
    document = update.message.document

    if not document:
        return

    file_name = document.file_name or ""

    if context.user_data.get("waiting_for_watermark"):
        if not file_name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".rar")):
            await update.message.reply_text(
                "❌ ابعت صورة بصيغة PNG أو JPG أو WEBP، أو ملف RAR."
            )
            return

        settings_path = Path("settings.json")

        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
            except Exception:
                settings = {}
        else:
            settings = {}

        settings["watermark_file_id"] = document.file_id
        settings["watermark_file_name"] = file_name
        settings["watermark_message_id"] = update.message.message_id
        settings["watermark_position"] = settings.get(
            "watermark_position", "top_left"
        )
        settings["watermark_size"] = settings.get(
            "watermark_size", "20"
        )

        settings_path.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2)
        )

        context.user_data["waiting_for_watermark"] = False
        context.user_data["watermark_file_id"] = document.file_id
        context.user_data["watermark_message_id"] = update.message.message_id

        await update.message.reply_text(
            "✅ تم حفظ العلامة المائية بنجاح.\n\n"
            f"🖼️ الملف: {file_name}\n"
            "📍 الموضع الافتراضي: أعلى اليسار\n"
            "📏 الحجم الافتراضي: 20%\n\n"
            "♻️ سيُستخدم تلقائيًا في عمليات الحرق القادمة."
        )
        return

    if context.user_data.get("waiting_for_font"):
        if not file_name.lower().endswith((".ttf", ".otf", ".rar")):
            await update.message.reply_text(
                "❌ ابعت ملف الخط بصيغة TTF أو OTF أو RAR."
            )
            return

        settings_path = Path("settings.json")

        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
            except Exception:
                settings = {}
        else:
            settings = {}

        settings["font_file_id"] = document.file_id
        settings["font_file_name"] = file_name
        settings["font_message_id"] = update.message.message_id

        settings_path.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2)
        )

        context.user_data["waiting_for_font"] = False
        context.user_data["font_file_id"] = document.file_id
        context.user_data["font_message_id"] = update.message.message_id

        await update.message.reply_text(
            "✅ تم حفظ ملف الخط بنجاح.\n\n"
            f"🔤 الملف: {file_name}\n"
            "♻️ سيُستخدم تلقائيًا في عمليات الحرق القادمة."
        )
        return

    if mode == "subtitle":
        if not (
            file_name.lower().endswith(".srt")
            or file_name.lower().endswith(".ass")
            or file_name.lower().endswith(".ssa")
        ):
            await update.message.reply_text(
                "❌ ابعت ملف ترجمة بصيغة SRT أو ASS."
            )
            return

        context.user_data["srt_file_id"] = document.file_id
        context.user_data["subtitle_message_id"] = update.message.message_id
        context.user_data["subtitle_message_date"] = update.message.date.isoformat()
        context.user_data["subtitle_received"] = True
        context.user_data["subtitle_type"] = (
            "ass"
            if file_name.lower().endswith((".ass", ".ssa"))
            else "srt"
        )

        chat_id = update.effective_chat.id
        video_message_id = context.user_data.get("video_message_id")
        subtitle_type = context.user_data["subtitle_type"]

        await update.message.reply_text(
            "✅ تم استلام ملف الترجمة.\n\n"
            "🎬 اضغط «ابدأ الحرق» من قائمة إعدادات حرق الترجمة عندما تكون جاهزًا."
        )

        return

        return

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
                "❌ فشل تشغيل الترجمة.\n\n"
                f"كود الخطأ: {response.status_code}\n"
                f"{response.text[:500]}"
            )

    except Exception as e:

        await update.message.reply_text(
            "❌ حدث خطأ:\n\n"
            f"{e}"
        )


def main():

    if not BOT_TOKEN:

        print("❌ BOT_TOKEN غير موجود.")

        return

    app = Application.builder().token(
        BOT_TOKEN
    ).build()

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









