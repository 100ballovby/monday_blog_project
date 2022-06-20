import published as published
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app import app, login, db
from forms import LoginForm, RegistrationForm, EditProfileForm, PostForm
from wtforms.validators import ValidationError
from models import User, Post
from datetime import datetime


@login.user_loader
def load_user(id):
    return User.query.get(int(id))  # достает пользователя из базы данных и запоминает его


@app.route('/', methods=['GET', 'POST'])
def main_page():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main_page'))
    posts = Post.query.order_by(Post.published.desc()).all()
    return render_template('index.html', form=form, posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main_page'))
    form = LoginForm()
    if form.validate_on_submit():  # если форма отправляется
        user = User.query.filter_by(username=form.username.data).first()  # пытаюсь найти пользователя в БД по логину
        if user is None or not user.check_password(form.password.data):
            # если пользователь не найден в БД или пароль не совпал
            return redirect(url_for('login'))  # вернуть пользователя на страницу входа
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main_page'))
    return render_template('login.html', title='Login page', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main_page'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:  # если пользователь вошел
        return redirect(url_for('index'))  # перенаправим на главную
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            form.check_username(form.username)
            form.check_email(form.email)
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            db.session.add(user)  # добавить пользователя в БД
            db.session.commit()  # сохранить пользователя в БД
            flash('Вы успешно зарегистрированы!', 'success')
            return redirect(url_for('login'))  # перенаправить на страницу входа
        except ValidationError:
            flash('Пользователь с такими данными уже существует!', 'danger')
            return redirect(url_for('register'))
    return render_template('register.html', form=form)


@app.route('/support')
@login_required
def support():
    return render_template('support.html')


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.published.desc())
    return render_template('user.html', user=user, posts=posts)


@app.before_request  # при подключении
def before_request():
    if current_user.is_authenticated:  # если пользователь вошел на сайт
        current_user.last_seen = datetime.utcnow()  # переписываем время последнего визита
        db.session.commit()  # обновляем данные в базе


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about = form.about_me.data
        db.session.commit()
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about
    return render_template('edit_profile.html', form=form)