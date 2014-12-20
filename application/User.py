import os
import json
import time

from hashlib import sha1
from flask.ext.login import UserMixin
from sqlalchemy import Column, Integer, String

from config import DIRECTORY, USER_DIR, hashulate, Base

class User(UserMixin, Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
 
    @staticmethod
    def get(userid):
        if not User.query.filter(id=userid):
            return None
        return User(userid=userid)

    @staticmethod
    def new_user():
        with open(os.path.join(DIRECTORY, 'newuser.json'), 'r') as f:
            user = json.loads(f.read())
        print user
        # change this when using SQL
        user_id = sha1(str(time.time())+DIRECTORY).hexdigest()
        user['id'] = user_id
        return user_id

    @staticmethod
    def check_password(userid, password):
        with open(User.UserFile.format(userid), 'r') as f:
            expected = json.loads(f.read())['password']
        if expected == hashulate(password):
            return True
        return False
    
    def __init__(self, userid=None, username=None, password=None):
        if not userid:
            #fix this when implementing SQL
            self.username = username
            self.user = {}
            self['id'] = User.new_user()
            self['username'] = username
            self['password'] = hashulate(password)
            User.add_to_table(username, self['id'])
            self.save()
        else:
            with open(User.UserFile.format(userid), 'r') as f:
                self.user = json.loads(f.read())
  
    def is_authenticated(self):
        """Returns True if the user is authenticated, i.e. they have provided 
        valid credentials. (Only authenticated users will fulfill the criteria 
        of login_required.)"""
        return True

    def is_active(self):
        """Returns True if this is an active user - in addition to being 
        authenticated, they also have activated their account, not been 
        suspended, or any condition your application has for rejecting an 
        account. Inactive accounts may not log in (without being forced of 
        course)."""
        return True

    def is_anonymous(self):
        """Returns True if this is an anonymous user. (Actual users should 
        return False instead.)"""
        return False

    def get_id(self):
        """Returns a unicode that uniquely identifies this user, and can be 
        used to load the user from the user_loader callback. Note that this 
        must be a unicode - if the ID is natively an int or some other type, 
        you will need to convert it to unicode."""
        return self['id']

    def __setitem__(self, key, value):
        self.user[key] = value

    def __getitem__(self, key):
        return self.user[key]

    def __repr__(self):
        return '<User %r>' % (self.username)

    def save(self):
        with open(User.UserFile.format(self['id']), 'w') as f:
            f.write(json.dumps(self.user))

    def invite(self, game_id):
        self['invites'] += game_id

    def current_game(self):
        return self['current_game_id']

    @staticmethod
    def add_to_table(username, user_id):
        with open(User.UserTable, 'r') as f:
            users = json.loads(f.read())
        users[username] = user_id
        with open(User.UserTable, 'w') as f:
            f.write(json.dumps(users))

    @staticmethod
    def username_taken(username):
        with open(User.UserTable, 'r') as f:
            users = json.loads(f.read())
        return True if username in users else False

    @staticmethod
    def id_from_name(username):
        with open(User.UserTable, 'r') as f:
            user_id = json.loads(f.read())[username]
        return user_id

    def current_games(self):
        response = {}
        for game in self['games']:
            game = Game(game_id=game)
            response[game['id']] = game.model(self['id'])
        print response
        return json.dumps(response)

    def __enter__(self):
        return self

    def __exit__(self):
        self.save()
