import requests  
from bottle import Bottle, response, request as bottle_request
import duckdb
from datetime import datetime,timedelta
import schedule
import time
import thread

db = duckdb.connect('presentations_cwi.db')
duck_cursor = db.cursor()
# weekday = 0 (monday)
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

    def schedule_meeting(self,chat_id):
        self.send_message(chat_id,"What date you want to schedule the meeting? yyyy-mm-dd")
        data = bottle_request.json
        input_message = self.get_message(data)
        duck_cursor.execute("select count(*) from presentations where presentation_date = \'" +str(input_message)+ "\'")
        print (duck_cursor.fetchone())

    def make_announcement(self):
        duck_cursor.execute("select * from presentations where presentation_date = \'" +datetime.today().strftime('%Y-%m-%d')+ "\'")
        result = duck_cursor.fetchall()
        if (len(result) != 0):
            if(result[0][5]):
                message =  """[beep] Good morning my human friends, Today we have a talk by %s about %s Here is the zoom-link: %s [boop]""" %(result[0][1],result[0][2],result[0][5])
            else:
                message =  """[beep] Good morning my human friends, Today we have a talk by %s about %s [boop]""" %(result[0][1],result[0][2])
            self.send_message(self.da_chat_id,message)
        # else:
        #     message = """Good morning human friends, we don't have a presentation today. Happy Hacking!"""
        return

    def help(self):
        return """You can issue the following commands and I'll respond! 
        \\execute_query - I'm semi-fluent in sql, just tell me what you want
        \\meeting_today - I'll tell you if we have a meeting today 
        \\meeting_this_week - Do we have meetings this week?
        \\meeting_next_week - I'll tell you the meeting we have for next week
        \\help_insert - I'll give you a template to insert a meeting"""
        # schedule_meeting - if you want to schedule a meeting 
        # \\meeting_today - I'll tell you if we have a meeting today
    
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
                # if (r[3]):
                #     return_string += "\n Bio :" + r[3]
                # if (r[4]):
                #     return_string += "\n Abstract :" + r[4]
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
                # if (r[3]):
                #     return_string += "\n Bio :" + r[3]
                # if (r[4]):
                #     return_string += "\n Abstract :" + r[4]
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
            # if (result[0][3]):
            #     return_string += "\n Bio :" + result[0][3]
            # if (result[0][4]):
            #     return_string += "\n Abstract :" + result[0][4]
            if (result[0][5]):
                return_string += "\n Zoom Link:" + result[0][5]
            return return_string
    def help_insert(self):
        return """ I only have one table presentations(presentation_date Date NOT NULL UNIQUE, author String NOT NULL, title String NOT NULL, bio String, abtract string, zoom_link String);
        one insert example is \\execute_query insert into presentations values ('2020-05-08', ' tiago kepe', 'in memory processing',NULL,NULL,NULL)"""

    def what_to_answer(self,chat_id,text):
        first_word = text.split()[0]
        if (first_word == "\\create_table"):
            return "Not authorized"
            # print (create_table())
            # return "Table created, my good friend"
        if (first_word == "\\drop_table"):
            return "Not authorized"
            # print (drop_table())
            # return "Cleaning Complete beep"
        if (first_word == "\\execute_query"):
            try:
                duck_cursor.execute(text.split(' ', 1)[1])
            except Exception as e: 
                return str(e)
            return self.query_answer(duck_cursor.fetchall())
        if (first_word == "\\help"):
           return self.help()
        if (first_word == "\\meeting_today"):
           return self.meeting_today()
        if (first_word == "\\help_insert"):
           return self.help_insert()
        if (first_word == "\\meeting_next_week"):
           return self.meeting_next_week()
        if (first_word == "\\meeting_this_week"):
           return self.meeting_this_week()
        return "Beep Boop, I only understand the language of databases\n Say \\help if you want to know what I am capable of." 

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
