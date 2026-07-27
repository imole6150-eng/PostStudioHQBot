import json
import datetime
import logging

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CommandHandler,
    TypeHandler,
)

from config import TELEGRAM_BOT_TOKEN, OWNER_TELEGRAM_ID
from database import init_db, get_session, Post, Connection
from scheduler import scheduler, start_scheduler, schedule_post_job
from publishers import telegram_publisher, discord_publisher, twitter_publisher, facebook_publisher
from handlers import start as start_handlers
from handlers import connect as connect_handlers
from handlers import schedule as schedule_handlers
from handlers import queue as queue_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("poststudio")

PUBLISHERS = {
    "telegram": telegram_publisher,
    "discord": discord_publisher,
    "twitter": twitter_publisher,
    "facebook": facebook_publisher,
}


async def publish_post(post_id, bot):
    """Runs at scheduled time (or on /now): publishes one post to all of
    its linked connections and records the result."""
    session = get_session()
    post = session.query(Post).get(post_id)
    if not post or post.status not in ("scheduled",):
        session.close()
        return

    conn_ids = json.loads(post.connection_ids)
    logs = []
    all_ok = True
    for cid in conn_ids:
        conn = session.query(Connection).get(cid)
        if not conn:
            logs.append(f"connection #{cid}: missing")
            all_ok = False
            continue
        publisher = PUBLISHERS.get(conn.platform)
        if not publisher:
            logs.append(f"{conn.platform}: no publisher registered")
            all_ok = False
            continue
        ok, msg = await publisher.publish(bot, conn, post)
        logs.append(f"{conn.platform} ({conn.name}): {'OK' if ok else 'FAIL - ' + msg}")
        if not ok:
            all_ok = False

    post.status = "sent" if all_ok else "failed"
    post.result_log = "\n".join(logs)
    session.commit()
    session.close()
    log.info("Post #%s finished: %s", post_id, post.status)


async def guard(update, context):
    """If OWNER_TELEGRAM_ID is set, silently blocks everyone else."""
    if not OWNER_TELEGRAM_ID:
        return
    user = update.effective_user
    if user and str(user.id) != str(OWNER_TELEGRAM_ID):
        if update.message:
            await update.message.reply_text("This bot is private.")
        raise ApplicationHandlerStop


def build_app():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    async def _publish_wrapper(post_id):
        await publish_post(post_id, application.bot)

    application.bot_data["publish_func"] = _publish_wrapper

    application.add_handler(TypeHandler(Update, guard), group=-1)

    application.add_handler(CommandHandler("start", start_handlers.start))
    application.add_handler(CommandHandler("help", start_handlers.help_cmd))
    application.add_handler(connect_handlers.build_conversation())
    application.add_handler(schedule_handlers.build_conversation())
    application.add_handler(CommandHandler("connections", connect_handlers.list_connections))
    application.add_handler(CommandHandler("queue", queue_handlers.list_queue))
    application.add_handler(CommandHandler("stats", queue_handlers.stats))
    application.add_handler(CommandHandler("cancel", queue_handlers.cancel_post))
    application.add_handler(CommandHandler("now", queue_handlers.publish_now))

    return application


async def _reschedule_pending(application):
    """On startup, re-arms scheduler jobs for any post that's still
    'scheduled' — needed because a redeploy restarts the process."""
    session = get_session()
    pending = session.query(Post).filter(Post.status == "scheduled").all()
    now = datetime.datetime.utcnow()
    for post in pending:
        run_date = post.scheduled_time if post.scheduled_time > now else now + datetime.timedelta(seconds=10)
        schedule_post_job(post.id, run_date, application.bot_data["publish_func"])
    session.close()
    log.info("Re-armed %d pending post(s).", len(pending))


def main():
    init_db()
    application = build_app()
    start_scheduler()

    async def _post_init(app):
        await _reschedule_pending(app)

    application.post_init = _post_init

    log.info("PostStudioHQ bot starting (polling mode)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
