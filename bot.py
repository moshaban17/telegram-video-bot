import os
import json
from pathlib import Path
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
GH_TOKEN = os.getenv("GH_TOKEN")
GITHUB_OWNER = "moshaban17"
GITHUB_REPO = "telegram-video-bot"
WORKFLOW_FILE = "process.yml"
SETTINGS_FILE = Path("settings.json")

def load_settings():
    if not SETTINGS_FILE.exists(): return {}
    try: return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except: return {}

def save_settings(settings):
    SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
def workflow_url():
    return f"https://github.com{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"

def github_headers():
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GH_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

def dispatch_workflow(inputs):
    if not GH_TOKEN: return None, "GH_TOKEN غير موجود."
    clean_inputs = {}
    for key, value in inputs.items():
        if value is None or str(value).strip() == "":
            value = ""
        clean_inputs[str(key)] = str(value)
    payload = {"ref": "main", "inputs": clean_inputs}
    try:
        response = requests.post(workflow_url(), headers=github_headers(), json=payload, timeout=30)
        return response, None
    except Exception as exc:
        return None, str(exc)
def github_success(response):
    return response is not None and response.status_code in (200, 201, 202, 204)

def github_error_text(response):
    if response is None: return "لا توجد استجابة من GitHub."
    try: return response.text[:1000]
    except: return f"HTTP {response.status_code}"

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🔗 تحميل من رابط", callback_data="download"), InlineKeyboardButton("🎬 تحويل دقة", callback_data="convert")],
        [InlineKeyboardButton("📝 حرق ترجمة", callback_data="subtitle"), InlineKeyboardButton("🎙️ صوت → SRT", callback_data="speech")],
        [InlineKeyboardButton("🔊 إدارة الصوت", callback_data="audio"), InlineKeyboardButton("📦 استخراج ترجمة", callback_data="extract")],
        [InlineKeyboardButton("🖼️ Watermark", callback_data="watermark"), InlineKeyboardButton("🔗 ملف → رابط", callback_data="file_link")],
        [InlineKeyboardButton("👁️ كلام الشاشة → SRT", callback_data="ocr")],
        [InlineKeyboardButton("🌐 ترجمة SRT", callback_data="translate_srt")],
    ]
    return InlineKeyboardMarkup(keyboard)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🎬 أهلاً بك في بوت معالجة الفيديو.\n\nاختار الوظيفة المطلوبة:", reply_markup=main_menu())

def subtitle_menu():
    keyboard = [
        [InlineKeyboardButton("🔤 الخط", callback_data="burn_font"), InlineKeyboardButton("🔠 حجم الخط", callback_data="burn_size")],
        [InlineKeyboardButton("🎨 لون الترجمة", callback_data="burn_color"), InlineKeyboardButton("⬛ البوكس", callback_data="burn_box")],
        [InlineKeyboardButton("▫️ الحواف", callback_data="burn_outline"), InlineKeyboardButton("🖼️ العلامة المائية", callback_data="burn_watermark")],
        [InlineKeyboardButton("🎬 ابدأ الحرق", callback_data="burn_start")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def resolution_menu():
    keyboard = [
        [InlineKeyboardButton("نفس الدقة", callback_data="res_same"), InlineKeyboardButton("1080p", callback_data="res_1080p")],
        [InlineKeyboardButton("720p", callback_data="res_720p"), InlineKeyboardButton("480p", callback_data="res_480p")],
        [InlineKeyboardButton("360p", callback_data="res_360p")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)
async def menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        context.user_data.clear()
        await query.edit_message_text("🎬 القائمة الرئيسية\n\nاختار الوظيفة المطلوبة:", reply_markup=main_menu())
        return
    if data == "ocr":
        context.user_data.clear()
        context.user_data["mode"] = "ocr"
        await query.edit_message_text("👁️ كلام الشاشة → SRT\n\n🔗 ابعت الآن رابط الفيديو المباشر.")
        return
    if data == "download":
        context.user_data.clear()
        context.user_data["mode"] = "download"
        await query.edit_message_text("🔗 ابعت الآن رابط الفيديو المباشر.")
        return
    if data == "convert":
        context.user_data.clear()
        context.user_data["mode"] = "convert"
        await query.edit_message_text("🎬 ابعت رابط الفيديو.")
        return

    if data.startswith("res_"):
        resolution = data.replace("res_", "", 1)
        video_url = context.user_data.get("video_url")
        if not video_url:
            await query.edit_message_text("❌ لم يتم العثور على رابط الفيديو.\n\nابدأ من جديد من القائمة.")
            return
        await query.edit_message_text(f"✅ تم اختيار الدقة: {resolution}\n\n🚀 جاري تشغيل GitHub لمعالجة الفيديو...")
        inputs = {"video_url": video_url, "subtitle_url": "", "resolution": resolution, "chat_id": update.effective_chat.id, "operation": "video"}
        response, error = dispatch_workflow(inputs)
        if error:
            await query.message.reply_text(f"❌ حدث خطأ أثناء تشغيل GitHub:\n\n{error}")
            return
        if github_success(response):
            await query.message.reply_text("✅ بدأ تحميل الفيديو.\n\n📥 GitHub يقوم الآن بمعالجة الفيديو.\n📤 عند الانتهاء سيصل الناتج هنا.")
        else:
            await query.message.reply_text(f"❌ فشل تشغيل GitHub.\n\nكود الخطأ: {response.status_code}\n{github_error_text(response)}")
        return
    if data == "translate_srt":
        context.user_data.clear()
        context.user_data["mode"] = "translate_srt"
        await query.edit_message_text("🌐 ترجمة SRT إلى العربية الفصحى\n\n📄 ابعت الآن ملف SRT.")
        return
    if data == "subtitle":
        context.user_data["mode"] = "subtitle"
        await query.edit_message_text("📝 إعدادات حرق الترجمة\n\n⚙️ اختار الإعداد الذي تريد تغييره:", reply_markup=subtitle_menu())
        return
    if data == "burn_font":
        context.user_data["waiting_for_font"] = True
        await query.edit_message_text("🔤 إعداد الخط\n\n📎 ابعت الآن ملف الخط TTF أو OTF أو RAR.")
        return
    if data == "burn_size":
        keyboard = [[InlineKeyboardButton("20", callback_data="burn_size_20"), InlineKeyboardButton("24", callback_data="burn_size_24"), InlineKeyboardButton("26", callback_data="burn_size_26")],
                    [InlineKeyboardButton("28", callback_data="burn_size_28"), InlineKeyboardButton("32", callback_data="burn_size_32"), InlineKeyboardButton("36", callback_data="burn_size_36")],
                    [InlineKeyboardButton("40", callback_data="burn_size_40")], [InlineKeyboardButton("⬅️ رجوع", callback_data="subtitle")]]
        await query.edit_message_text("🔠 حجم الخط\n\nاختار حجم الخط:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("burn_size_"):
        size = data.replace("burn_size_", "", 1)
        settings = load_settings()
        settings["font_size"] = size
        save_settings(settings)
        await query.edit_message_text(f"🔠 تم حفظ حجم الخط: {size}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="subtitle")]]))
        return
    if data == "burn_color":
        keyboard = [[InlineKeyboardButton("⚪ أبيض", callback_data="burn_color_white"), InlineKeyboardButton("🟡 أصفر", callback_data="burn_color_yellow")],
                    [InlineKeyboardButton("🔵 سماوي", callback_data="burn_color_cyan"), InlineKeyboardButton("🟢 أخضر", callback_data="burn_color_green")],
                    [InlineKeyboardButton("🔴 أحمر", callback_data="burn_color_red")], [InlineKeyboardButton("⬅️ رجوع", callback_data="subtitle")]]
        await query.edit_message_text("🎨 لون الترجمة\n\nاختار لون الترجمة:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("burn_color_"):
        color = data.replace("burn_color_", "", 1)
        settings = load_settings()
        settings["font_color"] = color
        save_settings(settings)
        await query.edit_message_text(f"🎨 تم حفظ لون الترجمة: {color}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="subtitle")]]))
        return

    if data == "burn_box":
        keyboard = [[InlineKeyboardButton("⬛ تشغيل البوكس", callback_data="burn_box_on"), InlineKeyboardButton("⬜ إيقاف البوكس", callback_data="burn_box_off")], [InlineKeyboardButton("⬅️ رجوع", callback_data="subtitle")]]
        await query.edit_message_text("⬛ البوكس\n\nالبوكس يظهر خلف نص SRT فقط ويختفي مع اختفاء السطر.", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data in ("burn_box_on", "burn_box_off"):
        box = "on" if data == "burn_box_on" else "off"
        settings = load_settings()
        settings["subtitle_box"] = box
        save_settings(settings)
        await query.edit_message_text(f"⬛ البوكس: {'تشغيل' if box == 'on' else 'إيقاف'}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="subtitle")]]))
        return
    if data == "burn_outline":
        keyboard = [[InlineKeyboardButton("بدون حواف", callback_data="burn_outline_0"), InlineKeyboardButton("0.5", callback_data="burn_outline_0.5")],
                    [InlineKeyboardButton("1", callback_data="burn_outline_1"), InlineKeyboardButton("2", callback_data="burn_outline_2")], [InlineKeyboardButton("⬅️ رجوع", callback_data="subtitle")]]
        await query.edit_message_text("▫️ حواف الترجمة\n\nاختار سمك الحواف:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("burn_outline_"):
        outline = data.replace("burn_outline_", "", 1)
        settings = load_settings()
        settings["subtitle_outline"] = outline
        save_settings(settings)
        await query.edit_message_text(f"▫️ تم حفظ الحواف: {outline}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="subtitle")]]))
        return

    if data == "burn_watermark":
        keyboard = [[InlineKeyboardButton("📎 رفع/تغيير العلامة", callback_data="wm_upload")], [InlineKeyboardButton("📍 الموضع والحجم", callback_data="watermark_settings")], [InlineKeyboardButton("⬅️ رجوع", callback_data="subtitle")]]
        await query.edit_message_text("🖼️ إعدادات العلامة المائية\n\n📎 يمكنك رفع أو تغيير العلامة المائية.\n📍 ويمكنك تحديد موضعها وحجمها.", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "wm_upload":
        context.user_data["waiting_for_watermark"] = True
        await query.edit_message_text("📎 أرسل الآن ملف العلامة المائية.\n\nالمسموح:\nPNG / JPG / JPEG / WEBP / RAR\n\n⚠️ أرسل PNG كـ «ملف» للحفاظ على الشفافية.")
        return
    if data == "watermark_settings":
        keyboard = [[InlineKeyboardButton("↖️ أعلى اليسار", callback_data="wm_pos_top_left"), InlineKeyboardButton("↗️ أعلى اليمين", callback_data="wm_pos_top_right")],
                    [InlineKeyboardButton("↙️ أسفل اليسار", callback_data="wm_pos_bottom_left"), InlineKeyboardButton("↘️ أسفل اليمين", callback_data="wm_pos_bottom_right")],
                    [InlineKeyboardButton("📏 الحجم", callback_data="wm_size")],
                    [InlineKeyboardButton("🟢 تشغيل", callback_data="wm_enable"), InlineKeyboardButton("🔴 إيقاف", callback_data="wm_disable")], [InlineKeyboardButton("⬅️ رجوع", callback_data="burn_watermark")]]
        await query.edit_message_text("📍 إعدادات العلامة المائية\n\nاختر الموضع أو الحجم أو تشغيل/إيقاف العلامة.", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data in ("wm_enable", "wm_disable"):
        enabled = data == "wm_enable"
        settings = load_settings()
        settings["watermark_enabled"] = enabled
        save_settings(settings)
        await query.edit_message_text("🖼️ العلامة المائية\n\n" + ("🟢 الحالة: تشغيل" if enabled else "🔴 الحالة: إيقاف"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="watermark_settings")]]))
        return

    if data.startswith("wm_pos_"):
        position = data.replace("wm_pos_", "", 1)
        settings = load_settings()
        settings["watermark_position"] = position
        save_settings(settings)
        await query.edit_message_text("✅ تم حفظ موضع العلامة المائية.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="watermark_settings")]]))
        return
    if data == "wm_size":
        keyboard = [[InlineKeyboardButton("10%", callback_data="wm_size_10"), InlineKeyboardButton("15%", callback_data="wm_size_15")],
                    [InlineKeyboardButton("20%", callback_data="wm_size_20"), InlineKeyboardButton("25%", callback_data="wm_size_25")],
                    [InlineKeyboardButton("30%", callback_data="wm_size_30")], [InlineKeyboardButton("⬅️ رجوع", callback_data="watermark_settings")]]
        await query.edit_message_text("📏 اختر حجم العلامة المائية:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("wm_size_"):
        size = data.replace("wm_size_", "", 1)
        settings = load_settings()
        settings["watermark_size"] = size
        save_settings(settings)
        await query.edit_message_text(f"✅ تم حفظ حجم العلامة المائية: {size}%", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="watermark_settings")]]))
        return
    if data == "burn_start":
        if not context.user_data.get("video_received"):
            await query.answer("❌ الفيديو غير محفوظ في الجلسة الحالية.", show_alert=True)
            return
        if not context.user_data.get("subtitle_received"):
            await query.answer("❌ الترجمة غير محفوظة في الجلسة الحالية.", show_alert=True)
            return

        settings = load_settings()
        watermark_enabled = bool(settings.get("watermark_enabled", False))
        await query.edit_message_text("🎬 جاري تجهيز عملية حرق الترجمة...\n\n🚀 سيتم تشغيل GitHub لمعالجة الفيلم.")

        inputs = {
            "video_url": "", "subtitle_url": "", "resolution": "same", "chat_id": update.effective_chat.id,
            "telegram_message_id": context.user_data.get("video_message_id", ""),
            "telegram_message_date": context.user_data.get("video_message_date", ""),
            "subtitle_message_id": context.user_data.get("subtitle_message_id", ""),
            "subtitle_message_date": context.user_data.get("subtitle_message_date", ""),
            "subtitle_type": context.user_data.get("subtitle_type", "srt"),
            "font_message_id": settings.get("font_message_id", ""),
            "font_message_date": settings.get("font_message_date", ""),
            "font_size": settings.get("font_size", "26"),
            "font_color": settings.get("font_color", "white"),
            "subtitle_outline": settings.get("subtitle_outline", "0.5"),
            "subtitle_box": settings.get("subtitle_box", "off"),
            "watermark_message_id": settings.get("watermark_message_id", "") if watermark_enabled else "",
            "watermark_message_date": settings.get("watermark_message_date", "") if watermark_enabled else "",
            "watermark_position": settings.get("watermark_position", "top_left"),
            "watermark_size": settings.get("watermark_size", "20"),
            "watermark_enabled": str(watermark_enabled).lower(),
            "operation": "video",
        }

        response, error = dispatch_workflow(inputs)
        if error:
            await query.message.reply_text(f"❌ حدث خطأ أثناء تشغيل GitHub:\n\n{error}")
            return
        if github_success(response):
            await query.message.reply_text("✅ تم تشغيل GitHub بنجاح.\n\n🎬 جاري حرق الترجمة بالإعدادات المحفوظة.\n📤 سيصل الفيديو هنا بعد الانتهاء.")
        else:
            await query.message.reply_text(f"❌ فشل تشغيل GitHub.\n\nكود الخطأ: {response.status_code}\n{github_error_text(response)}")
        return
    if data == "speech":
        context.user_data.clear()
        context.user_data["mode"] = "speech"
        await query.edit_message_text("🎙️ ابعت الفيديو أو الملف الصوتي لتحويل الكلام إلى SRT.")
        return
    if data in ("audio", "extract", "file_link"):
        await query.edit_message_text("🔊 الميزة هتتضاف في التحديث القادم.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ القائمة الرئيسية", callback_data="main_menu")]]))
        return
    if data == "watermark":
        await query.edit_message_text("🖼️ إعداد العلامة المائية موجود داخل إعدادات حرق الترجمة.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 إعدادات حرق الترجمة", callback_data="subtitle")]]))
        return
async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    mode = context.user_data.get("mode")

    if mode == "ocr":
        if not (text.startswith("http://") or text.startswith("https://")):
            await update.message.reply_text("❌ الرابط غير صحيح. ابعت رابط الفيديو المباشر.")
            return
        await update.message.reply_text("⏳ تم استلام الرابط. جاري تشغيل OCR...")
        inputs = {"video_url": text, "subtitle_url": "", "resolution": "same", "chat_id": update.effective_chat.id, "operation": "video_ocr"}
        response, error = dispatch_workflow(inputs)
        if error:
            await update.message.reply_text(f"❌ حدث خطأ:\n\n{error}")
            return
        if github_success(response):
            await update.message.reply_text("✅ بدأ OCR. عند الانتهاء سيصل ملف SRT هنا.")
        else:
            await update.message.reply_text(f"❌ فشل تشغيل GitHub.\n\nكود الخطأ: {response.status_code}\n{github_error_text(response)}")
        return

    if mode not in ("download", "convert"):
        await update.message.reply_text("اختار وظيفة من القائمة أولًا:", reply_markup=main_menu())
        return
    if not (text.startswith("http://") or text.startswith("https://")):
        await update.message.reply_text("❌ الرابط غير صحيح. ابعت رابط الفيديو المباشر.")
        return
    context.user_data["video_url"] = text
    await update.message.reply_text("✅ تم استلام الرابط.\n\n🎬 اختار الدقة المطلوبة:", reply_markup=resolution_menu())
async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")

    if mode == "subtitle":
        context.user_data["video_message_id"] = update.message.message_id
        context.user_data["video_message_date"] = update.message.date.isoformat()
        context.user_data["video_received"] = True
        await update.message.reply_text("✅ تم استلام الفيديو.\n\n📝 الآن ابعت ملف الترجمة SRT أو ASS أو SSA.")
        return

    if mode == "speech":
        await update.message.reply_text("⏳ تم استلام الفيديو. جاري تشغيل تحويل الكلام إلى SRT...")
        inputs = {"video_url": "", "subtitle_url": "", "resolution": "same", "chat_id": update.effective_chat.id, "telegram_message_id": update.message.message_id, "telegram_message_date": update.message.date.isoformat(), "operation": "audio_srt"}
        response, error = dispatch_workflow(inputs)
        if error:
            await update.message.reply_text(f"❌ حدث خطأ:\n\n{error}")
            return
        if github_success(response):
            await update.message.reply_text("✅ بدأ تحويل الكلام إلى SRT. سيصل الملف هنا.")
        else:
            await update.message.reply_text(f"❌ فشل تشغيل GitHub.\n{github_error_text(response)}")
        return

    if mode not in ("download", "convert", "ocr"):
        await update.message.reply_text("اختار وظيفة من القائمة أولًا:", reply_markup=main_menu())
        return

    operation = "video_ocr" if mode == "ocr" else "video"
    await update.message.reply_text("⏳ تم استلام الفيديو. جاري تشغيل معالجة الفيديو...")
    inputs = {"video_url": "", "subtitle_url": "", "resolution": "same", "chat_id": update.effective_chat.id, "telegram_message_id": update.message.message_id, "telegram_message_date": update.message.date.isoformat(), "operation": operation}
    response, error = dispatch_workflow(inputs)
    if error:
        await update.message.reply_text(f"❌ حدث خطأ أثناء تشغيل GitHub:\n\n{error}")
        return
    if github_success(response):
        await update.message.reply_text("✅ بدأ معالجة الفيديو من تيليجرام. سيصل الناتج هنا.")
    else:
        await update.message.reply_text(f"❌ فشل تشغيل GitHub.\n{github_error_text(response)}")
async def receive_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")
    document = update.message.document
    if not document: return
    
    file_name = (document.file_name or "")
    lower_name = file_name.lower()
    video_extensions = (".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".ts", ".mp3", ".wav", ".m4a")

    if lower_name.endswith(video_extensions):
        context.user_data["video_message_id"] = update.message.message_id
        context.user_data["video_message_date"] = update.message.date.isoformat()
        context.user_data["video_received"] = True
        
        if mode == "subtitle":
            await update.message.reply_text("✅ تم استلام الفيديو (كمستند).\n\n📝 الآن ابعت ملف الترجمة SRT أو ASS أو SSA.")
            return
            
        chat_id = update.effective_chat.id
        message_id = update.message.message_id
        operation = "audio_srt" if mode == "speech" else ("video_ocr" if mode == "ocr" else "video")
        
        await update.message.reply_text("⏳ تم استلام ملف الفيديو. جاري إرساله إلى GitHub...")
        inputs = {"video_url": "", "subtitle_url": "", "resolution": "same", "chat_id": chat_id, "telegram_message_id": message_id, "telegram_message_date": update.message.date.isoformat(), "operation": operation}
        response, error = dispatch_workflow(inputs)
        if error:
            await update.message.reply_text(f"❌ حدث خطأ:\n\n{error}")
            return
        if github_success(response):
            await update.message.reply_text("✅ بدأ GitHub معالجة الملف. سيصل الناتج هنا عند الانتهاء.")
        else:
            await update.message.reply_text(f"❌ فشل تشغيل GitHub.\n{github_error_text(response)}")
        return

    if context.user_data.get("waiting_for_watermark"):
        if not lower_name.endswith((".png", ".jpg", ".jpeg", ".webp", ".rar")):
            await update.message.reply_text("❌ ابعت صورة بصيغة صالحة أو ملف RAR.")
            return
        settings = load_settings()
        settings["watermark_file_id"] = document.file_id
        settings["watermark_file_name"] = file_name
        settings["watermark_message_id"] = update.message.message_id
        settings["watermark_message_date"] = update.message.date.isoformat()
        settings["watermark_enabled"] = True
        save_settings(settings)
        context.user_data["waiting_for_watermark"] = False
        await update.message.reply_text(f"✅ تم حفظ العلامة المائية بنجاح.\n\n🖼️ الملف: {file_name}")
        return

    if context.user_data.get("waiting_for_font"):
        if not lower_name.endswith((".ttf", ".otf", ".rar")):
            await update.message.reply_text("❌ ابعت ملف الخط بصيغة TTF أو OTF أو RAR.")
            return
        settings = load_settings()
        settings["font_file_id"] = document.file_id
        settings["font_file_name"] = file_name
        settings["font_message_id"] = update.message.message_id
        settings["font_message_date"] = update.message.date.isoformat()
        save_settings(settings)
        context.user_data["waiting_for_font"] = False
        await update.message.reply_text(f"✅ تم حفظ ملف الخط بنجاح.\n\n🔤 الملف: {file_name}")
        return

    if mode == "subtitle":
        if not lower_name.endswith((".srt", ".ass", ".ssa")):
            await update.message.reply_text("❌ ابعت ملف ترجمة بصيغة SRT أو ASS أو SSA.")
            return
        context.user_data["subtitle_message_id"] = update.message.message_id
        context.user_data["subtitle_message_date"] = update.message.date.isoformat()
        context.user_data["subtitle_received"] = True
        context.user_data["subtitle_type"] = "ass" if lower_name.endswith(".ass") else ("ssa" if lower_name.endswith(".ssa") else "srt")
        await update.message.reply_text("✅ تم استلام ملف الترجمة.\n\n🎬 اضغط «ابدأ الحرق» من القائمة عندما تكون جاهزًا.", reply_markup=subtitle_menu())
        return

    if mode == "translate_srt":
        if not lower_name.endswith(".srt"):
            await update.message.reply_text("❌ لازم تبعت ملف بصيغة SRT.")
            return
        await update.message.reply_text("⏳ تم استلام ملف SRT. جاري إرساله للترجمة...")
        inputs = {"video_url": "", "subtitle_url": "", "resolution": "same", "chat_id": update.effective_chat.id, "srt_file_id": document.file_id, "operation": "translate_srt"}
        response, error = dispatch_workflow(inputs)
        if error:
            await update.message.reply_text(f"❌ حدث خطأ:\n\n{error}")
            return
        if github_success(response):
            await update.message.reply_text("✅ بدأت ترجمة ملف SRT. عند الانتهاء سيعود هنا.")
        else:
            await update.message.reply_text(f"❌ فشل تشغيل الترجمة.\n{github_error_text(response)}")

def main():
    if not BOT_TOKEN: return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text))
    app.add_handler(MessageHandler(filters.VIDEO, receive_video))
    app.add_handler(MessageHandler(filters.Document.ALL, receive_document))
    print("🤖 البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
