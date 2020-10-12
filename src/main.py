"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os, threading
from flask import Flask, request, jsonify, url_for
from flask_jwt_simple import (
    JWTManager, jwt_required, create_jwt, get_jwt_identity
)
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Bet
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


# def periodic_check():
#     active_bets = Bet.query.filter_by(state = "enviado").all()
#     for bet in active_bets:
#         bet.check_date()
#     threading.Timer(1, periodic_check).start()

# periodic_check()

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


    jwt_identity = ""

    user = None

    if "email" in request_body: 
        jwt_identity = request_body["email"]
        user = User.query.filter_by(email=request_body["email"]).first()
    else:
        jwt_identity = request_body["username"]
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
                "result": "user not found"
            }), 404
                    
            
    return jsonify(ret), 200

@app.route('/user', methods=['GET'])
@jwt_required
def get_user():
    """ Verificar vigencia del token y poder utilizar su informacion """
    user = User.query.get(get_jwt_identity())

    if isinstance(user, User):
        return jsonify(user.serialize())
    else:
        return jsonify({
            "result": "user doesnt exist"
        }), 404
    

@app.route('/users', methods=['GET'])
def get_users():
    """ buscar y regresar todos los usuarios """
    users = User.query.all()
    users_serialize = list(map(lambda user: user.serializeUsers(), users))
    return jsonify(users_serialize), 200

@app.route('/bets', methods=['GET'])
def get_bets():
    """ buscar y regresar todos las apuestas """
    bets = Bet.query.all()
    bets_serialize = list(map(lambda bet: bet.serializeBets(), bets))
    return jsonify(bets_serialize), 200

@app.route('/user/<user_id>', methods=['GET'])
def get_user_id(user_id):
    """ buscar y regresar un usuario en especifico """
    user = User.query.get(user_id)
    if isinstance(user, User):
        return jsonify(user.serialize()), 200
    else:
        return jsonify({
            "result": "user not found"
        }), 404

@app.route('/bet/<bet_id>', methods=['GET', 'PATCH'])
def get_bet(bet_id):
    """ buscar y regresar un apuesta en especifico  """
    bet = Bet.query.get(bet_id)
    sender = User.query.get(bet.sender_id)
    receiver = User.query.get(bet.receiver_id)
    if isinstance(bet, Bet):
        if request.method == "GET":
            return jsonify(bet.serialize()), 200
        else:
            dictionary = request.json
            print(sender.ludos)
            print(bet.ludos)
            if(dictionary["state"] == "aceptado"):
                receiver.ludos -= bet.ludos
            
            if(dictionary["state"] == "rechazado"):
                sender.ludos += bet.ludos
            
            
            # if(
            #     dictionary["state"] == "enviado" or
            #     dictionary["state"] == "aceptado" or
            #     dictionary["state"] == "rechazado" or
            #     dictionary["state"] == "ganador" or
            #     dictionary["state"] == "empate" or
            #     dictionary["state"] == "desacuerdo"
            # ):
            bet.update_bet(dictionary)

            if(bet.winner_sender == bet.winner_receiver and bet.winner_sender != "" and bet.winner_sender != "empate"):
                bet.state = "ganador"
                bet.winner = bet.winner_sender
                winner = User.query.filter_by(username = bet.winner).first()
                winner.ludos += bet.ludos*2
            elif(bet.winner_sender == bet.winner_receiver and bet.winner_sender == "empate"):
                bet.state = "empate"
                bet.winner = "empate"
                sender.ludos += bet.ludos
                receiver.ludos += bet.ludos
            elif(bet.winner_sender != bet.winner_receiver and bet.winner_sender != "" and bet.winner_receiver != ""):
                bet.state = "desacuerdo"
                bet.winner = "desacuerdo"
                sender.ludos += bet.ludos
                receiver.ludos += bet.ludos
            
            try: 
                db.session.commit()
                return jsonify(bet.serialize()), 200
            except Exception as error:
                db.session.rollback()
                print(f"{error.args} {type(error)}")
                return jsonify({
                    "result": f"{error.args}"
                }), 500

            
            # if(bet.state == "ganador"):
            #     winner = User.query.filter_by(username=bet.).first()
            #     -= bet.ludos
            
            

            
    else:
        return jsonify({
            "result": "bet not found"
        }), 404


@app.route('/bet', methods=['POST'])
@jwt_required
def create_bet():
    """
        "POST": crear una apuesta y devolverla
    """
    body = request.json
    if body is None:
        return jsonify({
            "response": "empty body"
        }), 400

    if (
        "ludos" not in body or
        "name" not in body or
        "description" not in body or
        "due_date" not in body or
        "sender_id" not in body or
        "receiver_name" not in body
    ):
        return jsonify({
            "response": "Missing properties"
        }), 400
    if(
        body["ludos"] == "" or
        body["name"] == "" or
        body["description"] == "" or
        body["sender_id"] == "" or
        body["receiver_name"] == "" 
    ):
        return jsonify({
            "response": "empty property values"
        }), 400

    sender =  User.query.get(body["sender_id"])
    if(body["ludos"] > sender.ludos):
        return jsonify({
            "response": "not ludos enough"
        }), 400
    else:
        sender.ludos -= body["ludos"]

        receiver = User.query.filter_by(username=body["receiver_name"]).first()

    if body["sender_id"] == receiver.id:
        return jsonify({
            "response": "cant create bet with yourself"
        }), 400

    if isinstance(receiver, User):
        new_bet = Bet.create_bet(
            body["ludos"],
            body["name"],
            body["description"],
            body["due_date"],
            body["sender_id"],
            receiver.id
        )
        db.session.add(new_bet)
        try:
            db.session.commit()
            return jsonify(new_bet.serialize()), 201
        except Exception as error:
            db.session.rollback()
            print(f"{error.args} {type(error)}")
            return jsonify({
                "response": f"{error.args}"
            }), 500
    else:
        return jsonify({
            "response": "user not found"
        }), 404

@app.route("/check", methods=["GET"])
def check_bets():
    active_bets = Bet.query.filter_by(state = "enviado").all()
    for bet in active_bets:
        bet.check_date()

    return jsonify({"response":"bets checked"}), 200
    


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)




