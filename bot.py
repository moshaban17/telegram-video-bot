import os
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

BOT_USERNAME = "CinmalekHardsubBot"


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
                "👁️ كلام الشاشة → SRT",
                callback_data="ocr"
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
                "🌐 ترجمة SRT",
                callback_data="translate_srt"
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def start(update, context):

    context.user_data.clear()

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
            "🔗 تحميل فيديو\n\n"
            "📹 ابعت الآن الفيديو هنا، أو ابعت رابط الفيديو المباشر."
        )


    elif query.data == "convert":

        context.user_data["mode"] = "convert"

        await query.edit_message_text(
            "🎬 تحويل دقة\n\n"
            "📹 ابعت الآن الفيديو هنا، أو ابعت رابط الفيديو المباشر."
        )


    elif query.data == "ocr":

        context.user_data["mode"] = "ocr"

        await query.edit_message_text(
            "👁️ استخراج الكلام الظاهر على الشاشة إلى SRT\n\n"
            "📹 ابعت الآن الفيديو هنا، أو ابعت رابط الفيديو المباشر.\n\n"
            "اللغات المدعومة:\n"
            "🇬🇧 English\n"
            "🇱🇰 Sinhala\n"
            "🇮🇳 Hindi\n"
            "🇮🇳 Malayalam\n"
            "🇮🇳 Telugu\n"
            "🇮🇳 Tamil\n"
            "🇧🇩 Bengali"
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

        context.user_data["mode"] = "speech"

        await query.edit_message_text(
            "🎙️ تحويل الكلام المنطوق إلى SRT\n\n"
            "📹 ابعت الآن الفيديو أو الملف الصوتي.\n\n"
            "🔇 سيتم تجاهل الصمت والموسيقى والمؤثرات الصوتية قدر الإمكان."
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


def github_dispatch(
    chat_id,
    operation,
    source_type="url",
    video_url="",
    telegram_message_id="",
    resolution="same",
    srt_file_id="",
    subtitle_url=""
):

    if not GH_TOKEN:

        raise RuntimeError(
            "GH_TOKEN غير موجود في Termux."
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
            "subtitle_url": subtitle_url,
            "resolution": resolution,
            "chat_id": str(chat_id),
            "srt_file_id": srt_file_id,
            "telegram_message_id": str(
                telegram_message_id
            ),
            "bot_username": BOT_USERNAME,
            "source_type": source_type,
            "operation": operation,
        },
    }


    response = requests.post(
        api_url,
        headers=headers,
        json=data,
        timeout=30,
    )


    return response


async def receive_text(update, context):

    text = (
        update.message.text or ""
    ).strip()

    mode = context.user_data.get("mode")


    if mode in (
        "download",
        "convert",
        "ocr",
        "speech"
    ):

        if not (
            text.startswith("http://")
            or text.startswith("https://")
        ):

            await update.message.reply_text(
                "❌ الرابط غير صحيح.\n\n"
                "ابعت رابط فيديو أو ملف صوتي مباشر يبدأ بـ http:// أو https://"
            )

            return


        chat_id = update.effective_chat.id


        if mode == "ocr":

            operation = "video_ocr"

        elif mode == "speech":

            operation = "audio_srt"

        else:

            operation = "video"


        await update.message.reply_text(
            "⏳ تم استلام الرابط.\n\n"
            "🚀 جاري تشغيل GitHub..."
        )


        try:

            response = github_dispatch(
                chat_id=chat_id,
                operation=operation,
                source_type="url",
                video_url=text,
                telegram_message_id="",
                resolution="same",
                srt_file_id="",
                subtitle_url=""
            )


            if response.status_code == 204:

                if mode == "ocr":

                    await update.message.reply_text(
                        "✅ بدأ استخراج الكلام من الشاشة.\n\n"
                        "📥 GitHub يقوم الآن بتحميل الفيديو.\n"
                        "📤 عند الانتهاء سيصل ملف SRT هنا."
                    )

                elif mode == "speech":

                    await update.message.reply_text(
                        "✅ بدأ استخراج الكلام المنطوق.\n\n"
                        "📥 GitHub يقوم الآن بتحميل الملف.\n"
                        "🎙️ يتم تجاهل الصمت والموسيقى والمؤثرات قدر الإمكان.\n"
                        "📤 عند الانتهاء سيصل ملف SRT هنا."
                    )

                else:

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
                "❌ حدث خطأ:\n\n"
                f"{str(e)}"
            )


        return


    await update.message.reply_text(
        "اختار وظيفة من القائمة أولًا:",
        reply_markup=main_menu(),
    )


async def receive_video(update, context):

    mode = context.user_data.get("mode")


    if mode not in (
        "download",
        "convert",
        "ocr",
        "speech"
    ):

        await update.message.reply_text(
            "اختار وظيفة من القائمة أولًا:",
            reply_markup=main_menu(),
        )

        return


    video = update.message.video


    if not video:

        return


    chat_id = update.effective_chat.id

    message_id = update.message.message_id


    if mode == "ocr":

        operation = "video_ocr"

    elif mode == "speech":

        operation = "audio_srt"

    else:

        operation = "video"


    if mode == "speech":

        message = (
            "⏳ تم استلام الفيديو.\n\n"
            "📥 سيتم تنزيله مباشرة على GitHub، "
            "وليس على هاتفك.\n\n"
            "🎙️ جاري استخراج الكلام المنطوق فقط..."
        )

    else:

        message = (
            "⏳ تم استلام الفيديو.\n\n"
            "📥 سيتم تنزيله مباشرة على GitHub، "
            "وليس على هاتفك.\n\n"
            "🚀 جاري تشغيل المعالجة..."
        )


    await update.message.reply_text(message)


    try:

        response = github_dispatch(
            chat_id=chat_id,
            operation=operation,
            source_type="telegram",
            video_url="",
            telegram_message_id=message_id,
            resolution="same",
            srt_file_id="",
            subtitle_url=""
        )


        if response.status_code == 204:

            if mode == "speech":

                await update.message.reply_text(
                    "✅ تم تشغيل GitHub.\n\n"
                    "📥 GitHub يقوم الآن بسحب الفيديو من تيليجرام.\n"
                    "🎙️ سيتم استخراج الكلام المنطوق فقط.\n"
                    "📤 عند الانتهاء سيصل ملف SRT هنا."
                )

            else:

                await update.message.reply_text(
                    "✅ تم تشغيل GitHub.\n\n"
                    "📥 GitHub يقوم الآن بسحب الفيديو من تيليجرام.\n"
                    "📤 بعد انتهاء المعالجة سيصل الناتج هنا."
                )

        else:

            await update.message.reply_text(
                "❌ فشل تشغيل GitHub.\n\n"
                f"كود الخطأ: {response.status_code}\n"
                f"{response.text[:500]}"
            )


    except Exception as e:

        await update.message.reply_text(
            "❌ حدث خطأ:\n\n"
            f"{str(e)}"
        )


async def receive_document(update, context):

    mode = context.user_data.get("mode")


    document = update.message.document


    if not document:

        return


    file_name = (
        document.file_name or ""
    )


    # =========================
    # SRT
    # =========================

    if mode == "translate_srt":

        if not file_name.lower().endswith(".srt"):

            await update.message.reply_text(
                "❌ لازم تبعت ملف بصيغة SRT."
            )

            return


        if not GH_TOKEN:

            await update.message.reply_text(
                "❌ GH_TOKEN غير موجود في Termux."
            )

            return


        file_id = document.file_id

        chat_id = update.effective_chat.id


        await update.message.reply_text(
            "⏳ تم استلام ملف SRT.\n\n"
            "🤖 جاري إرسال الملف للترجمة..."
        )


        try:

            response = github_dispatch(
                chat_id=chat_id,
                operation="translate_srt",
                source_type="url",
                video_url="",
                telegram_message_id="",
                resolution="same",
                srt_file_id=file_id,
                subtitle_url=""
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
                f"{str(e)}"
            )


        return


    # =========================
    # AUDIO / VIDEO FOR SPEECH
    # =========================

    if mode == "speech":

        media_extensions = (
            ".mp4",
            ".mkv",
            ".avi",
            ".mov",
            ".webm",
            ".m4v",
            ".ts",
            ".mp3",
            ".wav",
            ".m4a",
            ".aac",
            ".ogg",
            ".opus",
            ".flac",
            ".amr",
            ".wma"
        )


        if not file_name.lower().endswith(
            media_extensions
        ):

            await update.message.reply_text(
                "❌ ابعت فيديو أو ملف صوتي مدعوم."
            )

            return


        chat_id = update.effective_chat.id

        message_id = update.message.message_id


        await update.message.reply_text(
            "⏳ تم استلام الملف.\n\n"
            "📥 سيتم تنزيله مباشرة على GitHub، "
            "وليس على هاتفك.\n\n"
            "🎙️ جاري استخراج الكلام المنطوق فقط..."
        )


        try:

            response = github_dispatch(
                chat_id=chat_id,
                operation="audio_srt",
                source_type="telegram",
                video_url="",
                telegram_message_id=message_id,
                resolution="same",
                srt_file_id="",
                subtitle_url=""
            )


            if response.status_code == 204:

                await update.message.reply_text(
                    "✅ تم تشغيل GitHub.\n\n"
                    "📥 GitHub يقوم الآن بسحب الملف من تيليجرام.\n"
                    "🎙️ سيتم تجاهل الصمت والموسيقى والمؤثرات قدر الإمكان.\n"
                    "📤 عند الانتهاء سيصل ملف SRT هنا."
                )

            else:

                await update.message.reply_text(
                    "❌ فشل تشغيل GitHub.\n\n"
                    f"كود الخطأ: {response.status_code}\n"
                    f"{response.text[:500]}"
                )


        except Exception as e:

            await update.message.reply_text(
                "❌ حدث خطأ:\n\n"
                f"{str(e)}"
            )


        return


    # =========================
    # VIDEO FILE
    # =========================

    if mode in (
        "download",
        "convert",
        "ocr"
    ):

        video_extensions = (
            ".mp4",
            ".mkv",
            ".avi",
            ".mov",
            ".webm",
            ".m4v",
            ".ts"
        )


        if not file_name.lower().endswith(
            video_extensions
        ):

            await update.message.reply_text(
                "❌ الملف ليس فيديو مدعومًا."
            )

            return


        chat_id = update.effective_chat.id

        message_id = update.message.message_id


        if mode == "ocr":

            operation = "video_ocr"

        else:

            operation = "video"


        await update.message.reply_text(
            "⏳ تم استلام ملف الفيديو.\n\n"
            "📥 سيتم تنزيله مباشرة على GitHub، "
            "وليس على هاتفك.\n\n"
            "🚀 جاري تشغيل المعالجة..."
        )


        try:

            response = github_dispatch(
                chat_id=chat_id,
                operation=operation,
                source_type="telegram",
                video_url="",
                telegram_message_id=message_id,
                resolution="same",
                srt_file_id="",
                subtitle_url=""
            )


            if response.status_code == 204:

                await update.message.reply_text(
                    "✅ تم تشغيل GitHub.\n\n"
                    "📥 GitHub يقوم الآن بسحب الفيديو من تيليجرام.\n"
                    "📤 بعد انتهاء المعالجة سيصل الناتج هنا."
                )

            else:

                await update.message.reply_text(
                    "❌ فشل تشغيل GitHub.\n\n"
                    f"كود الخطأ: {response.status_code}\n"
                    f"{response.text[:500]}"
                )


        except Exception as e:

            await update.message.reply_text(
                "❌ حدث خطأ:\n\n"
                f"{str(e)}"
            )


        return


    await update.message.reply_text(
        "اختار وظيفة من القائمة أولًا:",
        reply_markup=main_menu(),
    )


def main():

    if not BOT_TOKEN:

        print(
            "❌ BOT_TOKEN غير موجود."
        )

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


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_text
        )
    )


    print(
        "🤖 البوت يعمل..."
    )


    app.run_polling()


if __name__ == "__main__":

    main()
