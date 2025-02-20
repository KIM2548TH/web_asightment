from flask import redirect, url_for, request, session, render_template
from flask_login import current_user, LoginManager, login_url, logout_user
from werkzeug.exceptions import Forbidden, Unauthorized
import models
from functools import wraps

login_manager = LoginManager()

def init_acl(app):
    login_manager.init_app(app)
    login_manager.login_view = "login"  # ตั้งค่าหน้าเว็บที่ต้องการให้ผู้ใช้ไปเมื่อยังไม่ได้ล็อกอิน

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id)) # กําหนดการโหลดผู้ใช้งานจาก ID

def roles_required(*roles):
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login', next=request.url))
            
            user_roles = {role.name for role in current_user.roles}
            if any(role in user_roles for role in roles):
                return func(*args, **kwargs)
            
            raise Forbidden("You do not have permission to access this resource.")
        return wrapped
    return wrapper