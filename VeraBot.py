__author__ = 'genro'
# -*- coding: utf-8 -*-
import vk
import re
import random
import sys
import sqlite3
import time
import chatterbotapi
from itertools import permutations


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


class Session(object):
    pass


class Dialog(object):
    def __init__(self, person, bot, api, db):
        self.person = person
        self.bot = bot
        self.API = api
        self.DB = db

    def start(self):
        num = 0
        while num <= 10:
            question = self.person.say()
            if not question:
                return False, num
            else:
                answer = self.bot.think(question)
                if not answer:
                    return False, num
                else:
                    self.person.think(answer)
            num += 1
        return self.person.id, num
        pass


class Person(object):
    def __init__(self, id=None, api=None, db=None):
        self.id = id
        self.api = api
        self.DB = db

    def say(self, n=0):
        if n == 350:
            return False
        messages = [i['message'] for i in self.api.messages.getDialogs(unread=1)['items']]
        all_ids = [message['user_id'] for message in messages]
        if self.id in all_ids:
            index = all_ids.index(id)
            answer = messages[index]['body']
            return answer
        else:
            n += 1
            time.spleep(10)
            return self.say(n)

    def think(self, s):
        self.api.messages.send(user_id=self.id, message=s)
        answer = self.say()
        if not answer:
            answer = DB.get_not_answered()
            self.DB.save(s)
            return answer
        else:
            self.DB.save(s, answer)
            return answer
        pass


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
    def __init__(self, db=None):
        self.DB = db
        factory = chatterbotapi.ChatterBotFactory()
        bot = factory.create(chatterbotapi.ChatterBotType.CLEVERBOT)
        self.bot = bot.create_session()

    def think(self, s):
        unfixed = self.bot.think(s)
        answer = unfixed.replace('|', '\u').decode('unicode_escape')
        question = s
        if self.DB is not None:
            self.DB.save(question, answer)
        else:
            pass
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

        with con:
            if answer is None:
                question = question.lower()
                cur.execute("INSERT INTO NotAnswered VALUES(?)", (question,))
            elif answer is not None:
                question = question.lower()
                answer = answer.lower()
                cur.execute("INSERT INTO Answers VALUES(?, ?)", (question, answer))
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
            choice = random.choice(cur.fetchall())
            cur.execute("DELETE FROM NotAnswered WHERE question == ?", (choice,))
        return choice[0]

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


class IdError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


if __name__ == '__main__':
    pass




