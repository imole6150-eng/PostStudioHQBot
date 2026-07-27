import json

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from database import get_session, Connection

CHOOSE_PLATFORM, ASK_NAME, ASK_FIELD = range(3)

PLATFORM_FIELDS = {
    "telegram": ["chat_id"],
    "discord": ["webhook_url"],
    "twitter": ["consumer_key", "consumer_secret", "access_token", "access_token_secret"],
    "facebook": ["page_id", "page_access_token"],
}

FIELD_PROMPTS = {
    "chat_id": (
        "Send the Telegram channel/chat ID (e.g. -1001234567890).\n"
        "Add this bot as an admin of that channel first, then use a tool "
        "like @userinfobot or @RawDataBot to find the channel's ID."
    ),
    "webhook_url": "Send the Discord channel Webhook URL (Channel Settings → Integrations → Webhooks → New Webhook).",
    "consumer_key": "Send your Twitter/X API Consumer Key (developer.twitter.com, free tier).",
    "consumer_secret": "Send your Twitter/X API Consumer Secret.",
    "access_token": "Send your Twitter/X Access Token (Read + Write permissions).",
    "access_token_secret": "Send your Twitter/X Access Token Secret.",
    "page_id": "Send your Facebook Page ID.",
    "page_access_token": "Send your Facebook Page Access Token (Graph API Explorer, page-scoped, long-lived if possible).",
}


async def connect_start(update, context):
    keyboard = [
        [InlineKeyboardButton("Telegram Channel", callback_data="telegram")],
        [InlineKeyboardButton("Discord", callback_data="discord")],
        [InlineKeyboardButton("Twitter / X", callback_data="twitter")],
        [InlineKeyboardButton("Facebook Page", callback_data="facebook")],
    ]
    await update.message.reply_text(
        "Which platform do you want to connect?", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSE_PLATFORM


async def platform_chosen(update, context):
    query = update.callback_query
    await query.answer()
    platform = query.data
    context.user_data["new_conn"] = {"platform": platform, "fields": {}}
    context.user_data["remaining_fields"] = list(PLATFORM_FIELDS[platform])
    await query.edit_message_text(
        f"Connecting {platform}.\nGive this connection a nickname (e.g. 'Main Channel'):"
    )
    return ASK_NAME


async def name_given(update, context):
    context.user_data["new_conn"]["name"] = update.message.text.strip()
    return await ask_next_field(update, context)


async def ask_next_field(update, context):
    remaining = context.user_data["remaining_fields"]
    if not remaining:
        return await save_connection(update, context)
    field = remaining[0]
    await update.message.reply_text(FIELD_PROMPTS[field])
    return ASK_FIELD


async def field_given(update, context):
    remaining = context.user_data["remaining_fields"]
    field = remaining.pop(0)
    context.user_data["new_conn"]["fields"][field] = update.message.text.strip()
    return await ask_next_field(update, context)


async def save_connection(update, context):
    data = context.user_data["new_conn"]
    session = get_session()
    conn = Connection(
        telegram_user_id=update.effective_user.id,
        platform=data["platform"],
        name=data["name"],
        credentials=json.dumps(data["fields"]),
    )
    session.add(conn)
    session.commit()
    conn_id = conn.id
    session.close()
    await update.message.reply_text(
        f"✅ Connected #{conn_id} '{data['name']}' ({data['platform']}). Use /connections to view all."
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update, context):
    context.user_data.clear()
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


async def list_connections(update, context):
    session = get_session()
    conns = (
        session.query(Connection)
        .filter(Connection.telegram_user_id == update.effective_user.id)
        .all()
    )
    session.close()
    if not conns:
        await update.message.reply_text("No connections yet. Use /connect to add one.")
        return
    lines = [f"#{c.id} [{c.platform}] {c.name}" for c in conns]
    await update.message.reply_text("Your connections:\n" + "\n".join(lines))


def build_conversation():
    return ConversationHandler(
        entry_points=[CommandHandler("connect", connect_start)],
        states={
            CHOOSE_PLATFORM: [CallbackQueryHandler(platform_chosen)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_given)],
            ASK_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, field_given)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
