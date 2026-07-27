WELCOME = (
    "👋 Welcome to PostStudioHQ Bot!\n\n"
    "I schedule and auto-publish posts to Telegram channels, Discord, "
    "Twitter/X, and Facebook Pages.\n\n"
    "Commands:\n"
    "/connect — link a channel/platform\n"
    "/connections — list your linked platforms\n"
    "/schedule — schedule a new post\n"
    "/queue — view scheduled/sent posts\n"
    "/stats — quick counts by status\n"
    "/cancel <id> — cancel a scheduled post\n"
    "/now <id> — publish a scheduled post immediately\n"
)


async def start(update, context):
    await update.message.reply_text(WELCOME)


async def help_cmd(update, context):
    await update.message.reply_text(WELCOME)
