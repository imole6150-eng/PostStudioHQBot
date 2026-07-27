import httpx


async def publish(bot, connection, post):
    """Post to a Facebook Page using the free Graph API.

    Note: posting to your OWN page as an admin works fine in an app that is
    still in Development Mode (no App Review needed). App Review is only
    required once you want other people's pages to use this.
    """
    creds = connection.creds()
    page_id = creds["page_id"]
    token = creds["page_access_token"]
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if post.media_file_id:
                tg_file = await bot.get_file(post.media_file_id)
                file_bytes = await tg_file.download_as_bytearray()
                files = {"source": ("image.jpg", bytes(file_bytes))}
                data = {"caption": post.content, "access_token": token}
                r = await client.post(
                    f"https://graph.facebook.com/{page_id}/photos", data=data, files=files
                )
            else:
                data = {"message": post.content, "access_token": token}
                r = await client.post(f"https://graph.facebook.com/{page_id}/feed", data=data)
        if r.status_code == 200:
            return True, "sent"
        return False, f"HTTP {r.status_code}: {r.text}"
    except Exception as e:
        return False, str(e)
