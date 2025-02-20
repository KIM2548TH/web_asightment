import flask
from flask import render_template, redirect, url_for, flash
from models import db, User, Role, Note, Tag
import forms
import acl
from flask import Blueprint
from flask_login import LoginManager, login_required, login_user, logout_user

module = Blueprint("templates", __name__)

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

# สร้าง LoginManager
login_manager = LoginManager()
login_manager.init_app(app)  # ตั้งค่า LoginManager

# ตั้งค่าฟังก์ชันสำหรับโหลดผู้ใช้
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

db.init_app(app)

@app.route("/")
def index():
    notes = Note.query.order_by(Note.title).all()
    return render_template("index.html", notes=notes)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = forms.LoginForm()  # สร้างฟอร์มล็อกอิน
    if form.validate_on_submit():  # ตรวจสอบการส่งฟอร์ม
        user = User.query.filter_by(username=form.username.data).first()  # ค้นหาผู้ใช้
        if user and user.authenticate(form.password.data):  # ตรวจสอบรหัสผ่าน
            login_user(user)  # ล็อกอินผู้ใช้
            return redirect(url_for("index"))
        flash("Invalid username or password", "danger")
    return render_template("login.html", form=form)  # แสดงฟอร์ม

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash("บัญชีนี้มีอยู่แล้ว กรุณาใช้ชื่อผู้ใช้อื่น", "danger")
            return render_template("register.html", form=form)
        
        user = User()
        form.populate_obj(user)
        role = Role.query.filter_by(name="user").first()
        if not role:
            role = Role(name="user")
            db.session.add(role)
        user.roles.append(role)
        user.password_hash = form.password.data
        db.session.add(user)
        db.session.commit()
        flash("ลงทะเบียนสำเร็จ! กรุณาเข้าสู่ระบบ", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/page")
@acl.roles_required("admin")
def page():
    return render_template("page.html")

@app.route("/page2")
@login_required
def page2():
    return render_template("page_2.html")

@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    tag = Tag.query.filter_by(name=tag_name).first()
    notes = tag.notes if tag else []
    return render_template("tags_view.html", tag_name=tag_name, notes=notes)

@app.route("/tags/<tag_id>/update_tags", methods=["GET", "POST"])
def update_tags(tag_id):
    tag = Tag.query.get(tag_id)
    form = forms.TagsForm(obj=tag)
    if form.validate_on_submit():
        tag.name = form.name.data
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("update_tags.html", form=form, form_name=tag.name)

@app.route("/tags/<tag_id>/delete_tags", methods=["POST"])
def delete_tags(tag_id):
    tag = Tag.query.get(tag_id)
    db.session.delete(tag)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/notes/create_note", methods=["GET", "POST"])
def create_note():
    form = forms.NoteForm()
    if form.validate_on_submit():
        note = Note()
        form.populate_obj(note)
        note.tags = [Tag.query.filter_by(name=tag_name).first() or Tag(name=tag_name) for tag_name in form.tags.data]
        db.session.add(note)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("create_note.html", form=form)

@app.route("/tags/<tag_id>/update_note", methods=["GET", "POST"])
def update_note(tag_id):
    note = Note.query.filter(Note.tags.any(id=tag_id)).first()
    form = forms.NoteForm(obj=note)
    if form.validate_on_submit():
        note.title = form.title.data
        note.description = form.description.data
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("update_note.html", form=form)

@app.route("/tags/<tag_id>/delete_note", methods=["POST"])
def delete_note(tag_id):
    note = Note.query.filter(Note.tags.any(id=tag_id)).first()
    if note:
        note.description = ""
        db.session.commit()
    return redirect(url_for("index"))

@app.route("/tags/<tag_id>/delete", methods=["POST"])
def delete(tag_id):
    note = Note.query.filter(Note.tags.any(id=tag_id)).first()
    if note:
        db.session.delete(note)
        db.session.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
