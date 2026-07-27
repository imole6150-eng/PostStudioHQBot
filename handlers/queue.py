from database import get_session, Post
from scheduler import cancel_post_job


async def list_queue(update, context):
    session = get_session()
    posts = (
        session.query(Post)
        .filter(Post.telegram_user_id == update.effective_user.id)
        .order_by(Post.scheduled_time)
        .all()
    )
    session.close()
    if not posts:
        await update.message.reply_text("No posts in queue. Use /schedule to add one.")
        return
    lines = []
    for p in posts:
        snippet = (p.content[:30] + "...") if len(p.content) > 30 else p.content
        lines.append(f"#{p.id} [{p.status}] {p.scheduled_time} UTC — {snippet}")
    await update.message.reply_text("\n".join(lines))


async def stats(update, context):
    session = get_session()
    posts = (
        session.query(Post)
        .filter(Post.telegram_user_id == update.effective_user.id)
        .all()
    )
    session.close()
    counts = {}
    for p in posts:
        counts[p.status] = counts.get(p.status, 0) + 1
    if not counts:
        await update.message.reply_text("No posts yet.")
        return
    lines = [f"{status}: {count}" for status, count in counts.items()]
    await update.message.reply_text("📊 Post stats:\n" + "\n".join(lines))


async def cancel_post(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /cancel <post_id>")
        return
    post_id = int(context.args[0])
    session = get_session()
    post = session.query(Post).get(post_id)
    if not post or post.telegram_user_id != update.effective_user.id:
        session.close()
        await update.message.reply_text("Post not found.")
        return
    post.status = "cancelled"
    session.commit()
    session.close()
    cancel_post_job(post_id)
    await update.message.reply_text(f"Cancelled post #{post_id}.")


async def publish_now(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /now <post_id>")
        return
    post_id = int(context.args[0])
    session = get_session()
    post = session.query(Post).get(post_id)
    session.close()
    if not post or post.telegram_user_id != update.effective_user.id:
        await update.message.reply_text("Post not found.")
        return
    publish_func = context.application.bot_data["publish_func"]
    await publish_func(post_id)
    await update.message.reply_text(f"Published post #{post_id} — check /queue for the result.")
