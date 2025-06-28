from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import LoginManager
from flask_gravatar import Gravatar
from flask_sqlalchemy import SQLAlchemy

bootstrap = Bootstrap5()
ckeditor = CKEditor()
login_manager = LoginManager()
gravatar = Gravatar(size=100, rating='g', default='retro')
db = SQLAlchemy()
