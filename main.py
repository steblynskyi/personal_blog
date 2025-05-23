from datetime import date, datetime
import os
import smtplib
import logging

from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

# Environment variables
GMAIL_SMTP_ADDRESS = os.environ.get("GMAIL_SMTP_ADDRESS")
GMAIL_SMTP_EMAIL = os.environ.get("GMAIL_SMTP_EMAIL")
GMAIL_SMTP_PASSWORD = os.environ.get("GMAIL_SMTP_PASSWORD")
FLASK_KEY = os.environ.get("FLASK_KEY")
DB_URL = os.environ.get("DB_URL", "sqlite:///posts.db")

# Validate environment variables
for var in [GMAIL_SMTP_ADDRESS, GMAIL_SMTP_EMAIL, GMAIL_SMTP_PASSWORD, FLASK_KEY]:
    if var is None:
        raise ValueError("One or more environment variables are not set.")

app.config['SECRET_KEY'] = FLASK_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL

# Initialize extensions
ckeditor = CKEditor(app)
Bootstrap5(app)
login_manager = LoginManager(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro')

# Database setup
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Database models
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")

    def __init__(self, email, password, name):
        self.email = email
        self.password = password
        self.name = name

class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    post_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")

with app.app_context():
    db.create_all()

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

# User registration
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if db.session.execute(db.select(User).where(User.email == form.email.data)).scalar():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("blog.get_all_posts"))
    return render_template("register.html", form=form, current_user=current_user, year=datetime.now().year)

# User login
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))

        if not check_password_hash(user.password, form.password.data):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('get_all_posts'))

    return render_template("login.html", form=form, current_user=current_user, year=datetime.now().year)

# User logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))

# Display all blog posts
@app.route('/')
def get_all_posts():
    posts = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template("index.html", all_posts=posts, current_user=current_user, year=datetime.now().year)

# Show a specific post and handle comments
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for("show_post", post_id=post_id))

    return render_template("post.html", post=requested_post, current_user=current_user, form=comment_form, year=datetime.now().year)

# Admin-only route to add a new post
@app.route("/new-post", methods=["GET", "POST"])
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
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("blog.get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user, year=datetime.now().year)

# Admin-only route to edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
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
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user, year=datetime.now().year)

# Admin-only route to delete a post
@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

# About page
@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user, year=datetime.now().year)

# Validate form data
def validate_form(data):
    required_fields = ["name", "email", "phone", "message"]
    return all(field in data and data[field] for field in required_fields)

# Send email function
def send_email(name, email, phone, message):
    try:
        with smtplib.SMTP(GMAIL_SMTP_ADDRESS, 587) as connection:
            connection.starttls()
            connection.login(user=GMAIL_SMTP_EMAIL, password=GMAIL_SMTP_PASSWORD)
            connection.sendmail(
                from_addr=GMAIL_SMTP_EMAIL,
                to_addrs=GMAIL_SMTP_EMAIL,
                msg=f"Subject:New Message from {name}\n\n"
                    f"Name: {name}\n"
                    f"Email: {email}\n"
                    f"Phone: {phone}\n"
                    f"Message: {message}"
            )
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

# Contact page and email sending
@app.route("/contact", methods=["GET", "POST"])
def contact():
    msg_sent = False
    if request.method == "POST":
        data = request.form
        if validate_form(data):
            send_email(data["name"], data["email"], data["phone"], data["message"])
            msg_sent = True
            return render_template("contact.html", msg_sent=msg_sent, year=datetime.now().year)
    return render_template("contact.html", msg_sent=msg_sent, year=datetime.now().year)

if __name__ == "__main__":
    app.run(
        debug=True,
        port=5001
    )