"""Message model tests."""


# run these tests like:
#
#    python -m unittest test_message_model.py




import os
from unittest import TestCase
from sqlalchemy import exc


from models import db, User, Message, Follows, Likes


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"




# Now we can import app


from app import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data


db.create_all()




class UserModelTestCase(TestCase):
    """Test views for messages."""


    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()


        self.uid = 94566
        u = User.signup("testing", "testing@test.com", "password", None)
        u.id = self.uid
        db.session.commit()


        self.u = User.query.get(self.uid)


        self.client = app.test_client()


    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


    def test_message_model(self):
        """Does basic model work?"""
       
        m = Message(
            text="a warble",
            user_id=self.uid
        )


        db.session.add(m)
        db.session.commit()


        # User should have 1 message
        self.assertEqual(len(self.u.messages), 1)
        self.assertEqual(self.u.messages[0].text, "a warble")


    def test_message_likes(self):
        m1 = Message(
            text="a warble",
            user_id=self.uid
        )


        m2 = Message(
            text="a very interesting warble",
            user_id=self.uid
        )


        u = User.signup("yetanothertest", "t@email.com", "password", None)
        uid = 888
        u.id = uid
        db.session.add_all([m1, m2, u])
        db.session.commit()


        u.likes.append(m1)


        db.session.commit()


        l = Likes.query.filter(Likes.user_id == uid).all()
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0].message_id, m1.id)




       

Message
"""Message View tests."""


# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py




import os
from unittest import TestCase


from models import db, connect_db, Message, User




os.environ['DATABASE_URL'] = "postgresql:///warbler-test"



from app import app, CURR_USER_KEY




db.create_all()





app.config['WTF_CSRF_ENABLED'] = False




class MessageViewTestCase(TestCase):
    """Test views for messages."""


    def setUp(self):
        """Create test client, add sample data."""


        db.drop_all()
        db.create_all()


        self.client = app.test_client()


        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 8989
        self.testuser.id = self.testuser_id


        db.session.commit()


    def test_add_message(self):
        """Can use add a message?"""


       

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id


           

            resp = c.post("/messages/new", data={"text": "Hello"})


            self.assertEqual(resp.status_code, 302)


            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")


    def test_add_no_session(self):
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))


    def test_add_invalid_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 99222224 # user does not exist


            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
   
    def test_message_show(self):


        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser_id
        )
       
        db.session.add(m)
        db.session.commit()


        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
           
            m = Message.query.get(1234)


            resp = c.get(f'/messages/{m.id}')


            self.assertEqual(resp.status_code, 200)
            self.assertIn(m.text, str(resp.data))


    def test_invalid_message_show(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
           
            resp = c.get('/messages/99999999')


            self.assertEqual(resp.status_code, 404)


    def test_message_delete(self):


        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser_id
        )
        db.session.add(m)
        db.session.commit()


        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id


            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)


            m = Message.query.get(1234)
            self.assertIsNone(m)


    def test_unauthorized_message_delete(self):



        u = User.signup(username="unauthorized-user",
                        email="testtest@test.com",
                        password="password",
                        image_url=None)
        u.id = 76543


        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser_id
        )
        db.session.add_all([u, m])
        db.session.commit()


        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 76543


            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))


            m = Message.query.get(1234)
            self.assertIsNotNone(m)


    def test_message_delete_no_authentication(self):


        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser_id
        )
        db.session.add(m)
        db.session.commit()


        with self.client as c:
            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))


            m = Message.query.get(1234)
            self.assertIsNotNone(m)
