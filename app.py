from flask import Flask, request, jsonify
#import response as res
import os

#init app
app = Flask(__name__)


@app.route('/predict', methods=['POST'])
def get():
    # result in form of array representing probablistic classes
    #resultClassify = res.classify(request.json["sentence"]) 
    resultResponse = res.response(request.json["sentence"])
    responseDict = {} 
    #for r in resultClassify:
        #responseDict[r[0]] = str(r[1])
    responseDict["sentence"] = resultResponse
    print(responseDict)
    return jsonify ( responseDict )


@app.route('/test', methods=['GET'])
def test():
    return "This is test function to success."


#Run server
if __name__ == "__main__":
    app.run(debug=False)