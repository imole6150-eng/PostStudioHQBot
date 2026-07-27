from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from config import DATABASE_URL

# Jobs are persisted in the same database as everything else, so scheduled
# posts survive a bot restart / redeploy on Railway.
scheduler = AsyncIOScheduler(jobstores={"default": SQLAlchemyJobStore(url=DATABASE_URL)})


def start_scheduler():
    if not scheduler.running:
        scheduler.start()


def schedule_post_job(post_id, run_date, publish_func):
    job_id = f"post_{post_id}"
    scheduler.add_job(
        publish_func,
        "date",
        run_date=run_date,
        args=[post_id],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=3600,
    )


def cancel_post_job(post_id):
    job_id = f"post_{post_id}"
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass
