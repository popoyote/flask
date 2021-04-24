from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class ProductsForm(FlaskForm):
    title = StringField('Название товара', validators=[DataRequired()])
    content = TextAreaField("Описание")
    price = IntegerField("Цена")
    submit = SubmitField('Применить')
