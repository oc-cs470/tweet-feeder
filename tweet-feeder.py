import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy


CONSUMER_KEY = 'mQssrYDA55cJITEUJiI2A'
CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET', 'CONSUMER_SECRET')
ACCESS_TOKEN = '1541840892-MMEGoRm4kFKKYlHAz6GjCnCp0bNn2vcIOuPexXi'
ACCESS_TOKEN_SECRET = os.environ.get('ACCESS_TOKEN_SECRET', 'ACCESS_TOKEN_SECRET')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tweet-feeder.db'
db = SQLAlchemy(app)


@app.route('/')
def index():
    return 'Tweet Feeder'


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)

