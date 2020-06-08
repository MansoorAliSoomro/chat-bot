from flask import Flask, request, jsonify
import requests
import tensorflow as tf
import src.response as res
import os
from flask import request
import json;
from flask import Response
import re

#init app
app = Flask(__name__)

BANK_APP_URL = "https://nameless-stream-67237.herokuapp.com" 

# only user ID is store
context = {}

# this is to make sure that data is stored for user context 
statefulContext = {}

@app.route('/predict', methods=['POST'])
def get():
    key = request.headers['key'] if 'key' in request.headers else '123'
    resultResponse = res.response(request.json["sentence"] , context , key, False)
    responseDict = {}
    if resultResponse:
        responseDict['intent'] = resultResponse['intent']
        responseDict['probability'] = str ( resultResponse['probability'] )
        responseDict['response'] = resultResponse['response']
        responseDict['context_filter'] =  resultResponse['context_filter'] if 'context_filter' in resultResponse else ''
        #responseDict['context_filter'] =  resultResponse['context_filter'] if 'content_filter' in resultResponse else ''
        responseDict['context_set'] = resultResponse['context_set'] if 'context_set' in resultResponse else ''
        responseDict['sentence'] = request.json["sentence"]
        responseDict['headers'] = { 'auth-token' : request.headers['auth-token']}
    
    print(resultResponse);
    result = getIntentResponse(responseDict, key)
    return result
    try:
        resp = jsonify(responseDict)
        return resp
    except:
        return { "error" : "Internal Server Error" }


@app.route('/test', methods=['POST'])
def test():
    response = res.response(request.json["sentence"] , context , '123', False)
    if response is not None:
        return jsonify( intent =  response['intent'], prob = response['probability']  )
    return None

@app.route('/context', methods=['GET'])
def getContext():
    return Response( json.dumps(context) )

@app.route('/contextstate', methods=['GET'])
def getStateContext():
    return Response( json.dumps(statefulContext) )

def getIntentResponse(response, userID):
    if('intent' in response):
        if(response['intent'] == 'username'):
            #user = requests.get('http://localhost:3000/api/users/username', headers=headers)
            user = requests.get(BANK_APP_URL + '/api/users/username', headers=response['headers'])
            #print (accounts.json())
            user = user.json()
            username = user['username']
            removeUserID(userID)
            return  jsonify ( speak = 'Greetigns What can I do for you ' + username )
        elif (response['intent'] == 'accountbalance'):
            account = requests.get( BANK_APP_URL + '/api/accounts', headers=response['headers'] )
            account = account.json()
            balance = account['currentBalance']
            removeUserID(userID)
            return jsonify( speak = 'Your current balance is ' + str(balance) )
        
        elif ( response['intent'] == 'greeting' ):
            print(response['response'])
            greetResult = response['response']
            removeUserID(userID) 
            return jsonify( speak = greetResult )

        elif (response['intent'] == 'accountlist' ):
            _list = requests.get( BANK_APP_URL + '/api/accounts/all', headers=response['headers'] )
            _list = _list.json()
            accounts = []
            for acc in _list:
                a = { 'id': acc['id'], 'currentBalance': acc['currentBalance'], 'description': acc['description'], 'account_number': acc['account_number'] }
                accounts.append(a)
            removeUserID(userID)
            return  Response( json.dumps ( {  'speak': 'You have ' + str( len(accounts) ) + ' accounts listed below:' , 'data': accounts, 'variable_usage': ['currentBalance', 'description', 'account_number'] } ) , mimetype='application/json') 

        elif (response['intent'] == 'beneficiarieslist'):
            _list = requests.get( BANK_APP_URL + '/api/beneficiaries/all', headers=response['headers'] ).json()
            beneficiaries = []
            for bef in _list:
                b = { 'id': bef['id'],  'name': bef['beneficiary_name'],  'account_number': bef['Account']['account_number'],  'balance': bef['Account']['currentBalance'] }
                beneficiaries.append(b)
            removeUserID(userID)
            return  Response( json.dumps ( {  'speak': 'You have ' + str( len(beneficiaries) ) + ' accounts beneficiaries listed below:' , 'data': beneficiaries, 'variable_usage': ['name',  'account_number'] } ) , mimetype='application/json')
        
        elif (response['intent'] == 'switch account'):
            _list = requests.get( BANK_APP_URL + '/api/accounts/all', headers=response['headers'] )
            _list = _list.json()
            accounts = []
            index = 0
            for acc in _list:
                a = { 'id': acc['id'], 'currentBalance': acc['currentBalance'], 'description': acc['description'], 'account_number': acc['account_number'], 'option': index }
                index += 1
                accounts.append(a)
            if(userID in context):
                statefulContext[userID] =  {'data': accounts}
            return  Response( json.dumps ( { 'speak': 'Select an account below: ' , 'data': accounts, 'variable_usage': ['currentBalance', 'description', 'account_number'] } ) , mimetype='application/json')

        elif ( response['intent'] == 'transaction' ):
            _list = requests.get(BANK_APP_URL + '/api/beneficiaries/all', headers=response['headers'])
            _list = _list.json()
            beneficiaries = []
            index = 0
            for bef in _list:
                b = { 'id': bef['id'],  'name': bef['beneficiary_name'],  'account_number': bef['Account']['account_number'], 'option': index }
                index += 1
                beneficiaries.append(b) 
            if(userID in context):
                statefulContext[userID] =  {'data': beneficiaries}
            return  Response( json.dumps ( {  'speak': 'Select One of beneficiaries listed below:' , 'data': beneficiaries, 'variable_usage': ['name',  'account_number'] } ) , mimetype='application/json')

        elif (response['intent'] == 'options'):
            if(response['context_filter'] == "switch account"):
                sentence = response['sentence']
                match = re.search("[0-9]+$", sentence)
                if (not match):
                    return "Error match does not exist"
                else:
                    value = int (match.group())
                userContext = None
                if ( userID in context ): 
                    userContext = list(context[userID].keys())[0] if isinstance( context[userID], dict ) else context[userID]
                if( response['context_filter'] ==  userContext and userContext == "switch account"  ):
                    data = statefulContext[userID]['data']
                    if value > len(data):
                        return "Too High value"
                    for i in data:
                        if i['option'] == value:
                            id = i['id']
                    print ( id )
                    response = requests.put(BANK_APP_URL + '/api/accounts/switch', json={'id': id}, headers=response['headers'])
                    return Response( json.dumps( { 'speak': 'account switched successfully' } ), mimetype='application/json' )
                    removeUserID(userID)
                else:
                    return "error occured"
            elif( response['context_filter'] == 'transaction' ):
                sentence = response['sentence']
                match = re.search("[0-9]+$", sentence)
                if (not match):
                    return "Error match does not exist"
                value = int ( match.group() )
                userContext = None
                if ( userID in context ): 
                    userContext = list(context[userID].keys())[0] if isinstance( context[userID], dict ) else context[userID]
                    print(userContext)
                if( response['context_filter'] == userContext and userContext == 'transaction' ):
                    data = statefulContext[userID]['data']
                    result = [ opt for opt in data if opt['option'] == value ]
                    if ( len (result) == 1 ):
                        result = result[0]['account_number']
                    else: 
                        result = None                         
                    context[userID] = response['context_set']
                    statefulContext[userID] = {}
                    statefulContext[userID]['account_number'] = result    
                    return jsonify(speak = "Select the amount of cash you want to transfer to " +  str ( result ) );
                

                return jsonify( speak = userContext )
            
            
            else:
                return jsonify( speak = 'Can not understand' )
        
        elif (response['intent'] == 'transfer' ):
            sentence = response['sentence']
            match = re.search("[0-9]+$", sentence)
            if (not match):
                return "Error match does not exist"
            else:
                value = int (match.group())
            
            accountNumber = statefulContext[userID]['account_number']
            amount = value

            response = requests.post(BANK_APP_URL + '/api/transaction', json={ 'account_number': accountNumber, 'amount': value }, headers=response['headers'])
            response.json();
            removeUserID(userID)

            if(response): 
                return jsonify( speak = "Your cash to this is trasnfered succuessully to accountnumber "  + str( accountNumber ) + " and the cash is " + str(value) )

            return jsonify ( speak = "Error Transfering cash" )

        elif (response['intent'] == 'transactionhistory' ):
            print("the intent is transaction history")
            result = requests.get(BANK_APP_URL + '/api/transaction/history', headers=response['headers'])
            result = result.json()
            return Response( json.dumps ( {  'speak': 'You have ' + str( len(result) ) + ' transactions listed below:' , 'data': result, 'variable_usage': ['username' , 'amount', 'account_number'] } ) , mimetype='application/json')
            
        elif ( response['intent'] == 'account balance' ):
            result = requests.get(BANK_APP_URL + '/api/accounts', headers=response['headers'])
            result = result.json()
            return Response( json.dumps ( {  'speak': 'your account balance is ' + str(result['currentBalance']) }, mimetype='application/json' ))
        
        elif ( response['intent'] == 'currentaccount' ):
            result = requests.get(BANK_APP_URL + '/api/accounts', headers=response['headers']).json()
            currentBalance = result['currentBalance']
            status = 'active' if result['status'] == 1 else 'unactive'  
            des = result['description']
            accountNum = result['account_number']
            
            return Response ( json.dumps ( { 'speak': "These are your current account details", 'data': { 
                'currentBalance': currentBalance, 'status': status,
                'description': des, 'account_number': accountNum } } ) , mimetype='application/json' )

        else:
            return jsonify( speak = 'No intent available' )

    else:
        return jsonify( speak = 'Can not understand' ) 


def removeUserID(userID):
    print(userID)
    if userID in context:
        del context[userID]
    if userID in statefulContext:
        del statefulContext[userID]

#Run server
if __name__ == "__main__":
    app.run(debug=True, host= 'localhost')