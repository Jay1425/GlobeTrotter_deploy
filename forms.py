from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Log in")


class SignupForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(min=2, max=80)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[Optional(), Length(min=7, max=32)])
    city = StringField("City", validators=[Optional(), Length(max=120)])
    country = SelectField("Country", choices=[
        ("", "Select Country"),
        ("US", "United States"), ("CA", "Canada"), ("GB", "United Kingdom"),
        ("DE", "Germany"), ("FR", "France"), ("IT", "Italy"), ("ES", "Spain"),
        ("AU", "Australia"), ("JP", "Japan"), ("IN", "India"), ("BR", "Brazil"),
        ("MX", "Mexico"), ("NL", "Netherlands"), ("BE", "Belgium"), ("CH", "Switzerland"),
        ("SE", "Sweden"), ("NO", "Norway"), ("DK", "Denmark"), ("FI", "Finland"),
        ("SG", "Singapore"), ("HK", "Hong Kong"), ("NZ", "New Zealand"), ("ZA", "South Africa"),
        ("AE", "United Arab Emirates"), ("other", "Other")
    ], validators=[Optional()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match")])
    additionalInfo = TextAreaField("Additional Information", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Create account")
