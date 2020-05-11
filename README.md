# Awesome-O CWI DA Bot ![Python application](https://github.com/pdet/cwidabot/workflows/Python%20application/badge.svg)
This project is a chat-bot used to schedule meetings and whatnot. Right now awesome-o is only capable of scheduling meetings and giving reminders about them. But the sky is the limit.

# Requirements
Python 3, [DuckDB](https://www.duckdb.org/) , [Bottle](https://bottlepy.org/docs/dev/) must be installed and  schedule.
If you use pip as a package manager the following command should suffice:
```bash
pip3 install duckdb bottle schedule
```

# Configuration File

<token> - Replace this line with your bot's token
<group_id> - This is the id where the bot should make the announcements
<bot_name> - @bot_name, so we can filter the messages he should reply to if he is in a group
<default_zoom_madam> - Link for default zoom madams
<default_zoom_fatal> - Link for default zoom fatal 
<sender_email> - Email used to send calendar invitations
<password> - Password for that email
<attendees> - Email(s) that should get the invitation

Obs: chmod 600 the configuration file

# Running
Be sure to first run create.py to create the current used schema.
I use [Ngrok](https://ngrok.com/) to interact with Telegram's webhook.
You just need to download it
```bash
./ngrok http <our_server_port>
(default)  ./ngrok http 8080
```
and set the webhook:
https://api.telegram.org/bot<bot_token>/setWebHook?url=https://<forward_ngrok_url.ngrok.io>/

# Contributing
I've made a list of issues that would be nice to have for this project. Right now is a one-day work kind of project, but we could use it for other tasks (e.g., scheduling Scilens usage, manage public group calendar, managing youtube/zoom/twitter channels).