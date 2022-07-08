from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from datetime import datetime
import os

app = Flask(__name__)


#Connect to Database
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todolist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Table User Configuration
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    user_name = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    tasks = db.relationship('Task', backref='user')


class Task(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    title = db.Column(db.String(100), unique=False, nullable=False)
    details = db.Column(db.String(500), nullable=True)
    completed = db.Column(db.Boolean, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False)
    date_completed = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
# db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/create-account", methods=['GET', "POST"])
def create_account():
    if request.method == "POST":

        if User.query.filter_by(user_name=request.form.get('user-name')).first():
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            user_name=request.form.get('user-name'),
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("todo_list"))

    return render_template("create-account.html", logged_in=current_user.is_authenticated)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('user-name')
        password = request.form.get('password')

        user = User.query.filter_by(user_name=username).first()
        # Email doesn't exist or password incorrect.
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('todo_list'))

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/todo-list", methods=["GET", "POST"])
@login_required
def todo_list():
    if request.method == "POST":
        title = request.form.get('task-title')
        date_finish = datetime.strptime(request.form.get('complete-date'), '%Y-%m-%d')
        details = request.form.get('task-details')
        complete = False
        today = datetime.now()
        user = current_user.id
        new_task = Task(title=title, details=details, date_completed=date_finish, completed=complete, date_created=today, user_id=user)
        db.session.add(new_task)
        db.session.commit()
        print(date_finish)
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template("todos.html", username=current_user.user_name, tasks=tasks, logged_in=True)


@app.route('/checked/<taskid>')
@login_required
def task_checked(taskid):
    task_to_update = Task.query.filter_by(id=taskid).first()
    print(taskid)
    print(task_to_update.id)
    if not task_to_update.completed:
        setattr(task_to_update, 'completed', True)
        print("set to true")
        db.session.commit()
    else:
        setattr(task_to_update, 'completed', False)
        print("set to false")
        db.session.commit()
    return redirect(url_for('todo_list'))


if __name__ == '__main__':
    app.run(debug=True)
