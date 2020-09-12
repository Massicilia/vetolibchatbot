import json
import requests

URL = "https://vetolibapi.herokuapp.com/api/v1/consultation"
r = requests.get(url=URL)
global consultations
consultations = r.json()
doExist = 0

# récupérer les données de intents.json
with open("previous_chats.json") as file:
    data = json.load(file)


def getDatasFormatFromDB(data):
    for consultation in consultations:
        doesIntentExists = 0
        for intent in data:
            if intent['message'] == "Mon " + consultation['race'] + " a une " + consultation['symptoms']:
                doesIntentExists = 1
                doExist = 0
                if consultation['disease'] in intent['response']:
                    doExist = 1
                if doExist == 0:
                    response = consultation['disease']
                    intent['response'] = intent['response'] + " ou " + response
        if doesIntentExists == 0:
            data.append({
                'message': "Mon " + consultation['race'] + " a une " + consultation['symptoms'],
                'response': "Cela peut être " + consultation['disease']
            })
    return data


dataToAdd = getDatasFormatFromDB(data)


with open("previous_chats.json", 'w') as outfile:
    json.dump(dataToAdd, outfile)
