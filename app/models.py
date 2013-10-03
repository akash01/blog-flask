from app import db
import datetime
from sqlalchemy import Sequence
from werkzeug import generate_password_hash, check_password_hash

ROLE_USER = 0
ROLE_ADMIN = 1

# user 
class User(db.Model):
    id = db.Column(db.Integer, Sequence('user_id_seq'), primary_key=True)
    #id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100))
    lastname = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    #password = db.Column(db.String(100))
    pwdhash = db.Column(db.String(254))
    role = db.Column(db.Integer, default = 0)
    posts = db.relationship('Post',backref='author',lazy = 'dynamic')

    def __init__(self, firstname, lastname, email, password):
        self.firstname = firstname.title()
        self.lastname = lastname.title()
        self.email = email.lower()
        self.set_password(password)

    def set_password(self, password):
        self.pwdhash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pwdhash, password)

    def is_authenticated(self):
        return True

    def get_id(id):
        for user in User:
            if user[0] == id:
                return user(user[0], [1])
        return None

    def __repr__(self):
        return '<User %r>' % (self.email)

# posts
class Post(db.Model):
    id = db.Column(db.Integer, Sequence('post_id_seq'), primary_key=True)
    title = db.Column(db.String(100))
    body = db.Column(db.Text())
    pub_date = db.Column(db.DateTime, default = datetime.datetime.now() )
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    #tags = db.Column(db.String(100))
    #tags = db.relationship('Tag', backref='tags',lazy = 'dynamic')

    # many to many Post<->Tag
    tags = db.relationship('Tag',secondary='post_tags',backref=db.backref('posts', lazy='dynamic'))

    #include tags in the init__(self,tags)
    def __init__(self, title, body, pub_date,user_id):
        self.title = title
        self.body = body
        self.pub_date = datetime.datetime.now()
        self.user_id = user_id

    def __repr__(self):
        return '<Post %r>' % (self.title)

#tags
class Tag(db.Model):
    id = db.Column(db.Integer, Sequence('tag_id_seq'), primary_key=True)
    name = db.Column(db.String(64))

    def __init__(self, name):
        self.name = name
    
    @classmethod
    def get_or_create(cls, tag_name):
        tag = cls.query.filter_by(name=tag_name).first()
        
        if not tag:
            tag = cls(tag_name)
            db.session.add(tag)
            db.session.commit()
        return tag

    @classmethod
    def update_tag(cls, tag_name):
        tag = cls.query.filter_by(name=tag_name).first()
        
        if tag:
            tag = cls(tag_name)
            db.session.merge(tag)
            db.session.commit()
            return tag
    
    def __repr__(self):
        return '<Tag %r>' % (self.name)

# Association tables
post_tags = db.Table('post_tags', db.Model.metadata,
    db.Column('post_id', db.Integer, 
              db.ForeignKey('post.id', ondelete='CASCADE', onupdate='CASCADE')),
    db.Column('tag_id', db.Integer,
              db.ForeignKey('tag.id', ondelete='CASCADE', onupdate='CASCADE')))

