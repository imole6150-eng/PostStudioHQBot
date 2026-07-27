import tweepy


async def publish(bot, connection, post):
    """Post a tweet using the free tier of the X (Twitter) API.

    Note: X's free API tier has a monthly write cap (check your developer
    portal for the current limit) and no read access. Posting-only usage
    like this fits within the free tier.
    """
    creds = connection.creds()
    try:
        client = tweepy.Client(
            consumer_key=creds["consumer_key"],
            consumer_secret=creds["consumer_secret"],
            access_token=creds["access_token"],
            access_token_secret=creds["access_token_secret"],
        )

        media_ids = None
        if post.media_file_id:
            auth = tweepy.OAuth1UserHandler(
                creds["consumer_key"],
                creds["consumer_secret"],
                creds["access_token"],
                creds["access_token_secret"],
            )
            api_v1 = tweepy.API(auth)
            tg_file = await bot.get_file(post.media_file_id)
            file_bytes = await tg_file.download_as_bytearray()
            tmp_path = f"/tmp/tw_media_{post.id}.jpg"
            with open(tmp_path, "wb") as f:
                f.write(bytes(file_bytes))
            media = api_v1.media_upload(tmp_path)
            media_ids = [media.media_id]

        client.create_tweet(text=post.content, media_ids=media_ids)
        return True, "sent"
    except Exception as e:
        return False, str(e)
