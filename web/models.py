from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.hybrid import hybrid_property
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from acl import init_acl
import sqlalchemy as sa


class Base(DeclarativeBase):
    pass

bcrypt = Bcrypt()
db = SQLAlchemy(model_class=Base)








def init_app(app):
    db.init_app(app)
    bcrypt.init_app(app)
    init_acl(app)
    with app.app_context():
        db.create_all()
        db.reflect()


def has_role(self, role_name):
    return any(role.name == role_name for role in self.roles)

##right here
note_tag_m2m = db.Table(
                    "note_tag",
                    sa.Column("note_id", sa.ForeignKey("notes.id"), primary_key=True),
                    sa.Column("tag_id", sa.ForeignKey("tags.id"), primary_key=True),
                )


class Tag(db.Model):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_date = mapped_column(sa.DateTime(timezone=True), server_default=func.now())


class Note(db.Model):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)

    title: Mapped[str] = mapped_column(sa.String, nullable=False)
    description: Mapped[str] = mapped_column(sa.Text)
    tags: Mapped[list[Tag]] = relationship(secondary=note_tag_m2m)
    created_date = mapped_column(sa.DateTime(timezone=True), server_default=func.now())
    updated_date = mapped_column(sa.DateTime(timezone=True), server_default=func.now())

##right here
user_roles = db.Table(
    "user_roles",
    db.Model.metadata,
    sa.Column("user_id", sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("role_id", sa.ForeignKey("roles.id"), primary_key=True),
    )

class Role(db.Model):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String, nullable=False, default="user")
    created_date = mapped_column(sa.DateTime(timezone=True), server_default=func.now())


class User(db.Model, UserMixin):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    username = db.Column(db.String)
    status = db.Column(db.String, default="active")
    _password_hash = db.Column(db.String)
    created_date = mapped_column(sa.DateTime(timezone=True), server_default=func.now())
    updated_date = mapped_column(sa.DateTime(timezone=True), server_default=func.now())
    roles: Mapped[list[Role]] = relationship(secondary=user_roles)
    
    @hybrid_property
    # this will prevent our password_hash from being returned in a request
    # to users
    def password_hash(self):
        raise Exception("Password hashes may not be viewed.")

    @password_hash.setter
    def password_hash(self, password):
        password_hash = bcrypt.generate_password_hash(password.encode("utf-8"))
        self._password_hash = password_hash.decode("utf-8")

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password.encode("utf-8"))
        # this prevents that Exception being raised everytime we try to call the
        # .to_dict() method in a request that returns information from users


    serialize_rules = ("-_password_hash",)