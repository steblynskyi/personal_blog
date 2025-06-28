import logging
import os
from datetime import date, datetime
import smtplib
from functools import wraps

from flask import Blueprint, abort, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db, login_manager
from .forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from .models import BlogPost, User, Comment

main = Blueprint('main', __name__)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


def validate_form(data):
    required_fields = ["name", "email", "phone", "message"]
    return all(field in data and data[field] for field in required_fields)


def send_email(name, email, phone, message):
    try:
        with smtplib.SMTP(os.environ["GMAIL_SMTP_ADDRESS"], 587) as connection:
            connection.starttls()
            connection.login(user=os.environ["GMAIL_SMTP_EMAIL"], password=os.environ["GMAIL_SMTP_PASSWORD"])
            connection.sendmail(
                from_addr=os.environ["GMAIL_SMTP_EMAIL"],
                to_addrs=os.environ["GMAIL_SMTP_EMAIL"],
                msg=f"Subject:New Message from {name}\n\n"
                    f"Name: {name}\n"
                    f"Email: {email}\n"
                    f"Phone: {phone}\n"
                    f"Message: {message}"
            )
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if db.session.execute(db.select(User).where(User.email == form.email.data)).scalar():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('main.login'))
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8),
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('main.get_all_posts'))
    return render_template('register.html', form=form, current_user=current_user, year=datetime.now().year)


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if not user:
            flash('That email does not exist, please try again.')
            return redirect(url_for('main.login'))

        if not check_password_hash(user.password, form.password.data):
            flash('Password incorrect, please try again.')
            return redirect(url_for('main.login'))

        login_user(user)
        return redirect(url_for('main.get_all_posts'))
    return render_template('login.html', form=form, current_user=current_user, year=datetime.now().year)


@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.get_all_posts'))


@main.route('/')
def get_all_posts():
    posts = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template('index.html', all_posts=posts, current_user=current_user, year=datetime.now().year)


@main.route('/post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('You need to login or register to comment.')
            return redirect(url_for('main.login'))
        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('main.show_post', post_id=post_id))
    return render_template('post.html', post=requested_post, current_user=current_user, form=comment_form, year=datetime.now().year)


@main.route('/new-post', methods=['GET', 'POST'])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime('%B %d, %Y')
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('main.get_all_posts'))
    return render_template('make-post.html', form=form, current_user=current_user, year=datetime.now().year)


@main.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for('main.show_post', post_id=post.id))
    return render_template('make-post.html', form=edit_form, is_edit=True, current_user=current_user, year=datetime.now().year)


@main.route('/delete/<int:post_id>')
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('main.get_all_posts'))


@main.route('/about')
def about():
    return render_template('about.html', current_user=current_user, year=datetime.now().year)


@main.route('/contact', methods=['GET', 'POST'])
def contact():
    msg_sent = False
    if request.method == 'POST':
        data = request.form
        if validate_form(data):
            send_email(data['name'], data['email'], data['phone'], data['message'])
            msg_sent = True
            return render_template('contact.html', msg_sent=msg_sent, year=datetime.now().year)
    return render_template('contact.html', msg_sent=msg_sent, year=datetime.now().year)

