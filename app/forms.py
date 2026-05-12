from flask_wtf import FlaskForm
# NEW: Import file handling fields
from flask_wtf.file import MultipleFileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, FloatField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Optional

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    submit = SubmitField("LOG IN", render_kw={"class": "btn btn-primary w-100 rounded-pill fw-bold"})

class RegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()], render_kw={"class": "form-control bg-dark text-light border-secondary"}) 
    dota2_username = StringField("Dota 2 Username", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    steam_id = StringField("Steam ID", validators=[Optional()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"}) 
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')], render_kw={"class": "form-control bg-dark text-light border-secondary"}) 
    submit = SubmitField("Register Account", render_kw={"class": "btn btn-primary w-100 rounded-pill fw-bold"}) #

class ProductForm(FlaskForm):
    name = StringField("Product Name", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"}) 
    price = FloatField("Price", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    # NEW: Field for multiple image uploads, replacing the old image_url field
    images = MultipleFileField("Upload Images (Optional)", validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only image files are allowed!')
    ], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    rarity = SelectField("Rarity", choices=[('Arcana', 'Arcana'), ('Immortal', 'Immortal'), ('Mythical', 'Mythical'), ('Rare', 'Rare')], render_kw={"class": "form-select bg-dark text-light border-secondary"}) 
    status = SelectField("Trade Status", choices=[('Tradeable', 'Tradeable'), ('Giftable', 'Giftable')], render_kw={"class": "form-select bg-dark text-light border-secondary"}) 
    quantity = IntegerField("Quantity in Stock", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"}) 
    description = TextAreaField("Product Description", render_kw={"class": "form-control bg-dark text-light border-secondary", "rows": 4}) 
    submit = SubmitField("Create Listing", render_kw={"class": "btn btn-success w-100 rounded-pill fw-bold"})

class EditProfileForm(FlaskForm):
    dota2_username = StringField("Dota 2 Username", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    steam_id = StringField("Steam ID", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    email = StringField("Email", validators=[DataRequired(), Email()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    current_password = PasswordField("Current Password", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    submit = SubmitField("Save Changes", render_kw={"class": "btn btn-primary w-100 rounded-pill fw-bold"})

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    new_password = PasswordField("New Password", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    confirm_new_password = PasswordField("Confirm New Password", validators=[DataRequired(), EqualTo('new_password')], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    submit = SubmitField("Change Password", render_kw={"class": "btn btn-primary w-100 rounded-pill fw-bold"})