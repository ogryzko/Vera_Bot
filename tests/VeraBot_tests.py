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

print vkapi.messages.getDialogs(unread=1)['items']
vkapi.access_token = token
vk_thread = Simle_VK_Thread(vkapi)
db_thread = DB_Thread('test.db')
c_bot = CBot()
def session():
    while True:
        try:
            message = IN_QUEUE.get()
        except Queue.Empty:
            pass
        else:
            mid = message['id']
            uid = message['user_id']
            message = c_bot.think(message)
            print message
            OUT_QUEUE.put((mid, uid, message))
ses = threading.Thread(target=session)
ses.start()
vk_thread.start()
db_thread.start()
vk_thread.join()
db_thread.join()
ses.join()
