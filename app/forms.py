from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired

class ImageGenerationForm(FlaskForm):
    positive_prompt = TextAreaField('Positive Prompt', validators=[DataRequired()])
    negative_prompt = TextAreaField('Negative Prompt')
    submit = SubmitField('Generate Image')

class ImageToImageForm(FlaskForm):
    input_image = FileField('Input Image', validators=[DataRequired()])
    positive_prompt = TextAreaField('Positive Prompt', validators=[DataRequired()])
    negative_prompt = TextAreaField('Negative Prompt')
    submit = SubmitField('Generate Image')