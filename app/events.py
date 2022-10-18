import uuid
from aws import event_table, org_table, user_table
from auth import tokenRequired;
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv
from organization import orgTokenRequired
import os

load_dotenv()
SALT = os.environ["JWT_SALT"]

# Blueprints modularize code: define these routes
events = Blueprint("events", __name__)

# Get all events hosted by an organization
@events.get("/org/<string:org>")
def getOrganization(org):
    print(org)
    res = org_table.get_item(Key={"orgname":org})['Item']

    # inefficient scan, but wtf it works anyways
    response = event_table.scan(
    ScanFilter={'uid': {
        'AttributeValueList': res['events'],
        'ComparisonOperator': 'IN' }
    }
)

    return jsonify({"events":response['Items']})
    
# Get the event details given an event id
@events.get("/id/<string:uid>")
@tokenRequired
def getID(username,uid):
    res = event_table.get_item(Key={"uid": uid})['Item']
    return res

# get the subbed events for a user
@events.get("/user")
@tokenRequired
def getEventsFromUser(username):
    res = user_table.get_item(Key={"username":username})['Item']
    subbed_events = res['subbed_events']
    response = event_table.scan(
    ScanFilter={'uid': {
        'AttributeValueList': subbed_events,
        'ComparisonOperator': 'IN' }
    }
    )
    print(response)
    return jsonify({"subbed_events":response['Items']})

# Create an event
@events.post("/")
@orgTokenRequired
def createEvent(organization):
    req = request.get_json()
    uid = uuid.uuid4() 
    org = org_table.get_item(Key={"orgname":organization})
    if "Item" not in org:
        return jsonify({"msg": "Organization does not exist"})
    else:
        org = org['Item']
    org['events'].append(str(uid))

    success = org_table.update_item(
            Key={"orgname": organization},
            UpdateExpression="SET events=:new_events",
            ExpressionAttributeValues={":new_events": org['events']},
            ReturnValues="UPDATED_NEW",
    )

    event = {
        "location": f"{req['lat']},{req['lon']}",
        "time_start": int(req['time_start']),
        "time_end": int(req['time_end']),
        "description": req['description'],
        "name": req['name'],
        "organization": organization,
        "users_checked": [],
        "uid": str(uid),
        "radius": req['radius'] # Radius in meters
    }

    event_table.put_item(Item=event)
    return event

# sub to an event for a user
@events.post("/sub/<string:id>")
@tokenRequired
def getEventSubList(username, id):
    res = user_table.get_item(Key={"username": username})
    if "Item" not in res:
        return jsonify({"msg": "Event does not exist"})
    else:
        res = res['Item']
    del res['password']

    email = res["email"]
    subbed_events = res["subbed_events"]
    if id not in subbed_events:
        subbed_events.append(id)
    else:
        return "Event has already been added" 
    subbed_orgs = res["subbed_orgs"]
    profile_pic = res["profile_pic"]

    success = user_table.update_item(
            Key={"username": username},
            UpdateExpression="SET subbed_events=:new_subbed_events",
            ExpressionAttributeValues={":new_subbed_events": subbed_events},
            ReturnValues="UPDATED_NEW",
    )

    return jsonify({"username": username, "email": email, "profile_pic" : profile_pic, "subbed_events": subbed_events, "subbed_orgs" : subbed_orgs})

# check in the user by adding to the to the event user_checked list
@events.post("/checkin/<string:id>")
@tokenRequired
def checkinUser(username, id):
    res = event_table.get_item(Key={"uid": id})
    # return jsonify(res)
    res = res['Item']
    location = res["location"]
    time_start = res["time_start"]
    description = res["description"]
    organization = res["organization"]
    users_checked = res["users_checked"]
    time_end = res["time_end"]

    if username not in users_checked:
        users_checked.append(username)
    else:
        return jsonify({"msg":"User has already been checked in"}), 202

    success = event_table.update_item(
            Key={"uid": id},
            UpdateExpression="SET users_checked=:new_users_checked",
            ExpressionAttributeValues={":new_users_checked": users_checked},
            ReturnValues="UPDATED_NEW",
    )

    return jsonify({"location": location, "time_start": time_start, "description" : description, "organization": organization, "users_checked" : users_checked, "time_end" : time_end})


@events.delete("/<string:id>")
def deleteEvent():
    pass

@events.get("/dump")
def dumpEventDatabase():
    res = event_table.scan()['Items']
    return res
