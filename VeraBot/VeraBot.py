import requests

__author__ = 'genro'
# -*- coding: utf-8 -*# -
import re
import random
import sys
import sqlite3
import time
import requests
import json
from itertools import permutations
import threading
import Queue
import vk
import chatterbotapi
import collections

DB_QUEUE = Queue.Queue()
VK_DICT = collections.OrderedDict()
VK_DICT_MUTEX = threading.Lock()
IN_QUEUE = Queue.Queue()
OUT_QUEUE = Queue.Queue()
NOT_ANSWERED = Queue.Queue()
ITS_NOT_TIME_TO_DIE = threading.Event()
ITS_NOT_TIME_TO_DIE.set()
USTAT = dict()

reload(sys)
sys.setdefaultencoding('utf-8')


def parse(s):
    delete = re.compile(u'\W+?', re.UNICODE)
    words = delete.sub(' ', s.lower()).split()
    for i, word in enumerate(words):
        words[i] = '%s%s%s' % (word[0], '_' * (len(word) - 2), word[-1])
    masks = []
    if len(words) <= 3:
        for perm in permutations(words):
            masks.append(u'%'.join(perm) + '%')
            perm = list(perm)
            perm.pop()
            masks.append((u'%'.join(perm)) + '%')
        return masks
    else:
        pass


def sql_from_masks(masks):
    mask = masks.pop()
    sql = "SELECT * FROM Answers WHERE question LIKE '%s'" % mask
    for mask in masks:
        sql += " OR SELECT * FROM Answers WHERE question LIKE '%s'" % mask
    return sql


class Session():
    def __init__(self):
        pass


class Dialog(threading.Thread):
    def __init__(self):
        self.person = Person()
        self.c_bot = CBot()
        threading.Thread.__init__(self)

    def run(self):
        while ITS_NOT_TIME_TO_DIE.is_set():
            with VK_DICT_MUTEX:
                message = None
                for key in VK_DICT:
                    if VK_DICT[key]['mark'] is True:
                        pass
                    elif VK_DICT[key]['mark'] is False:
                        message = VK_DICT[key]
                        VK_DICT[key]['mark'] = True
                        break
            if message is None:
                pass
            else:
                answer_message = self.c_bot.think(message)
                mid = message['id']
                uid = message['user_id']
                OUT_QUEUE.put((mid, uid, answer_message))
        pass


def make_long_poll_settings(vk_long_poll_settings):
    return vk_long_poll_settings['server'], vk_long_poll_settings['key'], vk_long_poll_settings['ts']


class LongPollServer(object):
    def __init__(self, vkapi):
        self.vkapi = vkapi
        self.decoder = json.JSONDecoder(strict=False)
        self.connected = False

    def connect(self):
        time.sleep(0.5)
        vk_long_poll_settings = self.vkapi.messages.getLongPollServer()
        self.server, self.key, self.ts = make_long_poll_settings(vk_long_poll_settings)
        self.connected = True

    def get_updats(self):
        if self.connected is False:
            self.connect()
            return self.get_updats()
        else:
            idx = 0
            url = 'http://%s?act=a_check&key=%s&ts=%s&wait=25&mode=2' % (self.server, self.key, self.ts)
            permanent_response = requests.get(url)
            dict_response, idx = self.decoder.raw_decode(permanent_response.text, idx)
            if 'failed' in dict_response:
                self.connect()
                return self.get_updats()
            else:
                self.ts = dict_response['ts']
                updates = dict_response['updates']
                return updates

    def get_unreaded_messages(self):
        EVENT_NEW_MESSAGE = 4
        FLAG_UNREADED = 1
        updates = self.get_updats()
        messages = []
        unformated_messages = filter(lambda x: x[0] == EVENT_NEW_MESSAGE, updates)
        for item in unformated_messages:
            if item[2] is not FLAG_UNREADED:
                pass
            else:
                message = {}
                message['id'] = item[1]
                message['user_id'] = item[3]
                message['body'] = item[6]
                message['attachments'] = item[7]
                messages.append(message)
        return messages

class Person(object):
    def __init__(self, id=None):
        self.id = id

    def think(self, message):
        mid = message['id']
        uid = self.id
        OUT_QUEUE.put((mid, uid, message['body']))
        while True:
            with VK_DICT_MUTEX:
                for m in reversed(VK_DICT):
                    if m is mid:
                        break
                    elif VK_DICT[m]['user_id'] is uid:
                        question, answer = message['body'], VK_DICT[m]['body']
                        DB_QUEUE.put((question, answer))
                        return answer
                    elif USTAT[uid] is 'offline':
                        return False
                    else:
                        raise IdError('Something wrong with Person %d' % uid)


class VBot(object):
    def __init__(self, db=None):
        self.DB = db

    def think(self, s):
        masks = parse(s)
        answer = DB.get_by_masks(masks)
        if not answer:
            self.DB.save(s)
            return DB.get_not_answered()
        else:
            return answer
        pass

    pass


class CBot(object):
    def __init__(self):
        factory = chatterbotapi.ChatterBotFactory()
        bot = factory.create(chatterbotapi.ChatterBotType.CLEVERBOT)
        self.bot = bot.create_session()

    def think(self, message):
        s = message['body']
        unfixed = self.bot.think(s)
        answers = \
                [u'\u0421\u0430\u043b\u044c\u0441\u0438\u0440\u0443\u0439 \u0447\u043b\u0435\u043d\u0438\u043d\u043d\u043a\u0441!',
                 u'\u0417\u0430\u0442\u043a\u043d\u0438\u0441\u044c \u043d\u0430\u0445\u0443\u0439, \u0414\u043e\u043d\u043d\u0438',
                 u'\u0421\u0443\u0431\u0431\u043e\u0442\u0430, \u0414\u043e\u043d\u043d\u0438, \u044d\u0442\u043e \u0448\u0430\u0431\u0431\u0430\u0442 \u2014 \u0435\u0432\u0440\u0435\u0439\u0441\u043a\u0438\u0439 \u0434\u0435\u043d\u044c \u043e\u0442\u0434\u044b\u0445\u0430. \u042d\u0442\u043e \u0437\u043d\u0430\u0447\u0438\u0442, \u044f \u043d\u0435 \u0440\u0430\u0431\u043e\u0442\u0430\u044e, \u043d\u0435 \u0432\u043e\u0436\u0443 \u043c\u0430\u0448\u0438\u043d\u0443, \u043d\u0435 \u043a\u0430\u0442\u0430\u044e\u0441\u044c, \u0431\u043b\u044f\u0434\u044c, \u043d\u0430 \u043c\u0430\u0448\u0438\u043d\u0435, \u043d\u0435 \u0431\u0435\u0440\u0443 \u0432 \u0440\u0443\u043a\u0438 \u0434\u0435\u043d\u044c\u0433\u0438, \u043d\u0435 \u0432\u043a\u043b\u044e\u0447\u0430\u044e \u043f\u043b\u0438\u0442\u0443 \u0438 \u0448\u0430\u0440\u044b \u0442\u043e\u0436\u0435 \u043d\u0438\u0445\u0443\u044f \u043d\u0435 \u043a\u0430\u0442\u0430\u044e!! \u0421\u043e\u0431\u043b\u044e\u0434\u0430\u0442\u044c \u0448\u0430\u0431\u0431\u0430\u0442!',
                  u'\u043a\u0435\u043d\u0442 \u0438 \u0431\u0440\u043e \u0432\u0435\u043a\u0442\u043e\u0440\u0430!',
                 u'\u0415\u0434\u0438\u043d\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439 \u0441\u043f\u043e\u0441\u043e\u0431 \u0431\u044b\u0442\u044c \u0441\u0447\u0430\u0441\u0442\u043b\u0438\u0432\u044b\u043c \u2014 \u044d\u0442\u043e \u043b\u044e\u0431\u0438\u0442\u044c \u0441\u0442\u0440\u0430\u0434\u0430\u043d\u0438\u044f.',
                 u'\u0447\u0442\u043e-\u0442\u043e \u044f \u0447\u0430\u0441\u0442\u043e \u043f\u043e\u0432\u0442\u043e\u0440\u044f\u044e\u0441\u044c'
]
        if 'clever' in unfixed.lower() or unfixed == '' or 'ios' in unfixed.lower():
            answer = random.choice(answers)
        else:
            answer = unfixed.replace('|', '\u').decode('unicode_escape')
            r = random.randint(0, 1)
            if 5 == random.randint(0, 10):
                answer = random.choice(answers)
            elif r == 0:
                answer = answer[0].lower() + answer[1:]
            else:
                pass
        question = s
        tuple = (question, answer)
        DB_QUEUE.put(tuple)
        return answer

    pass


class Bot(object):
    def __init__(self, id=None, db=None, api=None):
        self.person = Person(id, api, db)
        self.v_bot = VBot(db)
        self.c_bot = CBot(db)

    def set_person(self, person):
        self.person = person

    def think_p(self, s):
        self.person.think(s)

    def think_v(self, s):
        self.v_bot.think(s)

    def think_c(self, s):
        self.c_bot.think(s)

    def think(self, mod=None):
        pass


def kill_all():
    ITS_NOT_TIME_TO_DIE.clear()


class DB(object):
    def __init__(self, name):
        con = sqlite3.connect(name)
        cur = con.cursor()
        self.name = name
        with con:
            cur.executescript("""
            CREATE TABLE IF NOT EXISTS Answers (question TEXT, answer TEXT);
            CREATE TABLE IF NOT EXISTS NotAnswered (question TEXT);
            """)

    def save(self, question=None, answer=None):
        con = sqlite3.connect(self.name)
        cur = con.cursor()
        delete = re.compile(u'\W+?', re.UNICODE)
        with con:
            if answer is None:
                cur.execute("INSERT INTO NotAnswered VALUES(?)", (question,))
            elif answer is not None:
                question = delete.sub(' ', question.lower())
                try:
                    cur.execute("INSERT INTO Answers VALUES(?, ?)", (question, answer))
                except sqlite3.OperationalError:
                    self.save(question, answer)
            else:
                print 'WTF?'

    def drop(self):
        con = sqlite3.connect(self.name)
        cur = con.cursor()

        with con:
            cur.executescript("""
            DROP TABLE IF EXISTS Answers;
            DROP TABLE IF EXISTS NotAnswered;
            """)
            self.__init__(self.name)

    def print_table(self):
        con = sqlite3.connect(self.name)
        cur = con.cursor()
        cur.execute("SELECT * FROM Answers")
        answeres = cur.fetchall()
        print '-' * 20
        for ans in answeres:
            print ans[0], ans[1]

    def get_all_not_answered(self):
        con = sqlite3.connect(self.name)
        cur = con.cursor()

        with con:
            cur.execute("SELECT * FROM NotAnswered")
            for question in cur.fetchall():
                yield question

    def get_by_masks(self, masks):
        con = sqlite3.connect(self.name)
        cur = con.cursor()
        sql_command = sql_from_masks(masks)

        with con:
            cur.execute(sql_command)
            rows = cur.fetchall()
            try:
                answer = random.choice(rows)[1]
                ###############!!!!!!!!!!!
            except IndexError:
                answer = False
        return answer

    def shuffle(self):
        con = sqlite3.connect(self.name)
        cur = con.cursor()

        with con:
            cur.execute("SELECT * FROM Answers")
            rows = cur.fetchall()
            random.shuffle(rows)
            for i, row in enumerate(rows):
                if i == 30:
                    break
                else:
                    self.save(row[1], row[0])

    pass


class DB_Thread(threading.Thread):
    def __init__(self, name):
        self.db = DB(name)
        for question in self.db.get_all_not_answered():
            NOT_ANSWERED.put(question)
        threading.Thread.__init__(self)
        self.daemon = True

    def run(self):
        while True:
            try:
                question, answer = DB_QUEUE.get()
            except Queue.Empty:
                pass
            else:
                self.db.save(question, answer)
                #self.db.print_table()
        # self.db.clear_not_answered()
        while NOT_ANSWERED.not_empty:
            question = NOT_ANSWERED.get()
            self.db.save(question)


class VK_Thread(threading.Thread):
    def __init__(self, vkapi):
        self.vkapi = vkapi
        threading.Thread.__init__(self)

    def LazyChek(self):
        pass

    def run(self):
        while True:
            messages = self.vkapi.messages.getDialogs(unread=1)['items']
            time.sleep(0.5)
            with VK_DICT_MUTEX:
                for message in messages:
                    message['mark'] = False
                    if 'id' in message:
                        if message['id'] not in VK_DICT:
                            VK_DICT[message['id']] = message
                        elif VK_DICT[message['mark']] is True:
                            pass
                        else:
                            VK_DICT[message['id']] = message
                    else:
                        pass
            try:
                mid, uid, message = OUT_QUEUE.get()
            except Queue.Empty:
                pass
            else:
                self.vkapi.messages.markAsRead(mid)
                time.sleep(0.5)
                self.vkapi.messages.send(user_id=uid, message=message)
                time.sleep(0.5)
                with VK_DICT_MUTEX:
                    del VK_DICT[mid]

class Simle_VK_Thread(VK_Thread):
    def Vk_online(self):
        time.sleep(0.5)
        try:
            self.vkapi.account.setOnline()
            return time.sleep(0.5)
        except:
            return None

    def run(self):
        vk_code = """var requests=API.friends.getRequests();
        var ids=requests.items;
        var num=requests.count;
        var i=0; while(i<num){
            API.friends.add({"user_id":ids[i]});
            i=i+1;};
        var mes=API.messages.getDialogs({"unread":1}).items@.message;
        var mids=mes@.id;
        API.messages.markAsRead({"message_ids":mids});
        API.account.setOnline();
        return mes;"""
        messages = []
        while True:
            try:
                time.sleep(0.6)
                messages = self.vkapi.execute(code=vk_code)
            except:
                time.sleep(0.6)
                messages = self.vkapi.execute(code=vk_code)
            if messages == []: pass
            else:
                print messages
                for message in messages:
                    if 'fwd_messages' in message:
                        message['body'] = message['fwd_messages'][0]['body']
                    else:
                        pass
                    IN_QUEUE.put(message)
                try:
                    message = OUT_QUEUE.get()
                except Queue.Empty:
                    pass
                else:
                    uid = message['user_id']
                    answer = message['body']
                    if 'chat_id' in message:
                        chid = message['chat_id']
                        self.vkapi.messages.setActivity(chat_id=str(chid), type='typing')
                        time.sleep(2)
                        self.vkapi.messages.send(chat_id=chid, message=answer)
                    else:
                        self.vkapi.messages.setActivity(user_id=str(uid), type='typing')
                        time.sleep(2)
                        self.vkapi.messages.send(user_id=uid, message=answer)


class LongPoll_VK_Thread(threading.Thread):
    def __init__(self, vkapi):
        self.vkapi = vkapi
        self.long_poll_server = LongPollServer(vkapi)
        threading.Thread.__init__(self)

    def run(self):
        SetOnline_Add_Friends = """var requests=API.friends.getRequests();
        var ids=requests.items;
        var num=requests.count;
        var i=0; while(i<num){
            API.friends.add({"user_id":ids[i]});
            i=i+1;};
        API.account.setOnline();"""
        while True:
            messages = self.long_poll_server.get_unreaded_messages()
            if messages is []:
                pass
            else:
                print messages
                for message in messages:
                    IN_QUEUE.put(message)
                try:
                    message = OUT_QUEUE.get()
                except Queue.Empty:
                    pass
                else:
                    time.sleep(0.5)
                    mid = message['id']
                    self.vkapi.markAsRead(message_ids=list(mid))
                    uid = message['user_id']
                    answer = message['body']
                    time.sleep(0.5)
                    self.vkapi.messages.setActivity(user_id=str(uid), type='typing')
                    time.sleep(2)
                    self.vkapi.messages.send(user_id=uid, message=answer)







class IdError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class MultiApi(vk.API):
    def __init__(self, app_id, user_name, password, vk_mutex):
        self.vk_mutex = vk_mutex
        vk.API.__init__(self, app_id=app_id, user_login=user_name, user_password=password)

    def __getattr__(self, item):
        with self.vk_mutex:
            vk.API.__getattr__(self, method_name=item)
            time.sleep(1)

    pass


if __name__ == '__main__':
    pass




