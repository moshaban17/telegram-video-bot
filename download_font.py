import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession


async def main():
    client = TelegramClient(
        StringSession(os.environ["TG_SESSION"]),
        int(os.environ["API_ID"]),
        os.environ["API_HASH"]
    )

    await client.start()

    message = await client.get_messages(
        os.environ["BOT_USERNAME"],
        ids=int(os.environ["FONT_MESSAGE_ID"])
    )

    if not message or not message.media:
        raise RuntimeError("لم يتم العثور على ملف الخط.")

    await client.download_media(
        message,
        file="font_source"
    )

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
