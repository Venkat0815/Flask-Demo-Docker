from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.My_Bank
users = db["users"]

    # Utils 


def userExist(username):

    if users.count_documents({ "Username": username }) == 0:
        return False
    return True

def generateReturnDictionary(code, msg):
    
    retJson = {
        "status": code,
        "msg": msg
    }

    return retJson

def hashPassword(password):

    hash_pwd = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())

    return hash_pwd

def verifyCredentials(username, password):
    
    hashed_pwd = users.find_one({"Username": username}, {"Password": 1, "_id": 0})["Password"]

    if bcrypt.hashpw(password.encode("utf8"), hashed_pwd) == hashed_pwd:
        return generateReturnDictionary(200, "User Verified"), True
    return generateReturnDictionary(301, "Check Your Credentials"), False

def updateAccount(username, amount):
    
    update_status = users.update_one({"Username": username}, {
                                                                "$inc":{
                                                                        "Own":  amount
                                                                       }
                                                            })
    if update_status.modified_count:
        return generateReturnDictionary(200, " Amount added to account successfully !! ")
    return generateReturnDictionary(301, " Amount not added ")

def debitAccount(username, amount):
    
    debt_status = users.update_one({"Username": username}, {
                                                                "$inc": {
                                                                    "Own" : -amount
                                                                } 
                                                           })
    if debt_status.modified_count:
        return generateReturnDictionary(200, "Loan Payed Successfully!!"), False
    return generateReturnDictionary(301, " Not Debted amount !! "), True

def debtAccount(username, amount):

    update_status = users.update_one({"Username": username}, {
                                                                "$inc":{
                                                                        "debt":  amount
                                                                       }
                                                            })
    if update_status.modified_count:
        return generateReturnDictionary(200, " Amount added to account successfully !! ")
    return generateReturnDictionary(301, " Amount not added ")

def cashWithUser(username, amount):
    
    cash = users.find_one({"Username": username}, {"Own": 1, "_id": 0})["Own"]

    if cash > amount:
        return True
    return False

def amountCheck(amount):
    if not (amount > 0):
        return generateReturnDictionary(304, " Amount can't be negative "), True
    
    if not (amount > 100):
        return generateReturnDictionary(302, "Minimum amount need to be 100 RS"), True
    
    return None, False
     

    # Resources

class Register(Resource):

    def post(self):        
        
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        if not userExist(username):
            return jsonify(generateReturnDictionary(301, " Already an user exists!! "))
        
        hashed_password = hashPassword(password)

        insert_acknowledge = users.insert_one({
                                            "Username": username,
                                            "Password": hashed_password,
                                            "Own": 0,
                                            "Debt": 0
                                        }) 
        print(insert_acknowledge)
        if insert_acknowledge.inserted_id:
            return jsonify(generateReturnDictionary(200, " Registered Successfully !! "))
        
        return jsonify(generateReturnDictionary(301, " User Not Registered Successfully !! "))

class Add(Resource):

    def post(self):

        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        amount = postedData["amount"]

        if not userExist(username):
            return jsonify(generateReturnDictionary(301, "User Doesn't Exist"))

        credentials_status, error = verifyCredentials(username, password)

        if not error:
            return jsonify(credentials_status)

        #TODO Amount value can't be negative checkamount
        retJson, check_status = amountCheck(amount)
        
        if check_status:
            return jsonify(retJson)

        retJson = updateAccount("Bank", 1)
        retJson = updateAccount(username, amount-1)

        return jsonify(retJson)

class Transfer(Resource):
    
    def post(self):
        
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        to       = postedData["to"]
        amount   = postedData["amount"]

        if not userExist(username):
            return generateReturnDictionary(301, "User Doesn't Exist")

        credentials_status, error = verifyCredentials(username, password)

        if not error:
            return jsonify(credentials_status)

        retJson, check_status = amountCheck(amount)

        if check_status:
            return jsonify(retJson)

        cash_status = cashWithUser(username, amount)

        if not cash_status:
            return jsonify(generateReturnDictionary(302, "Not there enough money"))
        
        retJson, debt_status = debitAccount(username, amount)

        if debt_status:
            return jsonify(retJson)
        
        if not userExist(to):
            return generateReturnDictionary(301, "User Doesn't Exist")
        
        retJson = updateAccount("Bank", 1)
        retJson = updateAccount(to, amount-1)

        return jsonify(retJson)


class Balance(Resource):

    def post(self):
        
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        if not userExist(username):
            return jsonify(generateReturnDictionary(301, "User Doesn't Exist"))

        credentials_status, error = verifyCredentials(username, password)

        if not error:
            return jsonify(credentials_status)
        
        cash = users.find_one({"Username": username}, {"Own":1, "_id": 0})["Own"]

        return jsonify(generateReturnDictionary(200, cash))

class TakeLoan(Resource):

    def post(self):
        
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        amount = postedData["amount"]

        if not userExist(username):
            return jsonify(generateReturnDictionary(301, "User Doesn't Exist"))
        
        credentials_status, error = verifyCredentials(username, password)

        if not error:
            return jsonify(credentials_status)
        
        debtAccount(username, amount)
        retJson = updateAccount(username, amount)

        return jsonify(retJson)
        
class PayLoan(Resource):

    def post(self):
        
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        amount = postedData["amount"]

        if not userExist(username):
            return jsonify(generateReturnDictionary(301, "User Doesn't Exist"))

        credentials_status, error = verifyCredentials(username, password)

        if not error:
            return jsonify(credentials_status)
        retJson, check_status = amountCheck(amount)

        if check_status:
            return jsonify(retJson)

        cash_status = cashWithUser(username, amount)

        if not cash_status:
            return jsonify(generateReturnDictionary(302, "Not there enough money"))

        debtAccount(username, amount)
        retJson,error = debitAccount(username, amount)
        
        if not error:
            return jsonify(retJson)
        
        return jsonify({"status": 301, "msg": "Some error occured!! "})

api.add_resource(Register, '/register')
api.add_resource(Add, '/add')
api.add_resource(Transfer, '/transfer')
api.add_resource(Balance, '/balance')
api.add_resource(TakeLoan, '/takeloan')
api.add_resource(PayLoan, '/payloan')

if __name__ == "__main__":
    app.run(host="0.0.0.0")