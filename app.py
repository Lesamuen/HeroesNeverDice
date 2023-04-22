from flask import Flask
import database as db

# Initialize Flask app
app = Flask(__name__, template_folder = 'templates', static_folder = 'static')
app.secret_key = '0v5hY7S4Ki'

if __name__ == '__main__':
    db.init(app)
    app.run()
