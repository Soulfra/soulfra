from flask import Blueprint, render_template

blueprint = Blueprint('hello_world', __name__,
                     url_prefix='/hello',
                     template_folder='templates')

@blueprint.route('/')
def index():
    return render_template('hello_world/index.html')
