import os
from datetime import datetime, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession


async def main():
    client = TelegramClient(
        StringSession(os.environ["TG_SESSION"]),
        int(os.environ["API_ID"]),
        os.environ["API_HASH"]
    )

    await client.start()
    bot = await client.get_entity(os.environ["BOT_USERNAME"])

    target_date = os.environ.get("WATERMARK_MESSAGE_DATE", "").strip()
    target_id = os.environ.get("WATERMARK_MESSAGE_ID", "").strip()

    message = None

    if target_date:
        target_dt = datetime.fromisoformat(target_date)

        if target_dt.tzinfo is None:
            target_dt = target_dt.replace(tzinfo=timezone.utc)

        messages = await client.get_messages(bot, limit=100)

        candidates = [
            m for m in messages
            if m.media and m.date
        ]

        if candidates:
            message = min(
                candidates,
                key=lambda m: abs((m.date - target_dt).total_seconds())
            )

            diff = abs(
                (message.date - target_dt).total_seconds()
            )

            if diff > 120:
                message = None
            else:
                print("Selected watermark message:", message.id)
                print("Message date:", message.date.isoformat())
                print("Difference:", diff, "seconds")

    if message is None and target_id:
        message = await client.get_messages(
            bot,
            ids=int(target_id)
        )

    if not message or not message.media:
        raise RuntimeError("Watermark message not found")

    await client.download_media(
        message,
        file="watermark_source"
    )

    await client.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
