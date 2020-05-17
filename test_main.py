import bot
from datetime import datetime, timedelta
import duckdb
import os

# Clean Test Database
if os.path.exists("test.db"):
    os.remove("test.db")

# Bot Settings
app = bot.TelegramBot()
app.BOT_URL = 'bot_url/'
app.da_chat_id = '1010'
app.my_name = '@bot'
app.madam_zoom_link = 'www.madam.zoom'
app.fatal_zoom_link = 'www.fatal.zoom'
app.db = duckdb.connect('test.db')
app.test = True
app.duck_cursor = app.db.cursor()
app.duck_cursor.execute("CREATE TABLE IF NOT EXISTS presentations(presentation_date Date NOT NULL UNIQUE, "
                        "presentation_time TIME, author String, title String , bio String, "
                        "abstract string, zoom_link String);")

app.duck_cursor.execute("CREATE TABLE IF NOT EXISTS members(name String NOT NULL UNIQUE, last_madam DATE NOT NULL, "
                        "last_fatal Date NOT NULL);")
app.duck_cursor.execute("insert into members values ('Hannes Mühleisen', '2020-01-20' ,'2019-01-01');")
app.duck_cursor.execute("insert into members values ('Tim Gubner', '2020-01-27' ,'2020-03-09');")
app.duck_cursor.execute("insert into members values ('Nantia Makrynioti', '2020-05-11', '2020-03-27');")
app.duck_cursor.execute("insert into members values ('Peter Boncz', '2020-03-20', '2020-04-10');")
app.duck_cursor.execute("insert into members values ('Long Tran', '2019-01-01','2019-01-01');")

def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)

# Test bully
def test_bullying():
    next_monday = next_weekday(datetime.today(), 0)
    next_friday = next_weekday(next_monday, 4)
    result = app.request_speakers()
    assert len(result) == 2
    assert result[0] == "Long Tran"
    assert result[1] == "Hannes Mühleisen"
    app.what_to_answer("\\add_fatal ('" + next_friday.strftime('%Y-%m-%d') + "','Pedro','Cracking rehash')")
    result = app.request_speakers()
    assert len(result) == 1
    assert result[0] == "Hannes Mühleisen"
    result = app.request_speakers()
    assert len(result) == 1
    assert result[0] == "Tim Gubner"
    app.what_to_answer("\\add_madam ('" + next_monday.strftime('%Y-%m-%d') + "','Pedro','Cracking rehash')")
    result = app.request_speakers()
    assert len(result) == 0
    
def test_announcements():
    current_day = datetime.today()
    app.what_to_answer("\\add_fatal ('" + current_day.strftime('%Y-%m-%d') + "','Pedro','Cracking rehash')")
    assert app.make_announcement() == "[beep] Good morning my human friends, Today we have a talk by Pedro at " \
                                      "13:00 about Cracking rehash Here is the zoom-link: www.fatal.zoom " \
                                      "be there or be square[boop]"
    app.duck_cursor.execute("delete from presentations;")

    app.what_to_answer("\\add_holiday ('" + current_day.strftime('%Y-%m-%d') + "')")
    assert app.make_announcement() == "[beep] Hey Humans, enjoy the holiday! No working allowed today. [boop]"
    app.duck_cursor.execute("delete from presentations;")

    app.what_to_answer("\\add_scientific_meeting ('" + current_day.strftime('%Y-%m-%d') + "', '13:00:00')")
    assert app.make_announcement() == "[beep] Hey Humans, today is scientific meeting day, enjoy the sandwiches. [boop]"
    app.duck_cursor.execute("delete from presentations;")


# TODO: Check each insert, should be nicer with new RAPI
def test_insert():
    current_day = datetime.today()
    plus_one_day = timedelta(days=1)
    # Insert Fatal Wrong
    result = app.what_to_answer("\\add_fatal")
    assert result.startswith("Fatal was not scheduled, try either:")
    result = app.what_to_answer("\\add_fatal hau")
    assert result.startswith("Fatal was not scheduled, try either:")

    # Insert Fatal (date,author,title)
    result = app.what_to_answer("\\add_fatal ('" + current_day.strftime('%Y-%m-%d') + "','Pedro','Cracking rehash')")
    assert result == "Fatal Scheduled"
    # Insert Fatal (date,time,author,title)
    current_day += plus_one_day
    result = app.what_to_answer(
        "\\add_fatal ('" + current_day.strftime('%Y-%m-%d') + "','14:00:00','Diego','Bloom Layers of Obstruction')")
    assert result == "Fatal Scheduled"
    # Insert Fatal (date,time,author,title,zoom_link)
    current_day += plus_one_day
    result = app.what_to_answer("\\add_fatal ('" + current_day.strftime(
        '%Y-%m-%d') + "','14:00:00','MVR','Reinventing The Wheel: A bful wheel','duckduckgo')")
    assert result == "Fatal Scheduled"
    # Insert Madam Wrong
    result = app.what_to_answer("\\add_madam")
    result.startswith("Madam was not scheduled, try either:")
    result = app.what_to_answer("\\add_madam hau")
    assert result.startswith("Madam was not scheduled, try either:")

    # Insert Madam (date,author,title)
    current_day += plus_one_day
    result = app.what_to_answer("\\add_madam ('" + current_day.strftime('%Y-%m-%d') + "','TK','Microscopic HT')")
    assert result == "Madam Scheduled"
    # Insert Madam (date,time,author,title)
    # Insert Fatal (date,time,author,title)
    current_day += plus_one_day
    result = app.what_to_answer(
        "\\add_madam ('" + current_day.strftime('%Y-%m-%d') + "','14:00:00','Morpheu','Old New Hardware')")
    assert result == "Madam Scheduled"
    # Insert Madam (date,time,author,title,zoom_link)
    current_day += plus_one_day
    result = app.what_to_answer("\\add_madam ('" + current_day.strftime(
        '%Y-%m-%d') + "','14:00:00','Rick','Universe in a nutshell','rickityrick.com')")
    assert result == "Madam Scheduled"

    # Insert Holiday Wrong
    result = app.what_to_answer("\\add_holiday")
    assert result.startswith("Holiday was not scheduled,")
    result = app.what_to_answer("\\add_holiday hau")
    assert result.startswith("Holiday was not scheduled,")
    result = app.what_to_answer("\\add_holiday (a,b)")
    assert result.startswith("Wrong number of parameters for holidays")

    # Insert Holiday Right
    current_day += plus_one_day
    result = app.what_to_answer("\\add_holiday ('" + current_day.strftime('%Y-%m-%d') + "')")
    assert result == "Holiday Scheduled"

    # Insert Scientific Meeting Wrong
    result = app.what_to_answer("\\add_scientific_meeting")
    assert result.startswith("Scientific Meeting was not scheduled")
    result = app.what_to_answer("\\add_scientific_meeting hau")
    assert result.startswith("Wrong number of parameters for")
    result = app.what_to_answer("\\add_scientific_meeting (a)")
    assert result.startswith("Wrong number of parameters for")
    # Insert Scientific Meeting Right
    current_day += plus_one_day
    result = app.what_to_answer("\\add_scientific_meeting ('" + current_day.strftime('%Y-%m-%d') + "', '13:00:00')")
    assert result == "Scientific Meeting Scheduled"

    # Check if we have the correct number of entries in the db
    result = app.duck_cursor.execute("select count(*) from presentations").fetchall()
    assert result[0][0] == 8


# Test \sql
def test_sql():
    assert app.what_to_answer("\\sql").startswith("list index out of range")
    assert app.what_to_answer("\\sql bla").startswith("Parser: syntax error")
    assert app.what_to_answer("\\sql select count(*) from presentations")[0] == '8'
    assert app.what_to_answer("\\sql select count(*) from presentations; select * from presentations")[0] == '8'
    assert app.what_to_answer("\\sql CREATE TABLE abc (a integer)") == "You are not allowed to do this"
    assert app.what_to_answer(
        "\\sql insert into presentations (presentation_date) values ('2020-01-01')") == "You are not allowed to do this"
    assert app.what_to_answer("\\sql delete from presentations") == "You are not allowed to do this"
    assert app.what_to_answer("\\sql drop table presentations") == "You are not allowed to do this"
    assert app.what_to_answer("\\sql update presentations set author = 'santa'") == "You are not allowed to do this"


# Test Summary
# TODO: Should check whole summary, will be easier with new RAPI
def test_summary():
    result = app.what_to_answer('\\summary')
    assert len(result) == 138


# Test Config File
def test_config():
    f = open("config.txt", "r")
    assert f.readline().split("\n")[0] == "$token"
    assert f.readline().split("\n")[0] == "$group_id"
    assert f.readline().split("\n")[0] == "$bot_name"
    assert f.readline().split("\n")[0] == "$default_zoom_madam"
    assert f.readline().split("\n")[0] == "$default_zoom_fatal"
    assert f.readline().split("\n")[0] == "$sender_email"
    assert f.readline().split("\n")[0] == "$password"
    assert f.readline().split("\n")[0] == "$attendees"

# Test Deletes

# Test requests (user, group, supergroup)

# Test calendar invite