from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('index.html')  # Homepage template

@main_bp.route('/about')
def about():
    return render_template('about.html')  # About page

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')  # Contact page
