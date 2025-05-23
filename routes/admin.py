from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/make-post', methods=['GET', 'POST'])
@login_required
def make_post():
    return render_template('make-post.html')  # Create post template

@admin_bp.route('/post/<int:post_id>')
def view_post(post_id):
    return render_template('post.html', post_id=post_id)  # Single post template
