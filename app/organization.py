import functools
from aws import org_table, user_table,event_table
import jwt 
import hashlib
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv
import os
from auth import tokenRequired

load_dotenv()
SALT = os.environ["JWT_SALT_TWO"]

# Blueprints modularize code: define these routes
organization = Blueprint("organization", __name__)


@organization.get("/<string:orgName>")
def getOrganizationName(orgName):
    res = org_table.get_item(Key={"orgname":orgName})['Item']
    del res['password']
    return jsonify(res)
    

@organization.post("/")
def createOrganization():
    req = request.get_json()
    password_hashed = hashlib.pbkdf2_hmac(
        "sha256", req['password'].encode("utf-8"), b"SALT", 1000
    )
    tb = {"orgname": req['orgname'], "events": [],"subbed_users": [], "password": password_hashed}
    org_table.put_item(Item=tb)
    token = jwt.encode({"orgname": req['orgname']}, SALT, algorithm="HS256")
    return jsonify({"orgname": req['orgname'], "token": token})   

@organization.post("/login")
def orgLogin():
    req = request.get_json()
    password_hashed = hashlib.pbkdf2_hmac(
        "sha256", req['password'].encode("utf-8"), b"SALT", 1000
    )
    res = org_table.get_item(Key={"orgname": req['orgname']})
        
    if "Item" not in res:
        return jsonify({"message": f"User does not exist"}), 400
    else:
        res = res["Item"]
    
    # Check password
    if res['password'] != password_hashed:
        return jsonify({"message": f"User or password incorrect"}), 400

    token = jwt.encode({"orgname": res['orgname']}, SALT, algorithm="HS256")
    return jsonify({"orgname": req['orgname'], "events": res['events'], "subbed_users": res['subbed_users'],"token": token})   

def orgTokenRequired(f):
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
            current_user = org_table.get_item(Key={"orgname": data["orgname"]})
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

        return f(current_user["Item"]["orgname"], *args, **kwargs)

    return decorated

# sub to an organization from a user
@organization.post("/<string:orgname>")
@tokenRequired
def subToOrganization(username,orgname):
    org = org_table.get_item(Key={"orgname":orgname})
    if "Item" not in org:
        return jsonify({"msg": "Org does not exist"}), 404
    else:
        org = org['Item']
    user = user_table.get_item(Key={"username": username})['Item']
    org = org_table.get_item(Key={"orgname": orgname})['Item']
    user['subbed_orgs'].append(orgname)
    org['subbed_users'].append(username)
    print(org['subbed_users'])

    # TODO: get validation that user is not alrady subbed
    success = user_table.update_item(
            Key={"username": username},
            UpdateExpression="SET subbed_orgs=:new_orgs",
            ExpressionAttributeValues={":new_orgs": user['subbed_orgs']},
            ReturnValues="UPDATED_NEW",
    )
    success = org_table.update_item(
            Key={"orgname": orgname},
            UpdateExpression="SET subbed_users=:new_users",
            ExpressionAttributeValues={":new_users": org['subbed_users']},
            ReturnValues="UPDATED_NEW",
    )
    return jsonify({"msg":"SUCCESS"})


@organization.get("/dump")
def dumpOrganizationDatabase():
    def without(d, key):
        new_d = d.copy()
        new_d.pop(key)
        return new_d
    res = org_table.scan()['Items']
    res = [without(d,"password") for d in res]
    return res


@organization.get("/users")
@tokenRequired
def getOrganizationsByUser(username):
    req =user_table.get_item(Key={"username":username})['Item']
    return jsonify(req['subbed_orgs'])

# Get the event details given an event id
@organization.get("/event/<string:uid>")
@orgTokenRequired
def getID(orgname,uid):
    res = event_table.get_item(Key={"uid": uid})['Item']
    return res


