import requests  
from bottle import Bottle, response, request as bottle_request
import duckdb
from datetime import datetime,timedelta
import schedule
import time
import _thread as thread
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import email.encoders as Encoders
import os
import socket
import ssl

db = duckdb.connect('presentations_cwi.db')
duck_cursor = db.cursor()
zoom_file = open("config_zoom.txt", "r")
zoom_madam = zoom_file.readline().split("\n")[0]
zoom_fatal = zoom_file.readline().split("\n")[0]
def send_calendar_invite(eml_body,eml_subject, start, end):
    f = open("config_email.txt", "r")
    CRLF = "\r\n"
    login = f.readline().split("\n")[0]
    password = f.readline().split("\n")[0]
    attendees = [f.readline().split("\n")[0]]
    organizer = "Awesome-O;CN=Awesome-O:mailto:awesome-o"+CRLF+" @cwi.nl"
    fro = "Awesome-O Master <holanda@cwi.nl>"

    ddtstart = datetime.datetime.now()
    dtoff = datetime.timedelta(days = 1)
    dur = datetime.timedelta(hours = 1)
    ddtstart = ddtstart +dtoff
    dtend = ddtstart + dur
    dtstamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%SZ")
    dtstart = ddtstart.strftime("%Y%m%dT%H%M%SZ")
    dtend = dtend.strftime("%Y%m%dT%H%M%SZ")

    description = "DESCRIPTION: test invitation from pyICSParser"+CRLF
    attendee = ""
    for att in attendees:
        attendee += "ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-    PARTICIPANT;PARTSTAT=ACCEPTED;RSVP=TRUE"+CRLF+" ;CN="+att+";X-NUM-GUESTS=0:"+CRLF+" mailto:"+att+CRLF
    ical = "BEGIN:VCALENDAR"+CRLF+"PRODID:pyICSParser"+CRLF+"VERSION:2.0"+CRLF+"CALSCALE:GREGORIAN"+CRLF
    ical+="METHOD:REQUEST"+CRLF+"BEGIN:VEVENT"+CRLF+"DTSTART:"+dtstart+CRLF+"DTEND:"+dtend+CRLF+"DTSTAMP:"+dtstamp+CRLF+organizer+CRLF
    ical+= "UID:FIXMEUID"+dtstamp+CRLF
    ical+= attendee+"CREATED:"+dtstamp+CRLF+description+"LAST-MODIFIED:"+dtstamp+CRLF+"LOCATION:"+CRLF+"SEQUENCE:0"+CRLF+"STATUS:CONFIRMED"+CRLF
    ical+= "SUMMARY:test "+ddtstart.strftime("%Y%m%d @ %H:%M")+CRLF+"TRANSP:OPAQUE"+CRLF+"END:VEVENT"+CRLF+"END:VCALENDAR"+CRLF

    msg = MIMEMultipart('mixed')
    msg['Reply-To']=fro
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = eml_subject
    msg['From'] = fro
    msg['To'] = ",".join(attendees)

    part_email = MIMEText(eml_body,"html")
    part_cal = MIMEText(ical,'calendar;method=REQUEST')

    msgAlternative = MIMEMultipart('alternative')
    msg.attach(msgAlternative)

    ical_atch = MIMEBase('application/ics',' ;name="%s"'%("invite.ics"))
    ical_atch.set_payload(ical)
    Encoders.encode_base64(ical_atch)
    ical_atch.add_header('Content-Disposition', 'attachment; filename="%s"'%("invite.ics"))

    msgAlternative.attach(part_email)
    msgAlternative.attach(part_cal)

    mailServer = smtplib.SMTP('zwebmail.cwi.nl', 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(login, password)
    mailServer.sendmail(fro, attendees, msg.as_string())
    mailServer.close()

def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)

def announcement_time():
    while True:
        schedule.run_pending()
        time.sleep(60) # wait one minute

class BotHandlerMixin:  
    BOT_URL = None
    #Method to extract chat id from telegram request.
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
    def send_message(self,chat_id,answer):  
        prepared_data = {
            "chat_id": chat_id,
            "text": answer,
        }
        message_url = self.BOT_URL + 'sendMessage'
        requests.post(message_url, json=prepared_data)

class TelegramBot(BotHandlerMixin, Bottle):  
    BOT_URL = 'https://api.telegram.org/bot'
    da_chat_id = ''
    my_name = '@bobot'
    def __init__(self, *args, **kwargs):
        super(TelegramBot, self).__init__()
        self.route('/', callback=self.post_handler, method="POST")
        f = open("config.txt", "r")
        self.BOT_URL += f.readline().split("\n")[0]
        self.da_chat_id = f.readline().split("\n")[0]
        self.my_name =  f.readline().split("\n")[0]
        print (self.BOT_URL )
        print(self.da_chat_id)
        schedule.every().day.at("08:00").do(self.make_announcement)
        schedule.every().monday.at("11:38").do(self.request_speakers)
        thread.start_new_thread(announcement_time, ())  
    
    def addPresentations(date,author,title):
        Insert_statement = 'insert into presentations values ('+date+',' +author+',' + title+')'
        duck_cursor.execute(Insert_statement)

    def query_answer(self,qa_list):
        result_str = ''
        for x in qa_list:
            for y in x:
                result_str += str(y) + ' '
            result_str += '\n'
        return result_str        

    def schedule_madam(self,info):
        meeting_info = info.split(',')
        query = ''
        # (date,author,title)
        if (len(meeting_info) == 3):
            query = "INSERT INTO presentations (presentation_date, author, title) VALUES " + info
        # (date,author,title,zoom_link)
        elif (len(meeting_info) == 4):
            query = "INSERT INTO presentations (presentation_date, author, title,zoom_link) VALUES " + info
        else:
            query = "INSERT INTO presentations VALUES " + info
        try:
            duck_cursor.execute(query)
            return "Madam Scheduled"
        except Exception as e: 
            return "Madam was not scheduled, try either: \n \\schedule_madam ('yyyy-mm-dd','name_author','title') \n \\schedule_madam ('yyyy-mm-dd','name_author','title','zoom_link') \n \\schedule_madam ('yyyy-mm-dd','name_author','title','bio','abstract',zoom_link') \n "str(e)
    def schedule_meeting(self,info):
        meeting_info = info.split(',')
        query = ''
        # (date,author,title)
        if (len(meeting_info) == 3):
            query = "INSERT INTO presentations (presentation_date, author, title) VALUES " + info
        # (date,author,title,zoom_link)
        elif (len(meeting_info) == 4):
            query = "INSERT INTO presentations (presentation_date, author, title,zoom_link) VALUES " + info
        else:
            query = "INSERT INTO presentations VALUES " + info
        try:
            duck_cursor.execute(query)
            return "Meeting Scheduled"
        except Exception as e: 
            return str(e)

    def make_announcement(self):
        duck_cursor.execute("select * from presentations where presentation_date = \'" +datetime.today().strftime('%Y-%m-%d')+ "\'")
        result = duck_cursor.fetchall()
        if (len(result) != 0):
            if(result[0][5]):
                message =  """[beep] Good morning my human friends, Today we have a talk by %s about %s Here is the zoom-link: %s [boop]""" %(result[0][1],result[0][2],result[0][5])
            else:
                message =  """[beep] Good morning my human friends, Today we have a talk by %s about %s [boop]""" %(result[0][1],result[0][2])
            self.send_message(self.da_chat_id,message)
        return

    def request_speakers(self):
        next_monday = next_weekday(datetime.today(), 0)
        next_friday = next_weekday(next_monday, 4)
        missing_presenter = False
        query = "select count(*) from presentations where presentation_date = \'" +next_monday.strftime('%Y-%m-%d')+ "\'"
        print (query)
        duck_cursor.execute(query)
        message = "[beep] Hi humans, we are missing speakers for next week, based on advanced statistics I've decided that: \n"
        if (duck_cursor.fetchone()[0] == 0):
            missing_presenter = True
            duck_cursor.execute("select name from members order by last_madam, name")
            name = duck_cursor.fetchone()[0] 
            message += name + " should give a MADAM on " + next_monday.strftime('%d-%m-%Y') + "\n"
            duck_cursor.execute("update members set last_madam = '" + next_monday.strftime('%Y-%m-%d')+ "' where name = '" + name + "'")
        duck_cursor.execute("select count(*) from presentations where presentation_date = \'" +next_friday.strftime('%Y-%m-%d')+ "\'")
        if (duck_cursor.fetchone()[0] == 0):
            missing_presenter = True
            duck_cursor.execute("select name from members order by last_fatal, name")
            name = duck_cursor.fetchone()[0] 
            message += name + " should give a FATAL on " + next_friday.strftime('%d-%m-%Y') + "\n"
            duck_cursor.execute("update members set last_fatal = '" + next_friday.strftime('%Y-%m-%d') + "' where name = '" + name + "'")
        message += "Talk to me and schedule yourself for your talk ASAP [boop]"
        if (missing_presenter):
            self.send_message(self.da_chat_id,message)
        return 

    def help(self):
        return """You can issue the following commands and I'll respond! 
        \\sql - I'm semi-fluent in sql, just give me a query and I'll run it
        \\insert_madam - Inserts a madam \\insert_madam ('yyyy-mm-dd','author_name','presentation_title')
        \\insert_fatal - Inserts a fatal \\insert_fatal ('yyyy-mm-dd','author_name','presentation_title')
        \\insert_holiday - Inserts a holiday \\insert_holiday('yyyy-mm-dd','holiday_name')
        \\schedule - Schedule meetings
        \\summary - I'll give you a summary of all the metings from today onwards """

    def meeting_next_week(self):
        d = datetime.today()
        next_monday = next_weekday(d, 0)
        duck_cursor.execute("select * from presentations where presentation_date >= \'" +next_monday.strftime('%Y-%m-%d')+ "\' and presentation_date <= \'" +(next_monday+ timedelta(5)).strftime('%Y-%m-%d') +"\'" )
        result = duck_cursor.fetchall()
        if (len(result) == 0):
            return "Uff, no presentation for next week, maybe you should schedule yourself one?"
        else:
            return_string =''
            for r in result:
                return_string += "We have a presentation on " + str(r[0])+ " by: " + r[1] + "\n Title is:" + r[2]
                if (r[5]):
                    return_string += "\n Zoom Link:" + r[5]
                return_string+='\n'
            return return_string

    def meeting_this_week(self):
        d = datetime.today()
        next_monday = next_weekday(d, 0)
        duck_cursor.execute("select * from presentations where presentation_date >= \'" +datetime.today().strftime('%Y-%m-%d')+ "\' and presentation_date < \'" +next_monday.strftime('%Y-%m-%d') +"\'" )
        result = duck_cursor.fetchall()
        if (len(result) == 0):
            return "Uff, no presentation for next week, maybe you should schedule yourself one?"
        else:
            return_string =''
            for r in result:
                return_string += "We have a presentation on " + str(r[0])+ " by: " + r[1] + "\n Title is:" + r[2]
                if (r[5]):
                    return_string += "\n Zoom Link:" + r[5]
                return_string+='\n'
            return return_string 

    def meeting_today(self):
        duck_cursor.execute("select * from presentations where presentation_date = \'" +datetime.today().strftime('%Y-%m-%d')+ "\'")
        result = duck_cursor.fetchall()
        if (len(result) == 0):
            return "No presentations today, maybe you should schedule yourself one?"
        else:
            return_string = "We have a presentation today by: " + result[0][1] + "\n Title is:" + result[0][2]
            if (result[0][5]):
                return_string += "\n Zoom Link:" + result[0][5]
            return return_string

    def run_query(self,query):
        try:
            duck_cursor.execute(query)
        except Exception as e: 
            return str(e)
        return self.query_answer(duck_cursor.fetchall())

    def summary(self):
        return self.run_query( "SELECT presentation_date, author FROM presentations where presentation_date >= \'" +datetime.today().strftime('%Y-%m-%d') + "\' ORDER BY presentation_date")


    
    def help_insert(self):
        return """ You can either do:
        \\schedule ('yyyy-mm-dd',author,title)
        \\schedule ('yyyy-mm-dd',author,title,zoom_link)
        \\schedule ('yyyy-mm-dd',author,title,bio,abstract,zoom_link)
        """

    def what_to_answer(self,chat_id,text):
        first_word = text.split()[0]
        if (first_word == "\\sql"):
            query = text.split(' ', 1)[1]
            if (query.split(' ', 1)[0].lower() == "insert" or query.split(' ', 1)[0].lower() == "delete" or query.split(' ', 1)[0].lower() == "update")
            return "Not allowed yet."
        if (first_word == "\\help"):
           return self.help()
        if (first_word == "\\meeting_today"):
           return self.meeting_today()
        if (first_word == "\\next_week"):
           return self.meeting_next_week()
        if (first_word == "\\this_week"):
           return self.meeting_this_week()
        if (first_word == "\\summary"):
           return self.summary()
        if (first_word == '\\insert_madam'):
            return self.schedule_meeting(text.split(' ', 1)[1])
        if (first_word == '\\insert_fatal'):
            return self.schedule_meeting(text.split(' ', 1)[1])
        return "[Beep] I don't understand what you said, I only understand the language of databases\n Say \\help if you want to know what I am capable of. [Boop]" 

    def post_handler(self):
        data = bottle_request.json
        print(data)
        chat_id = self.get_chat_id(data)
        if (chat_id == -1):
            return response
        input_message = self.get_message(data)
        if (input_message == -1):
            return response
        if self.isgroup(data):
            first_word = input_message.split()[0]
            if (first_word != self.my_name):
                return response
            input_message = input_message.split(' ', 1)[1]
        answer_data = self.what_to_answer(chat_id,input_message)
        for answers in answer_data.split("\n"):
            self.send_message(chat_id,answers)
        return response  # status 200 OK by default

if __name__ == '__main__':
    app = TelegramBot()
    app.run(host='localhost', port=8080)
