import httpx


async def publish(bot, connection, post):
    """Post via a Discord webhook URL (free, no app review needed)."""
    creds = connection.creds()
    webhook_url = creds["webhook_url"]
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if post.media_file_id:
                tg_file = await bot.get_file(post.media_file_id)
                file_bytes = await tg_file.download_as_bytearray()
                files = {"file": ("image.jpg", bytes(file_bytes))}
                data = {"content": post.content}
                r = await client.post(webhook_url, data=data, files=files)
            else:
                r = await client.post(webhook_url, json={"content": post.content})
        if r.status_code in (200, 204):
            return True, "sent"
        return False, f"HTTP {r.status_code}: {r.text}"
    except Exception as e:
        return False, str(e)
