from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Optional

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    submit = SubmitField("LOG IN", render_kw={"class": "btn btn-primary w-100 rounded-pill fw-bold"})

class RegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    dota2_username = StringField("DOTA 2 Username", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    steam_id = StringField("Steam ID", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    submit = SubmitField("Create Account", render_kw={"class": "btn btn-primary w-100 rounded-pill fw-bold"}) # [cite: 710]

class ProductForm(FlaskForm):
    name = StringField("Enter Product Name", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    price = FloatField("Set Price", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    # Changed from DataRequired() to Optional()
    image_url = StringField("Add Image URL", validators=[Optional()], render_kw={"class": "form-control bg-dark text-light border-secondary", "placeholder": "https://..."}) 
    rarity = SelectField("Set Product Rarity", choices=[('Arcana', 'Arcana'), ('Immortal', 'Immortal'), ('Mythical', 'Mythical'), ('Rare', 'Rare')], render_kw={"class": "form-select bg-dark text-light border-secondary"})
    status = SelectField("Tradeable or Giftable?", choices=[('Tradeable', 'Tradeable'), ('Giftable', 'Giftable')], render_kw={"class": "form-select bg-dark text-light border-secondary"})
    quantity = IntegerField("Qty in Stock", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    description = TextAreaField("Add Product Description", render_kw={"class": "form-control bg-dark text-light border-secondary", "rows": 4})
    submit = SubmitField("Add product listing", render_kw={"class": "btn btn-success w-100 rounded-pill fw-bold"})

class EditProfileForm(FlaskForm):
    dota2_username = StringField("DOTA 2 Username", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    steam_id = StringField("Steam ID", validators=[DataRequired()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    email = StringField("Email", validators=[DataRequired(), Email()], render_kw={"class": "form-control bg-dark text-light border-secondary"})
    submit = SubmitField("Save Changes", render_kw={"class": "btn btn-primary w-100 rounded-pill fw-bold"})