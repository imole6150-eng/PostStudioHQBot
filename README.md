# PostStudioHQ Bot

A Telegram bot that schedules posts and auto-publishes them to **Telegram
channels, Discord, Twitter/X, and Facebook Pages** — built entirely on free
APIs, deployable on Railway straight from this GitHub repo.

## What it does

- `/connect` — link a destination (Telegram channel, Discord webhook,
  Twitter/X account, or Facebook Page)
- `/connections` — list what you've linked
- `/schedule` — pick platforms, write content, optionally attach a photo,
  set a UTC date/time — the bot posts it automatically when the time comes
- `/queue` — see all scheduled/sent/failed posts
- `/stats` — counts by status
- `/cancel <id>` — cancel a scheduled post
- `/now <id>` — publish immediately instead of waiting

Scheduled jobs are stored in the database (not just in memory), so a
Railway redeploy or restart won't lose your queue.

## Honest scope note

This covers the core of what most people actually use ContentStudio for:
one place to queue content across platforms and have it go out on
schedule. It does **not** include things that genuinely require paid
tooling or platform app-review approval to do at scale — a social inbox,
AI copywriting, deep analytics dashboards, or publishing to *other
people's* Facebook/Instagram/LinkedIn accounts. Posting to your **own**
Page/channel/account works fine on free tiers.

## 1. Create your Telegram bot

1. Message **@BotFather** on Telegram → `/newbot` → follow the prompts.
2. Copy the token it gives you (looks like `123456:ABC-DEF...`).

## 2. Push this code to GitHub

```bash
cd poststudio-bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/poststudio-bot.git
git push -u origin main
```

(Create the empty repo on GitHub first, named e.g. `poststudio-bot`,
**without** a README so it doesn't conflict.)

## 3. Deploy on Railway

1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy
   from GitHub repo** → pick `poststudio-bot`.
2. Railway auto-detects Python via `railway.json` / Nixpacks and will run
   `python main.py` on deploy (already configured).
3. Open the service → **Variables** tab → add:
   - `TELEGRAM_BOT_TOKEN` = the token from BotFather
   - `OWNER_TELEGRAM_ID` = your Telegram numeric ID (optional, recommended
     — get it from **@userinfobot**)
4. (Recommended) Add a **Postgres** plugin from Railway's "+ New" menu in
   the same project. It automatically injects `DATABASE_URL`, which this
   bot already reads — otherwise it falls back to a local SQLite file,
   which can be wiped on redeploy.
5. Deploy. Check the **Logs** tab for `PostStudioHQ bot starting...`.

This bot uses long-polling (no incoming webhook, no port to expose), so
you don't need to generate a public domain for it in Railway.

## 4. Connect your platforms

Run `/connect` in Telegram and follow the prompts. What each platform needs:

**Telegram channel** — add this bot as an **admin** of your channel/group,
then send its numeric chat ID (get it via **@RawDataBot** after forwarding
a message from the channel, or **@userinfobot** for groups).

**Discord** — in your server: Channel Settings → Integrations → Webhooks
→ New Webhook → copy URL. No account login needed, fully free.

**Twitter/X** — create a project at
[developer.twitter.com](https://developer.twitter.com) (free tier), create
an app, generate **Consumer Key/Secret** and **Access Token/Secret** with
**Read and Write** permission. Free tier has a monthly post cap — check
your developer portal for the current number.

**Facebook Page** — create an app at
[developers.facebook.com](https://developers.facebook.com), use the
**Graph API Explorer** to generate a Page Access Token for a Page you
admin, with `pages_manage_posts` and `pages_read_engagement` permissions.
Posting to your own Page works in Development Mode without App Review.

## 5. Schedule your first post

Run `/schedule`, tick the platform(s), send your text, attach a photo or
`/skip`, then send a time like `2026-08-01 14:30` (UTC). Check `/queue`
to confirm it's there.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # then fill in TELEGRAM_BOT_TOKEN
python main.py
```

## Project structure

```
poststudio-bot/
├── main.py                  # entry point, wires everything together
├── config.py                # env var loading
├── database.py               # SQLAlchemy models (Connection, Post)
├── scheduler.py              # persistent APScheduler wrapper
├── handlers/
│   ├── start.py              # /start, /help
│   ├── connect.py            # /connect, /connections
│   ├── schedule.py           # /schedule
│   └── queue.py              # /queue, /stats, /cancel, /now
├── publishers/
│   ├── telegram_publisher.py
│   ├── discord_publisher.py
│   ├── twitter_publisher.py
│   └── facebook_publisher.py
├── requirements.txt
├── railway.json
├── Procfile
├── .env.example
└── .gitignore
```

## Extending it

Adding a new destination type is just:
1. Add its required credential fields to `PLATFORM_FIELDS` /
   `FIELD_PROMPTS` in `handlers/connect.py`.
2. Add a `publishers/<name>_publisher.py` with an async `publish(bot,
   connection, post)` function returning `(ok: bool, message: str)`.
3. Register it in the `PUBLISHERS` dict in `main.py`.
