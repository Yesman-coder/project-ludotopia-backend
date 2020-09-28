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
from flask_jwt_simple import (
    JWTManager, jwt_required, create_jwt, get_jwt_identity
)
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get("APP_JWT_SECRET")
MIGRATE = Migrate(app, db)
db.init_app(app)
jwt = JWTManager(app)
CORS(app)
setup_admin(app)

jwt = JWTManager(app)


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
        "password" not in body 
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
        body["username"],
        body["password"],
        
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



@app.route("/login", methods=["POST"])
def handle_login():
    """ Compara El usuario/correo con la base de datos y genera un token si hay match """

    request_body = request.json

    if request_body is None:
        return jsonify({
            "result" : "missing request body"

        }), 400

    if (
        ("email" not in request_body and "username" not in request_body ) or
        "password" not in request_body
    ):
        return jsonify({
            "result": "missing fields in request body"
        }), 400


    

    user = None

    if "email" in request_body: 
        
        user = User.query.filter_by(email=request_body["email"]).first()
    else:
      
        user = User.query.filter_by(username=request_body["username"]).first()


    ret = None

    if isinstance(user, User):
        if (user.check_password(request_body["password"])):
            jwt = create_jwt(identity = user.id)
            ret = user.serialize()
            ret["jwt"] = jwt
        else: 
            return jsonify({
                "result": "invalid data"
            }), 400
    else:
        return jsonify({
            "result": "not found"
        }), 404
                    
            
    return jsonify(ret), 200

@app.route('/user', methods=['GET'])
@jwt_required
def get_user(user_id):
    """ Verificar vigencia del token y poder utilizar su informacion """
    user = User.query.get(get_jwt_identity())
    if isinstance(user, User):
        return jsonify(user.serialize()), 200
    else:
        return jsonify({
            "result": "user doesnt exist"
        }), 404


    

    


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
