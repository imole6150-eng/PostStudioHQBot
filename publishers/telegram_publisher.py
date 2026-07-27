async def publish(bot, connection, post):
    """Post to a Telegram channel/group the bot has been added to as admin."""
    creds = connection.creds()
    chat_id = creds["chat_id"]
    try:
        if post.media_file_id:
            await bot.send_photo(chat_id=chat_id, photo=post.media_file_id, caption=post.content)
        else:
            await bot.send_message(chat_id=chat_id, text=post.content)
        return True, "sent"
    except Exception as e:
        return False, str(e)
