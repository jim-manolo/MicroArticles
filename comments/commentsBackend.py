#Comments BackEnd
from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson.objectid import ObjectId
from authClient import AuthClient
import pprint

clientDB = MongoClient('mongodb://192.168.99.100:27017')
db = clientDB["comments"]
comments = db["comments-collection"]
app = Flask(__name__)
authClient = AuthClient(host="192.168.99.100")

@app.route("/articles/<articleID>/comments", methods=["GET"])
def listComments(articleID):
    commentList = comments.find({"articleID":ObjectId(articleID)})
    resultList = []
    for comment in commentList:
        resultList.append({
            "body": comment["body"],
            "get":"/articles/{}/comments/{}".format(articleID, str(comment["_id"])),
            "owner": comment["owner"]
        })
    return getResponseList(200, resultList)

@app.route("/articles/<articleID>/comments", methods=["POST"])
def createComment(articleID):
    params = request.get_json()
    if params is None:
        return getResponse(400,message="Request body must be json type")
    errFlag = False
    errMsg = ""
    if not "body" in params:
        errFlag = True
        errMsg += "Missing field body"
    if not "token" in params:
        errFlag = True
        errMsg += "Missing field token"
    if not "userID" in params:
        errFlag = True
        errMsg += "Missing field userID"
    if errFlag:
        return getResponse(400, message=errMsg)

    if not authClient.isTokenValid(token=params["token"],userID=params["userID"]):
      return getResponse(403, message="Access Denied!!")

    newComment = {
        "body": params["body"],
        "articleID": ObjectId(articleID),
        "owner": params["userID"]
    }
    commentID = comments.insert_one(newComment).inserted_id

    return getResponse(
        201,
        get="/articles/{}/comments/{}".format(articleID, str(commentID)),
        id=commentID
    )



@app.route("/articles/<articleID>/comments/<commentID>", methods=["PUT"])
def updateComment(articleID, commentID):
    params = request.get_json()
    if params is None:
        return getResponse(400,message="Request body must be json type")

    if not "token" in params:
        return getResponse(400, message="Missing token!")

    comment = comments.find_one({'_id': ObjectId(commentID)})
    if comment is None:
        return getResponse(404,message="Comment id {} isn't found".format(commentID))
    if not authClient.isTokenValid(token=params["token"], userID=comment["owner"]):
        return getResponse(403, message="Access Denied!!")

    updateObj = {}
    if "body" in params:
        updateObj["body"] = params["body"]
    comments.update({'_id': ObjectId(commentID)},{"$set":updateObj})
    return getResponse(
        200,
        get="/articles/{}/comments/{}".format(articleID, str(commentID))
    )


def getResponseList(status, aList):
    if aList is None:
        aList = []
    resp = jsonify(aList)
    resp.status_code = status
    return resp

def getResponse(status, **kwargs):
    obj = {}
    if kwargs is not None:
        obj = kwargs
    resp = jsonify(obj)
    resp.status_code = status
    return resp 

if __name__=='__main__':
    app.run(debug=True, port=5003)