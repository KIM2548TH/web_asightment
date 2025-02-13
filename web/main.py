import flask
import models
import forms
import acl as acl

from flask import (
    Blueprint,
)

from flask_login import login_required, login_user, logout_user
module = Blueprint("templates", __name__)

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()

    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/detail")
def detail():
    return flask.render_template("detail.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = forms.LoginForm()
    if not form.validate_on_submit():
        return flask.render_template(
            "login.html",
            form=form,
        )

    user = models.User.query.filter_by(username=form.username.data).first()

    if user and user.authenticate(form.password.data):
        login_user(user)
        return flask.redirect(flask.url_for("index"))

    return flask.redirect(flask.url_for("login", error="Invalid username or password"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return flask.redirect(flask.url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = forms.RegisterForm()
    if not form.validate_on_submit():
        return flask.render_template(
            "register.html",
            form=form,
        )
    user = models.User()  # Initialize the user here
    form.populate_obj(user)  # Populate the user object with form data

    role = models.Role.query.filter_by(name="user").first()
    if not role:  # Create the 'user' role if it doesn't exist
        role = models.Role(name="user")
        models.db.session.add(role)

    user.roles.append(role)
    user.password_hash = form.password.data
    models.db.session.add(user)
    models.db.session.commit()
    return flask.redirect(flask.url_for("login"))


@app.route("/page")
@acl.roles_required("admin")
def page():
    return flask.render_template("page.html")


@app.route("/page2")
@login_required
def page2():
    return flask.render_template("page_2.html")


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()
    return flask.render_template(
        "tags_view.html",
        tag_name=tag_name,
        notes=notes,
    )


@app.route("/tags/<tag_id>/update_tags", methods=["GET", "POST"])
def update_tags(tag_id):  # แกไข Tags ได
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.id == tag_id))
        .scalars()
        .first()
    )
    form = forms.TagsForm()
    form_name = tag.name

    if not form.validate_on_submit():
        print(form.errors)
        return flask.render_template("update_tags.html", form=form, form_name=form_name)

    note = models.Note(id=tag_id)
    form.populate_obj(note)
    tag.name = form.name.data
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_id>/delete_tags", methods=["GET", "POST"])
def delete_tags(tag_id):  # ลบ Tags ไดอยางเดียว
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.id == tag_id))
        .scalars()
        .first()
    )
    tag.name = ""
    db.session.commit()
    return flask.redirect(flask.url_for("index"))


@app.route("/notes/create_note", methods=["GET", "POST"])
def create_note():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "create_note.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_id>/update_note", methods=["GET", "POST"])
def update_note(tag_id):  # แกไข Note และสามารถเปลี่ยนชื่อ Title ได
    db = models.db
    notes = (
        db.session.execute(
            db.select(models.Note).where(models.Note.tags.any(id=tag_id))
        )
        .scalars()
        .first()
    )

    form = forms.NoteForm()
    form_title = notes.title
    form_description = notes.description
    if not form.validate_on_submit():
        print(form.errors)
        return flask.render_template(
            "update_note.html",
            form=form,
            form_title=form_title,
            form_description=form_description,
        )

    note = models.Note(id=tag_id)
    form.populate_obj(note)
    notes.description = form.description.data
    notes.title = form.title.data
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_id>/delete_note", methods=["GET", "POST"])
def delete_note(tag_id):  # ลบ Note เพียงอยางเดียวไมไดลบ Title
    db = models.db
    notes = (
        db.session.execute(
            db.select(models.Note).where(models.Note.tags.any(id=tag_id))
        )
        .scalars()
        .first()
    )
    notes.description = ""
    db.session.commit()
    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_id>/delete", methods=["GET", "POST"])
def delete(tag_id):  # ลบทั้งหมดที่เกี่ยวกับ Tags
    db = models.db
    notes = (
        db.session.execute(
            db.select(models.Note).where(models.Note.tags.any(id=tag_id))
        )
        .scalars()
        .first()
    )

    db.session.delete(notes)
    db.session.commit()
    return flask.redirect(flask.url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)