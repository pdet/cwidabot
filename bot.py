import requests
from bottle import Bottle, response, request as bottle_request
import duckdb
from datetime import datetime, timedelta
import schedule
import time
import _thread as thread
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
import email.encoders as Encoders


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)


def announcement_time():
    while True:
        schedule.run_pending()
        time.sleep(60)  # wait one minute


class BotHandlerMixin:
    BOT_URL = None

    # Method to extract chat id from telegram request.
    def get_chat_id(self, data):
        if "message" in data:
            chat_id = data['message']['chat']['id']
            return chat_id
        if "edited_message" in data:
            chat_id = data['edited_message']['chat']['id']
            return chat_id
        return -1

    # Method to extract message id from telegram request.
    def isgroup(self, data):
        if "message" in data:
            message_text = data['message']
            if "chat" in message_text:
                chat = message_text['chat']
                if "type" in chat:
                    chat_type = chat["type"]
                    if chat_type == "group" or chat_type == "supergroup":
                        return True
        return False

    def get_message(self, data):
        if "message" in data:
            message_text = data['message']
            if "text" in message_text:
                message_text = message_text['text']
                return message_text
            return -1
        if "edited_message" in data:
            message_text = data['edited_message']['text']
            return message_text
        return -1

    # Prepared data should be json which includes at least `chat_id` and `text`
    def send_message(self, chat_id, answer):
        prepared_data = {
            "chat_id": chat_id,
            "text": answer,
        }
        message_url = self.BOT_URL + 'sendMessage'
        try:
            requests.post(message_url, json=prepared_data)
        except Exception as e:
            return e


class TelegramBot(BotHandlerMixin, Bottle):
    BOT_URL = 'https://api.telegram.org/bot'
    da_chat_id = ''
    my_name = '@bobot'
    madam_zoom_link = 'www.zoom.org'
    fatal_zoom_link = 'www.zoom.org'
    login = 'bla'
    password = 'bla'
    attendees = 'bla'
    db = duckdb.connect('presentations_cwi.db')
    duck_cursor = db.cursor()
    test = False

    def __init__(self, *args, **kwargs):
        super(TelegramBot, self).__init__()
        self.route('/', callback=self.post_handler, method="POST")
        f = open("config.txt", "r")
        self.BOT_URL += f.readline().split("\n")[0]
        self.da_chat_id = f.readline().split("\n")[0]
        self.my_name = f.readline().split("\n")[0]
        self.madam_zoom_link = f.readline().split("\n")[0]
        self.fatal_zoom_link = f.readline().split("\n")[0]
        self.login = f.readline().split("\n")[0]
        self.password = f.readline().split("\n")[0]
        self.attendees = [f.readline().split("\n")[0]]
        schedule.every().day.at("08:00").do(self.make_announcement)
        schedule.every().monday.at("11:00").do(self.request_speakers)
        thread.start_new_thread(announcement_time, ())

    def send_calendar_invite(self, eml_body, eml_subject, start):
        CRLF = "\r\n"
        organizer = "Awesome-O;CN=Awesome-O:mailto:awesome-o" + CRLF + " @cwi.nl"
        fro = "Awesome-O <holanda@cwi.nl>"
        # Hacky fix to gmt stuff
        start -= timedelta(hours=2)
        dur = timedelta(hours=1)
        ddtstart = start
        dtstamp = ddtstart.strftime("%Y%m%dT%H%M%SZ")
        dtstart = start.strftime("%Y%m%dT%H%M%SZ")
        dtend = (start + dur).strftime("%Y%m%dT%H%M%SZ")
        description = eml_subject + CRLF
        attendee = ""
        for att in self.attendees:
            attendee += "ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-    PARTICIPANT;PARTSTAT=ACCEPTED;RSVP=TRUE" + CRLF \
                        + ";CN=" + att + ";X-NUM-GUESTS=0:" + CRLF + " mailto:" + att + CRLF
        ical = "BEGIN:VCALENDAR" + CRLF + "PRODID:pyICSParser" + CRLF + "VERSION:2.0" + CRLF \
               + "CALSCALE:GREGORIAN" + CRLF
        ical += "METHOD:REQUEST" + CRLF + "BEGIN:VEVENT" + CRLF + "DTSTART:" + dtstart + CRLF + "DTEND:" + dtend \
                + CRLF + "DTSTAMP:" + dtstamp + CRLF + organizer + CRLF
        ical += "UID:FIXMEUID" + dtstamp + CRLF
        ical += attendee + "CREATED:" + dtstamp + CRLF + description + "LAST-MODIFIED:" + dtstamp + CRLF + "LOCATION:" \
            + CRLF + "SEQUENCE:0" + CRLF + "STATUS:CONFIRMED" + CRLF
        ical += "SUMMARY:" + eml_subject + CRLF + "TRANSP:OPAQUE" + CRLF + "END:VEVENT" + CRLF + "END:VCALENDAR" + CRLF

        msg = MIMEMultipart('mixed')
        msg['Reply-To'] = fro
        msg['Date'] = formatdate(localtime=False)
        msg['Subject'] = eml_subject
        msg['From'] = fro
        msg['To'] = ",".join(self.attendees)

        part_email = MIMEText(eml_body, "html")
        part_cal = MIMEText(ical, 'calendar;method=REQUEST')

        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)

        ical_atch = MIMEBase('application/ics', ' ;name="%s"' % "invite.ics")
        ical_atch.set_payload(ical)
        Encoders.encode_base64(ical_atch)
        ical_atch.add_header('Content-Disposition', 'attachment; filename="%s"' % "invite.ics")

        msg_alternative.attach(part_email)
        msg_alternative.attach(part_cal)

        mail_server = smtplib.SMTP('zwebmail.cwi.nl', 587)
        mail_server.ehlo()
        mail_server.starttls()
        mail_server.ehlo()
        mail_server.login(self.login, self.password)
        mail_server.sendmail(fro, self.attendees, msg.as_string())
        mail_server.close()

    def query_answer(self, qa_list):
        result_str = ''
        for x in qa_list:
            for y in x:
                result_str += str(y) + ' '
            result_str += '\n'
        return result_str

    def schedule_madam(self, info):
        try:
            info = info.split(' ', 1)[1]
            meeting_info = info.split(',')
            query = ''
            presentation_date = meeting_info[0][1:]
            # (date,author,title)
            if len(meeting_info) == 3:
                query = "INSERT INTO presentations (presentation_date, author, title,zoom_link, presentation_time) " \
                        "VALUES " + info[:-1] + ",'" + self.fatal_zoom_link + "'" + ",'13:00:00') "
                print(query)
            # (date,time,author,title,zoom_link)
            elif len(meeting_info) == 4:
                query = "INSERT INTO presentations (presentation_date,presentation_time, author, title,zoom_link) " \
                        "VALUES " + info[:-1] + ",'" + self.fatal_zoom_link + "') "
            # (date,time,author,title,zoom_link)
            elif len(meeting_info) == 5:
                query = "INSERT INTO presentations (presentation_date,presentation_time, author, title,zoom_link) " \
                        "VALUES " + info
            else:
                query = "INSERT INTO presentations VALUES " + info
            self.duck_cursor.execute(query)
            query = "select * from presentations where presentation_date = " + presentation_date
            print(query)
            meeting_info = self.duck_cursor.execute(query).fetchall()
            print(meeting_info)
            presentation_date = meeting_info[0][0]
            presentation_time = meeting_info[0][1]
            author_name = meeting_info[0][2]
            title = meeting_info[0][3]
            zoom_link = meeting_info[0][6]
            subject = "Madam - " + author_name + " - " + title
            body = "[Beep]<br> Dear humans, <br>  %s will present a MADAM with title: %s <br> at %s" \
                   " <br> See you there,<br><br>  PS:[boop]" % (
                       author_name, title, zoom_link)
            if not self.test:
                self.send_calendar_invite(body, subject, datetime.combine(presentation_date, presentation_time))
            return "Madam Scheduled"
        except Exception as e:
            return "Madam was not scheduled, try either: \n \\add_madam ('yyyy-mm-dd','name_author','title') \n " \
                   "\\add_madam ('yyyy-mm-dd','hh:mm:ss','name_author','title') \n \\add_madam (" \
                   "'yyyy-mm-dd','hh:mm:ss','name_author','title','zoom_link') \n\\add_madam (" \
                   "'yyyy-mm-dd','name_author','title','bio','abstract',zoom_link') \n " + str(e)

    def schedule_fatal(self, info):
        try:
            info = info.split(' ', 1)[1]
            meeting_info = info.split(',')
            query = ''
            presentation_date = meeting_info[0][1:]
            # (date,author,title)
            if len(meeting_info) == 3:
                query = "INSERT INTO presentations (presentation_date, author, title,zoom_link, presentation_time) " \
                        "VALUES " + info[:-1] + ",'" + self.fatal_zoom_link + "'" + ",'13:00:00')"
                print(query)
            # (date,time,author,title)
            elif len(meeting_info) == 4:
                query = "INSERT INTO presentations (presentation_date,presentation_time, author, title,zoom_link) " \
                        "VALUES " + info[:-1] + ",'" + self.fatal_zoom_link + "')"
            # (date,time,author,title,zoom_link)
            elif len(meeting_info) == 5:
                query = "INSERT INTO presentations (presentation_date,presentation_time, author, title,zoom_link) " \
                        "VALUES " + info
            else:
                query = "INSERT INTO presentations VALUES " + info
            self.duck_cursor.execute(query)
            query = "select * from presentations where presentation_date = " + presentation_date
            print(query)
            meeting_info = self.duck_cursor.execute(query).fetchall()
            print(meeting_info)
            presentation_date = meeting_info[0][0]
            presentation_time = meeting_info[0][1]
            author_name = meeting_info[0][2]
            title = meeting_info[0][3]
            zoom_link = meeting_info[0][6]
            subject = "Fatal - " + author_name + " - " + title
            body = "[Beep]<br> Dear humans, <br>  %s will present a FATAL with title: %s <br> at %s <br> See you " \
                   "there,<br><br>  PS:[boop]" % (
                       author_name, title, zoom_link)
            if not self.test:
                self.send_calendar_invite(body, subject, datetime.combine(presentation_date, presentation_time))
            return "Fatal Scheduled"
        except Exception as e:
            return "Fatal was not scheduled, try either: \n \\add_fatal ('yyyy-mm-dd','name_author','title') \n " \
                   "\\add_fatal ('yyyy-mm-dd','hh:mm:ss','name_author','title') \n \\add_fatal (" \
                   "'yyyy-mm-dd','hh:mm:ss','name_author','title','zoom_link') \n\\add_fatal (" \
                   "'yyyy-mm-dd','name_author','title','bio','abstract',zoom_link') \n " + str(e)

    def schedule_holiday(self, info):
        try:
            info = info.split(' ', 1)[1]
            meeting_info = info.split(',')
            query = ''
            if len(meeting_info) == 1:
                query = "INSERT INTO presentations (presentation_date) VALUES " + info
            else:
                return "Wrong number of parameters for holidays , try: \n \\add_holiday ('yyyy-mm-dd')"
            self.duck_cursor.execute(query)
            return "Holiday Scheduled"
        except Exception as e:
            return "Holiday was not scheduled, try: \n \\add_holiday ('yyyy-mm-dd') \n" + str(e)

    def schedule_scientific_meeting(self, info):
        try:
            info = info.split(' ', 1)[1]
            meeting_info = info.split(',')
            query = ''
            if len(meeting_info) == 2:
                query = "INSERT INTO presentations (presentation_date,presentation_time) VALUES " + info
            else:
                return "Wrong number of parameters for scientific meetings , try: \n \\add_scientific_meeting (" \
                       "'yyyy-mm-dd','hh:mm:ss') "
            self.duck_cursor.execute(query)
            return "Scientific Meeting Scheduled"
        except Exception as e:
            return "Scientific Meeting was not scheduled, try: \n \\add_scientific_meeting ('yyyy-mm-dd','hh:mm:ss') " \
                   "\n" + str(e)

    def make_announcement(self):
        self.duck_cursor.execute(
            "select presentation_time, author,title,zoom_link from presentations where presentation_date = \'"
            + datetime.today().strftime('%Y-%m-%d') + "\'")
        result = self.duck_cursor.fetchall()
        print(len(result))
        if len(result) != 0:
            # Check if it is a holiday (i.e., time is null)
            if not result[0][0]:
                message = "[beep] Hey Humans, enjoy the holiday! No working allowed today. [boop]"
                self.send_message(self.da_chat_id,
                                  message)
                return message
                # Check if it is a scientific meeting (i.e., presenter is null)
            elif not result[0][1]:
                message = "[beep] Hey Humans, today is scientific meeting day, enjoy the sandwiches. [boop]"
                self.send_message(self.da_chat_id, message)
                return message
            # OW its a Madam/Fatal
            if result[0][3]:
                message = "[beep] Good morning my human friends, Today we have a talk by %s at %s about %s" \
                          " Here is the zoom-link: %s be there or be square[boop]" % (
                              result[0][1], result[0][0].strftime('%H:%M'), result[0][2], result[0][3])
                self.send_message(self.da_chat_id, message)
                return message
            else:
                message = "[beep] Good morning my human friends, Today we have a talk by %s about %s at %s[boop]" % (
                    result[0][1], result[0][2], result[0][0])
                self.send_message(self.da_chat_id, message)
                return message

    def request_speakers(self):
        next_monday = next_weekday(datetime.today(), 0)
        next_friday = next_weekday(next_monday, 4)
        missing_presenter = False
        speakers = []
        query = "select count(*) from presentations where presentation_date = \'" + next_monday.strftime(
            '%Y-%m-%d') + "\'"
        self.duck_cursor.execute(query)
        message = "[beep] Hi humans, we are missing speakers for next week, based on advanced statistics I've decided " \
                  "that: \n "
        if self.duck_cursor.fetchone()[0] == 0:
            missing_presenter = True
            self.duck_cursor.execute("select name from members order by last_madam, name")
            name = self.duck_cursor.fetchone()[0]
            message += name + " should give a MADAM on " + next_monday.strftime('%d-%m-%Y') + "\n"
            self.duck_cursor.execute("update members set last_madam = '" + next_monday.strftime(
                '%Y-%m-%d') + "' where name = '" + name + "'")
            speakers.append(name)
        self.duck_cursor.execute(
            "select count(*) from presentations where presentation_date = \'" + next_friday.strftime('%Y-%m-%d') + "\'")
        if self.duck_cursor.fetchone()[0] == 0:
            missing_presenter = True
            self.duck_cursor.execute("select name from members order by last_fatal, name")
            name = self.duck_cursor.fetchone()[0]
            message += name + " should give a FATAL on " + next_friday.strftime('%d-%m-%Y') + "\n"
            self.duck_cursor.execute("update members set last_fatal = '" + next_friday.strftime(
                '%Y-%m-%d') + "' where name = '" + name + "'")
            speakers.append(name)
        message += "Talk to me and schedule yourself for your talk ASAP [boop]"
        if missing_presenter:
            self.send_message(self.da_chat_id, message)
        return speakers

    def help(self):
        return """You can issue the following commands and I'll respond!
        \\sql - I'm semi-fluent in sql, just give me a query and I'll run it
        \\add_madam - Inserts a madam
        \\add_fatal - Inserts a fatal
        \\add_holiday - Inserts a holiday
        \\add_scientific_meeting - Inserts a scientific meeting
        \\summary - I'll give you a summary of all the meetings from today onwards """

    def run_query(self, text):
        try:
            forbidden_commands = ["insert", "delete", "update", "create", "drop", "copy"]
            # Avoid sql injection
            get_first = text.split(';')[0]
            query = get_first.split(' ', 1)[1]
            if query.split(' ', 1)[0].lower() in forbidden_commands:
                return "You are not allowed to do this"
            self.duck_cursor.execute(query)
        except Exception as e:
            return str(e)
        return self.query_answer(self.duck_cursor.fetchall())

    def summary(self):
        self.duck_cursor.execute(
            "SELECT presentation_date, author FROM presentations where presentation_date >= '" + datetime.today()
            .strftime('%Y-%m-%d') + "' ORDER BY presentation_date")
        return self.query_answer(self.duck_cursor.fetchall())

    def what_to_answer(self, text):
        first_word = text.split()[0]
        if first_word == "\\sql":
            return self.run_query(text)
        if first_word == "\\help":
            return self.help()
        if first_word == "\\summary":
            return self.summary()
        if first_word == '\\add_madam':
            return self.schedule_madam(text)
        if first_word == '\\add_fatal':
            return self.schedule_fatal(text)
        if first_word == '\\add_holiday':
            return self.schedule_holiday(text)
        if first_word == '\\add_scientific_meeting':
            return self.schedule_scientific_meeting(text)
        return "[Beep] I don't understand what you said, I only understand the language of databases\n Say \\help if " \
               "you want to know what I am capable of. [Boop] "

    def post_handler(self):
        data = bottle_request.json
        print(data)
        chat_id = self.get_chat_id(data)
        if chat_id == -1:
            return response
        input_message = self.get_message(data)
        if input_message == -1:
            return response
        if self.isgroup(data):
            first_word = input_message.split()[0]
            if first_word != self.my_name:
                return response
            input_message = input_message.split(' ', 1)[1]
        answer_data = self.what_to_answer(input_message)
        for answers in answer_data.split("\n"):
            self.send_message(chat_id, answers)
        return response  # status 200 OK by default


if __name__ == '__main__':
    app = TelegramBot()
    app.run(host='localhost', port=8080)
