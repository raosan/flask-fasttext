from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    return 'Index Page'

@app.route('/hello')
def hello():
    return 'Hello, World'

@app.route('/projects/')
def projects():
    return 'The project page'

@app.route('/about')
def about():
    return 'The about page'

@app.route("/me")
def me_api():
    return {
        "username": "user.username",
        "theme": "user.theme",
        "image": "image url",
    }

@app.route('/vector')
def run_vector():
    var = 'lala'
    return var