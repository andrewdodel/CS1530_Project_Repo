import os
import datetime
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash
from flask_sqlalchemy import SQLAlchemy
############################################################################################
#put these 2 lines into terminal before running

#set FLASK_APP=app
#flask initdb
#############################################################################################

#init
app = Flask(__name__)
app.secret_key = "Gallia est omnis divisia in partes tres"
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
app.config.from_object(__name__)
app.config['TESTING'] = True
app.debug = True
db = SQLAlchemy(app)
db.init_app(app)
boardList = db.Table('boardList',
                            db.Column('boardId', db.Integer, db.ForeignKey('board.boardId')),
                            db.Column('userId', db.Integer, db.ForeignKey('user.userId')))

class User(db.Model):
    userId = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), nullable=False)
    password = db.Column(db.String(16), nullable=False)
    boards = db.relationship('Board', backref='user', lazy='dynamic')

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __iter__(self):
        return iter(self.userId)

class Board(db.Model):
    boardId = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('user.userId'), nullable=False)
    name = db.Column(db.String(32), nullable=False)

    def __init__(self, boardId, userId, name):
        self.boardId = boardId
        self.userId = userId
        self.name = name

# init db
@app.cli.command('initdb')
def initdb():
    db.drop_all()
    db.create_all()
    db.session.commit()

def getUserId(username):
    user = User.query.filter_by(username=username).first()
    return user.userId if user else None

@app.before_request
def before_request():
    g.user = None
    if 'userId' in session:
        g.user = User.query.filter_by(userId=session['userId']).first()

#dafault page is homepage
@app.route('/')
def default():
    return redirect(url_for('mainPage'))

@app.route('/mainPage/')
def mainPage():
    return render_template('mainPage.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('patronPage', username=g.user.username))

    error = None

    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['user']).first()

        if user is None:
            error = 'Invalid username!'

        elif user.password == request.form['pass']:
            session['userId'] = user.userId
            return redirect(url_for('mainPage', username=user.username))
        else:
            error = 'Error! Double-check your password'

    return render_template('login.html', error=error)

@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    if g.user:
        return redirect(url_for('mainPage', username=g.user.username))

    error = None

    if request.method == 'POST':
        #check user
        if not request.form['user'] or getUserId(request.form['user']) is not None:
            error = 'Choose a new username!'
        #check pass
        elif not request.form['pass']:
            error = 'You need a password to create an account!'
         #add valid user/pass combo to database
        else:
            db.session.add(User(request.form['user'], request.form['pass']))
            db.session.commit()
            return redirect(url_for('mainPage'))

    return render_template('signup.html', error=error)

@app.route('/logout/')
def logout():
    if g.user:
        session.pop('userId', None)
    return render_template('logout.html')

if __name__ == '__main__':
    app.run()
