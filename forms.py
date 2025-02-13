from wtforms_sqlalchemy.orm import model_form
from flask_wtf import FlaskForm
from wtforms import Field, widgets, validators, fields

import models

class TagListField(Field):
    widget = widgets.TextInput()

    def __init__(self, label="", validators=None, remove_duplicates=True, **kwargs):
        super().__init__(label, validators, **kwargs)
        self.remove_duplicates = remove_duplicates
        self.data = []

    def process_formdata(self, valuelist):
        data = []

        if valuelist:
            data = [x.strip() for x in valuelist[0].split(",")]
        if not self.remove_duplicates:
            self.data = data
            return
        
        self.data = []
        for d in data:
            if d not in self.data:
                self.data.append(d)
                
    def _value(self):
        if self.data:
            return ", ".join(self.data)
        else:
            return ""
            

BaseNoteForm = model_form(
    models.Note, base_class=FlaskForm, exclude=["created_date", "updated_date"],
    db_session=models.db.session
)

BaseTagsForm = model_form(
    models.Tag ,base_class=FlaskForm, exclude=["created_date", "updated_date"],
    db_session=models.db.session
)

BaseUserForm = model_form(
    models.User,
    base_class=FlaskForm,
    exclude=["created_date", "updated_date", "status", "_password_hash"],
    db_session=models.db.session,
)

class LoginForm(FlaskForm):
    username = fields.StringField("username", [validators.DataRequired()])
    password = fields.PasswordField("password", [validators.DataRequired()])

class RegisterForm(BaseUserForm):
    username = fields.StringField(
    "username", [validators.DataRequired(), validators.length(min=6)]
    )
    password = fields.PasswordField(
    "password", [validators.DataRequired(), validators.length(min=6)]
    )
    name = fields.StringField(
    "name", [validators.DataRequired(), validators.length(min=6)]
    )

class NoteForm(BaseNoteForm):
    tags = TagListField("Tag")

    
class TagsForm(BaseTagsForm):
    tags = TagListField("Tag")


