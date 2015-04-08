# -*- coding: utf-8 -*-
from nose.tools import *
from VeraBot.VeraBot import *

def test_DB():
    db = DB('test.db')
    assert_equal(db.name, 'test.db')
    assert_equal(list(db.get_all_not_answered()), list())
    db.save('fuck', 'fuck')
    assert_equal(db.get_by_masks(['fuck']), 'fuck')

def test_DB_thread():
    db_thread = DB_Thread('test.db')
    db_thread.start()
    for i in xrange(100):
        DB_QUEUE.put((str(i), str(i+1)))
    db_thread.join()

#test_DB_thread()

def test_VK_thread():
    pass
app_id = '4677976'
user_name = 'genroe@mail.ru'
password = raw_input('>')
token = '8b3aa3c88b75ace274ee670cfe8223ea15b92d74de7ccebf80928e54ca82a6990ebbe33e8c8c1a3a8547f'
vkapi = vk.API(app_id, user_name, password, timeout=1.5)
vkapi.access_token = token
#print vkapi.messages.getDialogs(unread=1)['items']
vk_thread = Simle_VK_Thread(vkapi)
db_thread = DB_Thread('test.db')
c_bot = CBot()
def session():
    while True:
        try:
            message = IN_QUEUE.get()
            print "SESSION GOT!"
        except Queue.Empty:
            print "IN EMPty"
        else:
            question = message['body']
            message['body'] = c_bot.think(message)
            print "IN: %s Out: %s " % (question, message['body'])
            OUT_QUEUE.put(message)
ses = threading.Thread(target=session)
ses2 = threading.Thread(target=session)
ses.start()
vk_thread.start()
db_thread.start()
vk_thread.join()
db_thread.join()
ses.join()
