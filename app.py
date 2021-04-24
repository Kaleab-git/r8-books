#TODO: calculate average_score of a book
#TODO: in verification code html attach link 
#TODO: hash passwords
#TODO: to figure out if user has signed in yet. If so display: sign out. If not, display: sign in

import os
import random
from threading import Thread
from flask import Flask, render_template, session, redirect, url_for, request, abort
from flask_session import Session
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, validators
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_mail import Mail, Message

basedir = os.path.abspath(os.path.dirname(__file__))
   
app = Flask(__name__)


# Check for environment variable
# if not os.getenv("DATABASE_URL"):
#     raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://dvtrtgheuraofs:a0f1eb545d56c5d3b1b2faac7497be47472dc6eb4469a0242dd57c7abfd08879@ec2-107-22-245-82.compute-1.amazonaws.com:5432/dfubjh8odsr8th"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASKY_MAIL_SENDER'] = 'r8-Books kaleabgirmat@gmail.com'
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN')

bootstrap = Bootstrap(app)
mail = Mail(app)


# Set up database
engine = create_engine("postgresql://dvtrtgheuraofs:a0f1eb545d56c5d3b1b2faac7497be47472dc6eb4469a0242dd57c7abfd08879@ec2-107-22-245-82.compute-1.amazonaws.com:5432/dfubjh8odsr8th")
db = scoped_session(sessionmaker(bind=engine))

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)
def send_email(to, subject, template, **kwargs):
    msg = Message(subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


class NameForm(FlaskForm):
    email = StringField('Email address', validators=[DataRequired()])
    f_name = StringField('Fisrt Name', validators=[DataRequired()])
    l_name = StringField('Last Name', validators=[DataRequired()])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm Password')
    submit = SubmitField('Submit')
class LoginForm(FlaskForm):
    email = StringField('Email address', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')
class VerificationCode(FlaskForm):
    code_attempt = StringField('Enter Code here', validators=[DataRequired()])
    submit = SubmitField('Submit')
class SearchBook(FlaskForm):
    query = StringField("", validators=[DataRequired()])
    submit = SubmitField('Submit')
# @app.shell_context_processor
# def make_shell_context():
#     return dict(db=db, User=User, Role=Role)


@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/register', methods=["POST", "GET"])
def register():
    form = NameForm()
    if request.method == 'GET': return render_template('register.html', form=form)
    if request.method == 'POST':
        if form.password.data != form.confirm.data: return render_template('register.html', form=form, msg="Password Doesn't Match")
        if form.validate_on_submit():
            # user = User.query.filter_by(email=form.email.data).first()
            user = db.execute(f"select * from users where email='{form.email.data}';")
            if not user.fetchone():
                code = gen_random_str()
                session['code'] = code
                send_email(form.email.data, 'Verification Code',
                            'mail/new_user', user=form.email.data, code=code)
                return redirect(url_for('verify_user', email=form.email.data, f_name=form.f_name.data, l_name=form.l_name.data, password=form.password.data))
            else: return render_template('register.html', form=form, msg="Email already Exists!")
        else: return render_template('register.html', form=form, msg="Make sure you entered a valid information")


@app.route('/verify_user', methods=['POST','GET'])
def verify_user(): #resend verification code OR wrong email OR check code
    if 'code' not in session: redirect(url_for('login'))
    user = request.args.get('user')
    form = VerificationCode()
    if request.method == 'GET': return render_template('enter_code.html', form=form, email=request.args.get('email'), wrong_attempt=False)
    elif request.method == 'POST':
        if form.validate_on_submit():
            code_attempt = form.code_attempt.data
            if code_attempt != session['code']:
                return render_template('enter_code.html', form=form, user=user, wrong_attempt=True)
            else:
                email=request.args.get('email'); f_name=request.args.get('f_name'); l_name=request.args.get('l_name'); password=request.args.get('password')
                db.execute(f"insert into users (email,f_name,l_name,password) values ('{email}','{f_name}','{l_name}','{password}');")
                return redirect(url_for('login'))

@app.route('/login', methods=['POST', 'GET'])
def login():
    session.clear()
    form = LoginForm()
    if request.method == 'GET': return render_template('login.html', form=form)
    if request.method == 'POST':
        user = db.execute(f"select * from users where email='{form.email.data}';").fetchone()
        if not user or user['password'] != form.password.data:  return render_template('login.html', form=form, msg='Incorrect Credentials')
        session['current_user_email'] = user['email']
        session['current_user_name'] = user['f_name']
        return redirect(url_for('homepage'))

@app.route('/homepage.html', methods=['POST', 'GET'])
def homepage():
    if 'current_user_email' not in session: redirect(url_for('login')) #means the url was accessed directly without logging in
    form = SearchBook()
    if request.method == 'GET': return render_template('homepage.html', form=form, name=session['current_user_name'])
    query = f"%{form.query.data}%" #sandwitch the query in between %% to tell our db we're looking for a pattern and not an exact match
    result = db.execute(f"select * from books where isbn like '%{query}%' or lower(title) like lower('%{query}%') or lower(author) like lower('%{query}%') or year like '%{query}%';").fetchall()
    if not result: return render_template('homepage.html', form=form, name=session['current_user_name'], books=result, search=False)
    return render_template('homepage.html', form=form, name=session['current_user_name'], books=result)

@app.route('/homepage.html/ratebook', methods=['POST', 'GET'])
def ratebook():
    isbn = request.args.get('isbn')
    book = db.execute(f"select * from books where isbn='{isbn}';").fetchone()
    reviews = db.execute(f"select * from reviews where isbn='{isbn}';").fetchall() 
    if request.method == 'GET':
        email = session["current_user_email"] 
        user_review = db.execute(f"select * from reviews where isbn='{isbn}' and email='{email}';").fetchone()
        if not user_review: user_review = False 
        reviews = db.execute(f"select * from reviews where isbn='{isbn}' and email not in ('{email}');").fetchall()
        return render_template('ratebook.html', book=book, reviews=reviews, user_review=user_review)
    if request.method == 'POST':
        rating = request.form['rating']
        review_content = fix_stirng(request.form.get('review_content'))
        email = session["current_user_email"]
        user_review = db.execute(f"select * from reviews where isbn='{isbn}' and email='{email}';").fetchone()
        if user_review: return render_template('ratebook.html', book=book, reviews=reviews, user_review=user_review)
        db.execute(f"insert into reviews (email,isbn,review_content,rating) values ('{email}','{isbn}','{review_content}','{rating}');")
        db.execute("COMMIT;")
        review_count = book['review_count']
        average_score = book['average_score']
        if not review_count: review_count = 0
        if not average_score: average_score = 0
        db.execute(f"update books set review_count = {review_count+1};")
        db.execute(f"update books set average_score = {((int(average_score)*int(review_count))+int(rating))/(int(review_count)+1)};")        
        db.execute("COMMIT;")
        book = db.execute(f"select * from books where isbn='{isbn}';").fetchone()
        reviews = db.execute(f"select * from reviews where isbn='{isbn}';").fetchall() 
        user_review = db.execute(f"select * from reviews where isbn='{isbn}' and email='{email}';").fetchone() 
        return render_template('ratebook.html', book=book, reviews=reviews, user_review=user_review)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

def gen_random_str():
    string = "0123456789"
    return "".join(random.choice(string) for _ in range(5))

def fix_stirng(string):
    new_string = "" 
    for letter in string:
        if letter=="'": new_string += "'" + letter
        else: new_string += letter
    return new_string

def search_api(isbn):
    url = f"https://www.googleapis.com/books/v1/volumes?q={isbn}+isbn:keyes&key=AIzaSyAyNQ4uim767INfNoBLkYUspa2ioxbAJCY"