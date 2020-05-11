import bot
from datetime import datetime, timedelta
import duckdb
import os

# Clean Test Database
if os.path.exists("test.db"):
  os.remove("test.db")

#Bot Settings
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
    result = app.what_to_answer("\\add_fatal ('" + current_day.strftime('%Y-%m-%d') + "','14:00:00','Diego','Bloom Layers of Obstruction')")
    assert result == "Fatal Scheduled"
    # Insert Fatal (date,time,author,title,zoom_link)
    current_day += plus_one_day
    result = app.what_to_answer("\\add_fatal ('" + current_day.strftime('%Y-%m-%d') + "','14:00:00','MVR','Reinventing The Wheel: A bful wheel','duckduckgo')")
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
    result = app.what_to_answer("\\add_madam ('" + current_day.strftime('%Y-%m-%d') + "','14:00:00','Morpheu','Old New Hardware')")
    assert result == "Madam Scheduled"
    # Insert Madam (date,time,author,title,zoom_link)
    current_day += plus_one_day
    result = app.what_to_answer("\\add_madam ('" + current_day.strftime('%Y-%m-%d') + "','14:00:00','Rick','Universe in a nutshell','rickityrick.com')")
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

    #Check if we have the correct number of entries in the db
    result = app.duck_cursor.execute("select count(*) from presentations").fetchall()
    assert result[0][0] == 8

# Test requests (user, group supergroup)

# Test \sql

# Test Summary

# Test calendar invite

# Test announcements