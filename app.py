import os
import random

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///final.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show homepage"""
    return render_template("index.html")


@app.route("/hiragana")
@login_required
def hiragana():
    """Display Hiragana Chart"""
    return render_template("hiragana.html")


@app.route("/record")
@login_required
def record():
    """Show past record of quiz results"""
    # define lists
    username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
    username = username[0]["username"]
    lists = db.execute("SELECT type,datetime FROM record WHERE username = ?", username)

    # display history page
    return render_template("record.html", lists = lists)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Save into record
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        username = username[0]["username"]
        db.execute("INSERT INTO record (type,username) VALUES(?,?)", "LOGIN", username)

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    #save into records
    username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
    username = username[0]["username"]
    db.execute("INSERT INTO record (type,username) VALUES(?,?)", "LOGOUT", username)

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/katakana")
@login_required
def katakana():
    """Show katakana table"""
    return render_template("katakana.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # clear session
    session.clear()

    # if user arrives via GET
    if request.method == "GET":
        return render_template("register.html")

    # if user arrives via POST
    elif request.method == "POST":

        # check if username is blank
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # check if username has already existed
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) == 1:
            return apology("username has already been taken", 400)

        # check if password or confirmation is blank
        if not request.form.get("password"):
            return apology("must provide password", 400)
        if not request.form.get("confirmation"):
            return apology("must provide confirmation password", 400)

        # check if confirmation matches with password
        if request.form.get("confirmation") != request.form.get("password"):
            return apology("Confirmation does not match with password", 400)

        # check if password has at least 8 letters
        if len(request.form.get("password")) < 8:
            return apology("Password must include at least 8 letters", 400)

        # insert new user into database
        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, password)

        # Keep track of which user is logged in
        id = db.execute("SELECT id FROM users WHERE username = ?", request.form.get("username"))
        session["user_id"] = id[0]["id"]

        # Celebrate in records
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        username = username[0]["username"]
        db.execute("INSERT INTO record (type,username) VALUES(?,?)", "FIRST LOGIN", username)

        # redirect user to homepage
        return redirect("/")


@app.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():
    """Execute quiz"""
    # If user arrives via GET
    if request.method == "GET":
        return render_template("quiz.html")

    # If user arrives via POST (PLAY QUIZ)
    if request.method == "POST":

        Questions = ["あ","い","う","え","お","か","き","く","け","こ","さ","し","す","せ","そ","た","ち","つ","て","と","な","に","ぬ",
                "ね","の","は","ひ","ふ","へ","ほ","ま","み","む","め","も","や","ゆ","よ","ら","り","る","れ","ろ","わ","を","ん",
                "ア","イ","ウ","エ","オ","カ","キ","ク","ケ","コ","サ","シ","ス","セ","ソ","タ","チ","ツ","テ","ト","ナ","ニ","ヌ",
                "ネ","ノ","ハ","ヒ","フ","ヘ","ホ","マ","ミ","ム","メ","モ","ヤ","ユ","ヨ","ラ","リ","ル","レ","ロ","ワ","ヲ","ン"]

        Answers = ["a","i","u","e","o","ka","ki","ku","ke","ko","sa","shi","su","se","so","ta","chi","tsu","te","to","na","ni","nu",
                "ne","no","ha","hi","fu","he","ho","ma","mi","mu","me","mo","ya","yu","yo","ra","ri","ru","re","ro","wa","wo","n",
                "a","i","u","e","o","ka","ki","ku","ke","ko","sa","shi","su","se","so","ta","chi","tsu","te","to","na","ni","nu",
                "ne","no","ha","hi","fu","he","ho","ma","mi","mu","me","mo","ya","yu","yo","ra","ri","ru","re","ro","wa","wo","n",]

        # select a random number between 0 and 91 inclusive
        n = random.randint(0,91)

        # select random question
        RandomQuestion = Questions[n]
        RandomAnswer = Answers[n]

        #display question
        return render_template("question.html", RandomQuestion=RandomQuestion, RandomAnswer=RandomAnswer)



