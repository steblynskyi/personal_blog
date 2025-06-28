from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, ValidationError
from wtforms.validators import DataRequired, Email, Length, URL, EqualTo
from flask_ckeditor import CKEditorField


# Custom validator for password strength
def password_strength(form, field):
    if len(field.data) < 8 or not any(char.isdigit() for char in field.data):
        raise ValidationError("Password must be at least 8 characters long and contain at least one number.")


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired(), Length(max=150)], render_kw={"placeholder": "Enter the title of your blog post"})
    subtitle = StringField("Subtitle", validators=[DataRequired(), Length(max=150)], render_kw={"placeholder": "Enter a catchy subtitle"})
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()], render_kw={"placeholder": "Enter a valid URL for the blog image"})
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post", render_kw={"class": "btn btn-primary"})


# Create a form to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message="Invalid email address.")], render_kw={"placeholder": "Enter your email"})
    password = PasswordField("Password", validators=[DataRequired(), password_strength], render_kw={"placeholder": "Enter a strong password"})
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password', message="Passwords must match.")], render_kw={"placeholder": "Re-enter your password"})
    name = StringField("Name", validators=[DataRequired(), Length(max=100)], render_kw={"placeholder": "Enter your full name"})
    submit = SubmitField("Sign Me Up!", render_kw={"class": "btn btn-success"})


# Create a form to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message="Invalid email address.")], render_kw={"placeholder": "Enter your email"})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={"placeholder": "Enter your password"})
    submit = SubmitField("Let Me In!", render_kw={"class": "btn btn-info"})


# Create a form to add comments
class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment", render_kw={"class": "btn btn-secondary"})
