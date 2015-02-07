__author__ = 'genro'
# -*- coding: utf-8 -*# -
import re
import random
import sys
import sqlite3
import time
from itertools import permutations
import threading
import Queue
import vk
import chatterbotapi
import collections

DB_QUEUE = Queue.Queue()
VK_DICT = collections.OrderedDict()
VK_DICT_MUTEX = threading.Lock()
OUT_QUEUE = Queue.Queue()
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
        answer = unfixed.replace('|', '\u').decode('unicode_escape')
        question = s
        DB_QUEUE.put(question, answer)
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

    def get_not_answered(self):
        con = sqlite3.connect(self.name)
        cur = con.cursor()

        with con:
            cur.execute("SELECT * FROM NotAnswered")
            try:
                choice = random.choice(cur.fetchall())[0]
            except IndexError:
                choice = False
            cur.execute("DELETE FROM NotAnswered WHERE question == ?", (choice,))
        return choice

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
        threading.Thread.__init__(self)

    def run(self):
        while True:
            try:
                question, answer = DB_QUEUE.get()
            except Queue.Empty:
                pass
            else:
                self.db.save(question, answer)


class VK_Thread(threading.Thread):
    def __init__(self, vkapi):
        self.vkapi = vkapi
        threading.Thread.__init__(self)

    def run(self):
        while True:
            messages = self.vkapi.messages.getDialogs(unread=1)['items']
            time.sleep(0.5)
            for message in messages:
                message['mark'] = False
                with VK_DICT_MUTEX:
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




