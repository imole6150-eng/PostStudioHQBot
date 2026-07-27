import json
import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from database import get_session, Connection, Post
from scheduler import schedule_post_job

CHOOSE_CONNS, GET_CONTENT, GET_MEDIA, GET_TIME = range(4)


def _keyboard(conns, selected):
    rows = []
    for c in conns:
        mark = "✅ " if c.id in selected else "▫️ "
        rows.append([InlineKeyboardButton(f"{mark}[{c.platform}] {c.name}", callback_data=f"toggle_{c.id}")])
    rows.append([InlineKeyboardButton("✅ Done", callback_data="done")])
    return InlineKeyboardMarkup(rows)


async def schedule_start(update, context):
    session = get_session()
    conns = (
        session.query(Connection)
        .filter(Connection.telegram_user_id == update.effective_user.id)
        .all()
    )
    session.close()
    if not conns:
        await update.message.reply_text("You have no connections yet. Use /connect first.")
        return ConversationHandler.END
    context.user_data["conns"] = {c.id: c for c in conns}
    context.user_data["selected"] = set()
    await update.message.reply_text(
        "Select platforms for this post, then tap Done:", reply_markup=_keyboard(conns, set())
    )
    return CHOOSE_CONNS


async def toggle_conn(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "done":
        if not context.user_data["selected"]:
            await query.answer("Select at least one platform first.", show_alert=True)
            return CHOOSE_CONNS
        await query.edit_message_text("Send the text content for your post:")
        return GET_CONTENT
    conn_id = int(query.data.split("_")[1])
    selected = context.user_data["selected"]
    if conn_id in selected:
        selected.remove(conn_id)
    else:
        selected.add(conn_id)
    conns = list(context.user_data["conns"].values())
    await query.edit_message_reply_markup(reply_markup=_keyboard(conns, selected))
    return CHOOSE_CONNS


async def content_given(update, context):
    context.user_data["content"] = update.message.text
    await update.message.reply_text("Send a photo to attach, or /skip for text-only:")
    return GET_MEDIA


async def media_given(update, context):
    photo = update.message.photo[-1]
    context.user_data["media_file_id"] = photo.file_id
    await update.message.reply_text("When should this be posted? Send in UTC as: YYYY-MM-DD HH:MM")
    return GET_TIME


async def skip_media(update, context):
    context.user_data["media_file_id"] = None
    await update.message.reply_text("When should this be posted? Send in UTC as: YYYY-MM-DD HH:MM")
    return GET_TIME


async def time_given(update, context):
    text = update.message.text.strip()
    try:
        run_date = datetime.datetime.strptime(text, "%Y-%m-%d %H:%M")
    except ValueError:
        await update.message.reply_text("Invalid format. Use: YYYY-MM-DD HH:MM (UTC)")
        return GET_TIME

    session = get_session()
    post = Post(
        telegram_user_id=update.effective_user.id,
        content=context.user_data["content"],
        media_file_id=context.user_data.get("media_file_id"),
        connection_ids=json.dumps(list(context.user_data["selected"])),
        scheduled_time=run_date,
        status="scheduled",
    )
    session.add(post)
    session.commit()
    post_id = post.id
    session.close()

    publish_func = context.application.bot_data["publish_func"]
    schedule_post_job(post_id, run_date, publish_func)

    await update.message.reply_text(f"📅 Scheduled post #{post_id} for {run_date} UTC.")
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update, context):
    context.user_data.clear()
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


def build_conversation():
    return ConversationHandler(
        entry_points=[CommandHandler("schedule", schedule_start)],
        states={
            CHOOSE_CONNS: [CallbackQueryHandler(toggle_conn)],
            GET_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, content_given)],
            GET_MEDIA: [MessageHandler(filters.PHOTO, media_given), CommandHandler("skip", skip_media)],
            GET_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_given)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
