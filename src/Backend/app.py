import os
import datetime
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, send_from_directory, request
from flask_sqlalchemy import SQLAlchemy
from random import randint
import hashlib
import time

from werkzeug.utils import secure_filename

############################################################################################
# put these 2 lines into terminal before running

# set FLASK_APP=app
# flask initdb
#############################################################################################

# init

app = Flask(__name__)
app.secret_key = "Gallia est omnis divisia in partes tres"
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'app.db')
UPLOAD_FOLDER = os.path.join(app.root_path, 'static')
print(SQLALCHEMY_DATABASE_URI)
print(UPLOAD_FOLDER)
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

SQLALCHEMY_TRACK_MODIFICATIONS = False
app.config.from_object(__name__)
app.config['TESTING'] = False
app.config['DEBUG'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.debug = False
db = SQLAlchemy(app)
db.init_app(app)
boardList = db.Table('boardList',
                     db.Column('boardId', db.Integer, db.ForeignKey('board.boardId')),
                     db.Column('userId', db.Integer, db.ForeignKey('user.userId'))
                     )


class User(db.Model):
    userId = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16), nullable=False)
    password = db.Column(db.String(32), nullable=False)
    lastUploadTime = db.Column(db.Integer, nullable=True)
    lastSignInTime = db.Column(db.Integer, nullable=True)
    boards = db.relationship('Board', backref='user', lazy='dynamic')

    def __init__(self, username, password):
        self.username = username
        self.password = hashlib.md5(password.encode()).hexdigest()

    def __iter__(self):
        return iter(self.userId)


class Board(db.Model):
    boardId = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('user.userId'), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    fileName = db.Column(db.String(32), nullable=False)
    smallScores = db.Column(db.String(170), nullable=True)
    medScores = db.Column(db.String(170), nullable=True)
    largeScores = db.Column(db.String(170), nullable=True)
    ultraScores = db.Column(db.String(170), nullable=True)

    def __init__(self, userId, filename, name):
        self.userId = userId
        self.name = name
        self.fileName = filename
        self.smallScores = ""
        self.medScores = ""
        self.largeScores = ""
        self.ultraScores = ""


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


# dafault page is homepage
@app.route('/')
def default():
    if g.user is not None:
        return render_template('mainPage.html', username=g.user.username)
    else:
        return render_template('mainPage.html')


@app.route('/mainPage/')
def mainPage():
    if g.user is not None:
        return render_template('mainPage.html', username=g.user.username)
    else:
        return render_template('mainPage.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('mainPage', username=g.user.username))

    error = None

    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['user']).first()
        if user is None:
            error = 'Invalid username!'
        elif user.lastSignInTime is not None and user.lastSignInTime > getCurrentTime() - 7:
            user.lastSignInTime = getCurrentTime()
            db.session.commit()
            error = 'Incorrect password was recently entered! Wait a few seconds before trying again!'
        elif user.password == hashlib.md5(request.form['pass'].encode()).hexdigest():
            session['userId'] = user.userId
            user.lastSignInTime = getCurrentTime()
            db.session.commit()
            return redirect(url_for('mainPage', username=user.username))
        else:
            user.lastSignInTime = getCurrentTime()
            db.session.commit()
            error = 'Error! Double-check your password'
    return render_template('login.html', error=error)


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    if g.user:
        return redirect(url_for('mainPage', username=g.user.username))

    error = None

    if request.method == 'POST':
        # check user
        if not request.form['user'] or getUserId(request.form['user']) is not None:
            error = 'Choose a new username!'
        # check pass
        elif not request.form['pass']:
            error = 'You need a password to create an account!'
        # add valid user/pass combo to database
        else:
            db.session.add(User(request.form['user'], request.form['pass']))
            db.session.commit()
            return redirect(url_for('mainPage', username=request.form['user']))

    return render_template('signup.html', error=error)


@app.route('/guide/', methods=['GET'])
def guide():
    return render_template('guide.html')


@app.route('/easyGame/<boardName>', methods=['GET', 'POST'])
def easyGame(boardName):
    print(boardName)
    if request.method == 'POST':
        if g.user is not None:
            gameData = request.json
            print(gameData['score'])
            thisBoard = Board.query.filter_by(fileName=boardName).first()
            thisBoard.smallScores = updateHS(thisBoard.smallScores, g.user.username, int(gameData['score']))
            db.session.commit()
            return render_template('easyGame.html', boardName = boardName)
    elif boardName is None:
        redirect(url_for('mainPage'))
    else:
        return render_template('easyGame.html', boardName = boardName)

@app.route('/easyGameWin/', methods=['GET', 'POST'])
def easyGameWin():
    if request.method == 'POST':
        if g.user is not None:
            gameData = request.json
            print(gameData['score'])
            score = gameData['score']
            boardName = gameData['boardName']
            thisBoard = Board.query.filter_by(fileName=boardName).first()
            thisBoard.smallScores = updateHS(thisBoard.smallScores, g.user.username, int(gameData['score']))
            db.session.commit()
            return render_template('easyGame.html', boardName = boardName)
    else:
        return render_template('mainPage.html')


@app.route('/mediumGame/<boardName>', methods=['GET', 'POST'])
def mediumGame(boardName):
    if request.method == 'POST':
        if g.user is not None:
            gameData = request.json
            print(gameData['score'])
            thisBoard = Board.query.filter_by(fileName=boardName).first()
            thisBoard.medScores = updateHS(thisBoard.medScores, g.user.username, int(gameData['score']))
            db.session.commit()
            return render_template('mediumGame.html', boardName = boardName)
    elif boardName is None:
        redirect(url_for('mainPage'))
    else:
        return render_template('mediumGame.html', boardName = boardName)


@app.route('/hardGame/<boardName>', methods=['GET', 'POST'])
def hardGame(boardName):
    if request.method == 'POST':
        if g.user is not None:
            gameData = request.json
            print(gameData['score'])
            thisBoard = Board.query.filter_by(fileName=boardName).first()
            thisBoard.largeScores = updateHS(thisBoard.largeScores, g.user.username, int(gameData['score']))
            db.session.commit()
            return render_template('hardGame.html', boardName = boardName)
    elif boardName is None:
        redirect(url_for('mainPage'))
    else:
        return render_template('hardGame.html', boardName = boardName)


@app.route('/ultraGame/<boardName>', methods=['GET', 'POST'])
def ultraGame(boardName):
    if request.method == 'POST':
        if g.user is not None:
            gameData = request.json
            print(gameData['score'])
            thisBoard = Board.query.filter_by(fileName=boardName).first()
            thisBoard.ultraScores = updateHS(thisBoard.ultraScores, g.user.username, int(gameData['score']))
            db.session.commit()
            return render_template('ultraGame.html', boardName = boardName)
    elif boardName is None:
        redirect(url_for('mainPage'))
    else:
        return render_template('ultraGame.html', boardName = boardName)


@app.route('/selectGame/', methods=['GET', 'POST'])
def selectGame():
    if request.method == 'POST':
        boardName = request.form['name']
        boardDifficulty = request.form['diff']
        thisBoard = Board.query.filter_by(name=boardName).first()
        if boardName is None or thisBoard is None:
            return render_template('selectGame.html', error="Select a valid game board before beginning!")
        if boardDifficulty == "easy":
            return redirect(url_for('easyGame', boardName=thisBoard.fileName))
        elif boardDifficulty == "medium":
            return redirect(url_for('mediumGame', boardName=thisBoard.fileName))
        elif boardDifficulty == "hard":
            return redirect(url_for('hardGame', boardName=thisBoard.fileName))
        elif boardDifficulty == "ultra":
            return redirect(url_for('ultraGame', boardName=thisBoard.fileName))
        else:
            return redirect(url_for('mainPage'))
    else:
        return render_template('selectGame.html', nameList=getNameList())


@app.route('/highscore/', methods=['GET', 'POST'])
def highscore():
    if request.method == 'POST':
        boardName = request.form['name']
        print(boardName)
        if boardName is None or Board.query.filter_by(name=boardName).first() is None:
            return render_template('highscore.html', error="Select a valid game board to view highscores!",
                                   nameList=getNameList())
        else:
            thisBoard = Board.query.filter_by(name=boardName).first()
            return render_template('highscore.html', nameList=getNameList(), easyList=thisBoard.smallScores.split(" "),
                                   mediumList=thisBoard.medScores.split(" "), hardList=thisBoard.largeScores.split(" "),
                                   ultraList=thisBoard.ultraScores.split(" "))
    else:
        return render_template('highscore.html', nameList=getNameList())


@app.route('/logout/')
def logout():
    if g.user:
        session.pop('userId', None)
    return render_template('logout.html')


@app.route('/upload/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if g.user is not None:
            name = request.form['name']
            if 'file' not in request.files:
                error = 'No file selected!'
                print(error)
                return render_template('upload.html', error=error)

            file = request.files['file']
            if file.filename == '':
                error = 'No selected file!'
                print(error)
                return render_template('upload.html', error=error)
            if not name or Board.query.filter_by(name=name).first() is not None:
                error = 'You need to give the picture a name!!'
                return render_template('upload.html', error=error)
            if g.user.lastSignInTime is not None and g.user.lastSignInTime > getCurrentTime() - 5:
                error = 'You just uploaded a file! Wait a few seconds before adding another!'
                return render_template('upload.html', error=error)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                print(filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                print("file saved")
                print(request.form['name'])
                newBoard = Board(g.user.userId, filename, name)
                print(newBoard)
                db.session.add(newBoard)
                g.user.lastUploadTime = getCurrentTime()
                db.session.commit()
                print(filename)
                return render_template('success.html')
            else:
                print('its still broke')
        else:
            return render_template('mainPage.html')

    else:
        return render_template('upload.html')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


def updateHS(bigString, user, score):
    usList = bigString.split(" ")
    print(usList)
    retString = ""
    scoreList = [(each[0:each.find('-')], each[each.find('-') + 1:]) for each in usList]

    for i in range(10):
        if i >= len(scoreList):
            scoreList.insert(i, (score, user))
            break
        elif score < int(scoreList[i][0]):
            scoreList.insert(i, (score, user))
            break

    for i in range(10):
        if i >= len(scoreList):
            break
        else:
            retString = retString + " " + str(scoreList[i][0]) + "-" + str(scoreList[i][1])

    return retString[1:]


def getNameList():
    nameList = []
    start = len(Board.query.all())
    i = start
    while (i > start - 5):
        nameList.append(Board.query.filter_by(boardId=i).first())
        i = i - 1
    return nameList

def getCurrentTime():
    return int(round(time.time()))


if __name__ == '__main__':
    app.run(host='0.0.0.0')