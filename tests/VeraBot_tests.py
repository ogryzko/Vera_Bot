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

