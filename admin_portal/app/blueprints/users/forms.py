from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class EndUserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    phone_number = StringField(
        "Phone Number", validators=[Optional(), Length(max=20)]
    )
    device_id = SelectField("Link Device", validators=[Optional()], choices=[])
    notes = TextAreaField("Notes", validators=[Optional()])
