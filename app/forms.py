from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional, ValidationError

# List of checkpoints with a tuple structure: (value, label, is_favorite)
CHECKPOINTS = [
    ('SD15/absolutereality_v181.safetensors', 'Absolute Reality v1.8.1', False),
    ('SD15/cyberrealistic_classicV31.safetensors', 'Cyberrealistic Classic V31', True),
    ('SD15/deliberate_v2.safetensors', 'Deliberate v2', False),
    ('SD15/dreamshaper_8.safetensors', 'Dreamshaper 8', False),
    ('SD15/Experience_v10-FP16.safetensors', 'Experience v10 FP16', False),
    ('SD15/Inkpunk-Diffusion-v2.ckpt', 'Inkpunk Diffusion v2', False),
    ('SD15/leosamsFilmgirlUltra_ultraBaseModel.safetensors', 'LEOSAM Filmgirl Ultra Base Model', False),
    ('SD15/mcbsMachinecodesComic_v2.safetensors', 'MCBS Machinecodes Comic v2', False),
    ('SD15/revAnimated_v121.safetensors', 'Rev Animated v1.2.1', False),
    ('SD15/Swizz8-REAL-BakedVAE-FP16.safetensors', 'Swizz8 REAL BakedVAE FP16', True),
    ('SD15/tfmAmericanCartoons_genesis.safetensors', 'TFM American Cartoons Genesis', False),
    ('SDXL/afroditexl_11Bkdvae.safetensors', 'Afrodite XL 11B KD VAE', False),
    ('SDXL/AnythingXL_xl.safetensors', 'Anything XL', False),
    ('SDXL/cartoonArcadiaSDXLSD1_v2.safetensors', 'Cartoon Arcadia SDXL SD1 v2', False),
    ('SDXL/counterfeitxl_v25.safetensors', 'Counterfeit XL v2.5', False),
    ('SDXL/dynavisionXLAllInOneStylized_release0557Bakedvae.safetensors', 'Dynavision XL All In One Stylized 0557 Baked VAE', False),
    ('SDXL/halcyonSDXL_v17.safetensors', 'Halcyon SDXL v1.7', False),
    ('SDXL/icbinpXL_v3.safetensors', 'ICBINP XL v3', False),
    ('SDXL/jibMixRealisticXL_v90BetterBodies.safetensors', 'JIB Mix Realistic XL v90 Better Bodies', True),
    ('SDXL/juggernautXL_version5.safetensors', 'Juggernaut XL v5', True),
    ('SDXL/Juggernaut_X_RunDiffusion.safetensors', 'Juggernaut X RunDiffusion', False),
    ('SDXL/leosamsHelloworldXL_helloworldXL70.safetensors', 'Leosams Hello World XL 70', True),
    ('SDXL/RealitiesEdgeXLSDXL_V7Bakedvae.safetensors', 'Realities Edge XL SDXL V7 Baked VAE', False),
    ('SDXL/sdxlUnstableDiffusers_v11Rundiffusion.safetensors', 'SDXL Unstable Diffusers v11 Rundiffusion', False),
    ('SDXL/sdxlYamersRealisticNSFW_v5SX.safetensors', 'SDXL Yamers Realistic NSFW v5SX', False),
    ('SDXL/suzannesXLMix_v60.safetensors', 'Suzanne\'s XL Mix v60', True),
]


class ImageGenerationForm(FlaskForm):
    positive_prompt = TextAreaField('Positive Prompt', validators=[DataRequired()])
    negative_prompt = TextAreaField('Negative Prompt')

    # Node #3 parameters
    steps = IntegerField('Steps', validators=[NumberRange(min=1, max=150)], default=20)
    cfg = FloatField('CFG Scale', validators=[NumberRange(min=1, max=30)], default=8)
    sampler_name = SelectField('Sampler', choices=[
        ('euler', 'Euler'),
        ('euler_ancestral', 'Euler Ancestral'),
        ('heun', 'Heun'),
        ('heunpp2', 'Heun++2'),
        ('dpm_2', 'DPM 2'),
        ('dpm_2_ancestral', 'DPM 2 Ancestral'),
        ('lms', 'LMS'),
        ('dpm_fast', 'DPM Fast'),
        ('dpm_adaptive', 'DPM Adaptive'),
        ('dpmpp_2s_ancestral', 'DPM++ 2S Ancestral'),
        ('dpmpp_sde', 'DPM++ SDE'),
        ('dpmpp_sde_gpu', 'DPM++ SDE GPU'),
        ('dpmpp_2m', 'DPM++ 2M'),
        ('dpmpp_2m_sde', 'DPM++ 2M SDE'),
        ('dpmpp_2m_sde_gpu', 'DPM++ 2M SDE GPU'),
        ('dpmpp_3m_sde', 'DPM++ 3M SDE'),
        ('dpmpp_3m_sde_gpu', 'DPM++ 3M SDE GPU'),
        ('ddpm', 'DDPM'),
        ('lcm', 'LCM'),
        ('ddim', 'DDIM'),
        ('uni_pc', 'UniPC'),
        ('uni_pc_bh2', 'UniPC BH2')
    ], default='euler')
    scheduler = SelectField('Scheduler', choices=[
        ('normal', 'Normal'),
        ('karras', 'Karras'),
        ('exponential', 'Exponential'),
        ('sgm_uniform', 'SGM Uniform'),
        ('simple', 'Simple'),
        ('ddim_uniform', 'DDIM Uniform')
    ], default='normal')
    denoise = FloatField('Denoise', validators=[NumberRange(min=0, max=1)], default=1)

    # Node #4 parameter
    ckpt_name = SelectField('Checkpoint', choices=[
                                                      (value, label) for value, label, is_favorite in CHECKPOINTS if
                                                      is_favorite
                                                  ] + [('', '--- Other Checkpoints ---')] + [
                                                      (value, label) for value, label, is_favorite in CHECKPOINTS if
                                                      not is_favorite
                                                  ])

    # Node #5 parameters
    width = IntegerField('Width', validators=[NumberRange(min=64, max=2048)], default=512)
    height = IntegerField('Height', validators=[NumberRange(min=64, max=2048)], default=512)
    batch_size = IntegerField('Batch Size', validators=[NumberRange(min=1, max=4)], default=1)

    submit = SubmitField('Generate Image')


def validate_seed(form, field):
    if field.data != '-1' and not field.data.isdigit():
        raise ValidationError('Seed must be -1 or a positive integer')


class ImageToImageForm(FlaskForm):
    input_image = FileField('Input Image', validators=[
        FileRequired(),
        FileAllowed(['png', 'jpg', 'jpeg'], 'Images only!')
    ])
    positive_prompt = TextAreaField('Positive Prompt', validators=[DataRequired()])
    negative_prompt = TextAreaField('Negative Prompt')

    # Node #3 parameters
    # Change seed to StringField
    seed = StringField('Seed', validators=[Optional(), validate_seed], default='-1')
    steps = IntegerField('Steps', validators=[NumberRange(min=1, max=150)], default=20)
    cfg = FloatField('CFG Scale', validators=[NumberRange(min=1, max=30)], default=8)
    sampler_name = SelectField('Sampler', choices=[
        ('euler', 'Euler'),
        ('euler_ancestral', 'Euler Ancestral'),
        ('heun', 'Heun'),
        ('heunpp2', 'Heun++2'),
        ('dpm_2', 'DPM 2'),
        ('dpm_2_ancestral', 'DPM 2 Ancestral'),
        ('lms', 'LMS'),
        ('dpm_fast', 'DPM Fast'),
        ('dpm_adaptive', 'DPM Adaptive'),
        ('dpmpp_2s_ancestral', 'DPM++ 2S Ancestral'),
        ('dpmpp_sde', 'DPM++ SDE'),
        ('dpmpp_sde_gpu', 'DPM++ SDE GPU'),
        ('dpmpp_2m', 'DPM++ 2M'),
        ('dpmpp_2m_sde', 'DPM++ 2M SDE'),
        ('dpmpp_2m_sde_gpu', 'DPM++ 2M SDE GPU'),
        ('dpmpp_3m_sde', 'DPM++ 3M SDE'),
        ('dpmpp_3m_sde_gpu', 'DPM++ 3M SDE GPU'),
        ('ddpm', 'DDPM'),
        ('lcm', 'LCM'),
        ('ddim', 'DDIM'),
        ('uni_pc', 'UniPC'),
        ('uni_pc_bh2', 'UniPC BH2')
    ], default='euler_ancestral')
    scheduler = SelectField('Scheduler', choices=[
        ('normal', 'Normal'),
        ('karras', 'Karras'),
        ('exponential', 'Exponential'),
        ('sgm_uniform', 'SGM Uniform'),
        ('simple', 'Simple'),
        ('ddim_uniform', 'DDIM Uniform')
    ], default='karras')
    denoise = FloatField('Denoise', validators=[NumberRange(min=0, max=1)], default=0.8)

    # Node #4 parameter
    ckpt_name = SelectField('Checkpoint', choices=[
                                                      (value, label) for value, label, is_favorite in CHECKPOINTS if
                                                      is_favorite
                                                  ] + [('', '--- Other Checkpoints ---')] + [
                                                      (value, label) for value, label, is_favorite in CHECKPOINTS if
                                                      not is_favorite
                                                  ])

    submit = SubmitField('Generate Image')