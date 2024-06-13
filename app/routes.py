from flask import Blueprint, render_template, url_for, flash, redirect, request
from app import db, bcrypt
from app.models import User, Task
from app.forms import TaskForm
from app.forms import LoginForm
from flask_login import login_user, current_user, logout_user, login_required

main = Blueprint('main', __name__)


@main.route("/")
def entrance():
    return render_template('index.html')
@main.route("/home")
def home():
    search_query = request.args.get('q')
    if search_query:
        tasks = Task.query.filter(
            Task.title.contains(search_query) | Task.description.contains(search_query)).filter_by(
            author=current_user).all()
    else:
        tasks = Task.query.filter_by(author=current_user).order_by(Task.due_date.asc()).all()
    return render_template('home.html', title='Home', tasks=tasks)

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html')


@main.route("/login", methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()

    if form.validate_on_submit():
        # Attempt to find the user by email
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            # Check if the password matches
            if user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('main.home'))
            else:
                flash('Login Unsuccessful. Please check email and password', 'danger')
        else:
            flash('Login Unsuccessful. User does not exist.', 'danger')

    return render_template('login.html', title='Login', form=form)
@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.entrance'))

@main.route("/account")
@login_required
def account():
    return render_template('account.html')

@main.route("/task/new", methods=['GET', 'POST'])
@login_required
def new_task():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(title=form.title.data, description=form.description.data,
                    due_date=form.due_date.data, category=form.category.data, author=current_user)
        db.session.add(task)
        db.session.commit()
        flash('Your task has been created!', 'success')
        return redirect(url_for('main.home'))
    return render_template('create_task.html', title='New Task', form=form)


@main.route("/task/<int:task_id>/delete", methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.author != current_user:
        flash('You are not authorized to delete this task.', 'danger')
        return redirect(url_for('main.home'))
    # Delete the task from the database
    db.session.delete(task)
    db.session.commit()

    flash('Your task has been deleted!', 'success')
    return redirect(url_for('main.home'))

@main.route("/task/<int:task_id>")
def task(task_id):
    task = Task.query.get_or_404(task_id)
    return render_template('task.html', title=task.title, task=task)

@main.route("/task/<int:task_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.author != current_user:
        flash('You are not authorized to delete this task.', 'danger')
        return redirect(url_for('main.home'))
    form = TaskForm(obj=task)
    if form.validate_on_submit():
        form.populate_obj(task)  # Update task fields with form data
        db.session.commit()
        flash('Your task has been updated!', 'success')
        return redirect(url_for('main.home'))

    return render_template('edit_task.html', title='Edit Task', form=form)