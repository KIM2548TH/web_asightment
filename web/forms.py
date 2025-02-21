from wtforms_sqlalchemy.orm import model_form
from flask_wtf import FlaskForm
from wtforms import Field, widgets, validators, fields
from flask_wtf.file import FileAllowed
import models
            


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


class Province_Form(FlaskForm):
    name = fields.StringField("Province Name", [validators.DataRequired()])
    region = fields.SelectField("Region", choices=[
        ('เหนือ', 'เหนือ'),
        ('กลาง', 'กลาง'),
        ('อีสาน', 'อีสาน'),
        ('ใต้', 'ใต้')
    ], validators=[validators.DataRequired()])
    image_file = fields.FileField("Image File", validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Only image files are allowed')
    ])

class Cost_of_Living_Form(FlaskForm):
    province_name = fields.SelectField("Province", coerce=str, validators=[validators.DataRequired()])
    year = fields.SelectField("Year", coerce=int, validators=[validators.DataRequired()])
    food = fields.FloatField("Food Cost", [validators.DataRequired()])
    housing = fields.FloatField("Housing Cost", [validators.DataRequired()])
    energy = fields.FloatField("Energy Cost", [validators.DataRequired()])
    transportation = fields.FloatField("Transportation Cost", [validators.DataRequired()])
    entertainment = fields.FloatField("Entertainment Cost", [validators.DataRequired()])
