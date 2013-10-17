#!/usr/bin/env python

import base64
import os
from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.mail import Mail, Message
from flask_oauth import OAuth


CONSUMER_KEY = 'mQssrYDA55cJITEUJiI2A'
CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET', 'CONSUMER_SECRET')
ACCESS_TOKEN = '1541840892-MMEGoRm4kFKKYlHAz6GjCnCp0bNn2vcIOuPexXi'
ACCESS_TOKEN_SECRET = os.environ.get('ACCESS_TOKEN_SECRET', 'ACCESS_TOKEN_SECRET')


app = Flask(__name__)
app.secret_key = 'cheeseburger'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tweet-feeder.db'
db = SQLAlchemy(app)
oauth = OAuth()
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'marcus.darden@cs.olivetcollege.edu'
mail_password = os.environ.get('MAIL_PASSWORD', 'password')
mail_password = base64.b64decode(mail_password)
app.config['MAIL_PASSWORD'] = mail_password.strip()
app.config['MAIL_DEFAULT_SENDER'] = 'marcus.darden@cs.olivetcollege.edu'
mailer = Mail(app)

twitter = oauth.remote_app('twitter',
                           base_url='https://api.twitter.com/1.1/',
                           request_token_url='https://api.twitter.com/oauth/request_token',
                           access_token_url='https://api.twitter.com/oauth/access_token',
                           authorize_url='https://api.twitter.com/oauth/authenticate',
                           consumer_key=CONSUMER_KEY,
                           consumer_secret=CONSUMER_SECRET)


class User(db.Model):
    id = db.Column('user_id', db.Integer, primary_key=True)
    name = db.Column(db.String(60))
    oauth_token = db.Column(db.String(100))
    oauth_secret = db.Column(db.String(100))

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<User %s>' % self.name


#class Tweet(db.Model):
    #pass


@app.route('/')
def index():
    return render_template('index.html', tweets=None)


@app.route('/feed')
def feed():
    return 'Display feed here...'


@app.route('/mail')
def mail():
    msg = Message('Test message subject.')
    msg.add_recipient('marcus.darden@cs.olivetcollege.edu')
    mailer.send(msg)
    return 'Message sent!'


@app.route('/login')
def login():
    """Calling into authorize will cause the OpenID auth machinery to kick
    in.  When all worked out as expected, the remote application will
    redirect back to the callback URL provided.
    """
    print 'request.args', request.args
    print 'request.referrer', request.referrer
    url = url_for('authorized', next=request.args.get('next') or request.referrer or None)
    print url
    return twitter.authorize(callback=url)


@app.route('/authorized')
@twitter.authorized_handler
def authorized(resp):
    """Called after authorization.  After this function finished handling,
    the OAuth information is removed from the session again.  When this
    happened, the tokengetter from above is used to retrieve the oauth
    token and secret.

    Because the remote application could have re-authorized the application
    it is necessary to update the values in the database.

    If the application redirected back after denying, the response passed
    to the function will be `None`.  Otherwise a dictionary with the values
    the application submitted.  Note that Twitter itself does not really
    redirect back unless the user clicks on the application name.
    """
    next_url = request.args.get('next') or url_for('feed')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    user = User.query.filter_by(name=resp['screen_name']).first()

    # user never signed on
    if user is None:
        user = User(resp['screen_name'])
        db.session.add(user)
    print resp
    print next_url

    # in any case we update the authenciation token in the db
    # In case the user temporarily revoked access we will have
    # new tokens here.
    user.oauth_token = resp['oauth_token']
    user.oauth_secret = resp['oauth_token_secret']
    db.session.commit()

    session['user_id'] = user.id
    flash('You were signed in')
    return redirect(next_url)


@twitter.tokengetter
def get_twitter_token():
    """This is used by the API to look for the auth token and secret
    it should use for API calls.  During the authorization handshake
    a temporary set of token and secret is used, but afterwards this
    function has to return the token and secret.  If you don't want
    to store this in the database, consider putting it into the
    session instead.
    """
    user = g.get('user', None)
    if user is not None:
        return user.oauth_token, user.oauth_secret


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


@app.after_request
def after_request(response):
    db.session.remove()
    return response


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)

