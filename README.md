# Awesome-O CWI DA Bot
This project is a chat-bot used to schedule meetings and whatnot.

# Requirements
Python 2, [DuckDB](https://www.duckdb.org/) , [Bottle](https://bottlepy.org/docs/dev/) must be installed and  schedule.
If you use pip as a package manager the following command should suffice:
```bash
pip install duckdb bottle schedule
```

# Configuration file
<token> - Replace this line with your bot's token
<group_id> - This is the id where the bot should make the announcements
<bot_name> - @bot_name, so we can filter the messages he should reply to if he is in a group

# Running
Be sure to first run create.py to create the current used schema.
I use [Ngrok](https://ngrok.com/) to interact with Telegram's webhook.
You just need to download it
```bash
./ngrok http <our_server_port>
(e.g.,)  ./ngrok http <our_server_port>
```
and set the webhook:
https://api.telegram.org/bot<bot_token>/setWebHook?url=https://<forward_ngrok_url.ngrok.io>/

# Contributing
I've made a list of issues that would be nice to have for this project. Right now is a one-day work kind of project, but we could use it for other tasks (e.g., scheduling Scilens usage, manage public group calendar, managing youtube/zoom/twitter channels).