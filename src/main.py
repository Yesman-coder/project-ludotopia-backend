"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/register', methods=['POST'])
def post_user():
    """
        "POST": registrar un usuario y devolverlo
    """
    body = request.json
    if body is None:
        return jsonify({
            "response": "empty body"
        }), 400
    if (
        "email" not in body or
        "name" not in body or
        "last_name" not in body or
        "phone" not in body or
        "username" not in body or
        "password" not in body or
    ):
        return jsonify({
            "response": "Missing properties"
        }), 400
    if(
        body["email"] == "" or
        body["name"] == "" or
        body["last_name"] == "" or
        body["username"] == "" or
        body["password"] == ""
    ):
        return jsonify({
            "response": "empty property values"
        }), 400

    new_user = User.register(
        body["email"],
        body["name"],
        body["last_name"],
        body["phone"],
        body["ludos"],
        body["username"],
        body["password"],
        body["status"]
    )
    db.session.add(new_user)
    try:
        db.session.commit()
        return jsonify(new_user.serialize()), 201
    except Exception as error:
        db.session.rollback()
        print(f"{error.args} {type(error)}")
        return jsonify({
            "response": f"{error.args}"
        }), 500


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
