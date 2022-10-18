import functools
import hashlib
import jwt

from aws import user_table
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv
import os

load_dotenv()
SALT = os.environ["JWT_SALT"]

# Blueprints modularize code: define these routes
auth = Blueprint("auth", __name__)

@auth.get("/")
def defaults():
    return "no"


@auth.route("/register", methods=["POST"])
def signup():
    """Creates a user"""
    req = request.get_json()
    email, password, username = req["email"], req["password"], req["username"]
    password_hashed = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), b"SALT", 1000
    )

    # Check if user exists
    res = user_table.get_item(Key={"username": username})
    if "Item" in res:
        return (
            jsonify({"message": f"User with username {username} already exists"}),
            400,
        )

    # Create user based on hashed password
    user = {
        "username": username,
        "email": email,
        "password": password_hashed,
        "profile_pic": ":)",
        "subbed_events": [],
        "subbed_orgs": []
    }
    user_table.put_item(Item=user)

    # Create token and return
    token = jwt.encode({"username": username, "email": email}, SALT, algorithm="HS256")
    return jsonify({"username": username, "email": email, "token": token})


def tokenRequired(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            # Make sure headers are valid
            if len(request.headers["authorization"].split(" ")) < 2:
                return {
                    "message": "Invalid Authentication!",
                    "data": None,
                    "error": "Unauthorized",
                }, 401
            token = request.headers["Authorization"].split(" ")[1]
        if not token:
            return {
                "message": "Authentication Token is missing!",
                "data": None,
                "error": "Unauthorized",
            }, 401
        try:
            data = jwt.decode(token, SALT, algorithms=["HS256"])
            current_user = user_table.get_item(Key={"username": data["username"]})
            if current_user is None:
                return {
                    "message": "Invalid Authentication token!",
                    "data": None,
                    "error": "Unauthorized",
                }, 401
        except Exception as e:
            return {
                "message": "Something went wrong",
                "data": None,
                "error": str(e),
            }, 500

        return f(current_user["Item"]["username"], *args, **kwargs)

    return decorated


# add session token to check if someone is logged in
@auth.route("/login", methods=["POST"])
def login():
    """Creates a user"""
    req = request.get_json()
    username, password = req["username"], req["password"]
    password_hashed = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), b"SALT", 1000
    )

    # Check if user exists
    res = user_table.get_item(Key={"username": username})
    if "Item" not in res:
        return jsonify({"message": f"User does not exist"}), 400
    else:
        res = res["Item"]

    # Check Password
    email = res["email"]
    password_check = res["password"]
    subbed_events = res["subbed_events"]
    subbed_orgs = res["subbed_orgs"]
    profile_pic = res["profile_pic"]

    if password_check != password_hashed:
        return jsonify({"message": f"Incorrect Password"}), 400

    # Create token and return
    token = jwt.encode({"username": username, "email": email}, SALT, algorithm="HS256")
    return jsonify({"username": username, "email": email, "token": token, "profile_pic" : profile_pic, "subbed_events" : subbed_events, "subbed_orgs" : subbed_orgs})


@auth.get("/protected")
@tokenRequired
def protected(username):
    return user_table.get_item(Key={"username":username})['Item']['subbed_orgs']