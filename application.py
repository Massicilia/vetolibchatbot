# _____TF-IDF libraries_____
import json
# _____helper Libraries_____
import os
import pickle
import random
import timeit

import numpy as np
import requests
from flask import Flask, json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# _____________DATA PROCESS
URL = "https://vetolibapi.herokuapp.com/api/v1/consultation"
r = requests.get(url=URL)
global consultations
consultations = r.json()
doExist = 0

# récupérer les données de intents.json
with open("previous_chats.json", encoding='utf8') as file:
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

with open("previous_chats.json", 'w', encoding='utf8') as outfile:
    json.dump(dataToAdd, outfile)


# _____________DATA PROCESS

def talk_to_cb_primary(test_set_sentence, minimum_score, json_file_path, tfidf_vectorizer_pikle_path,
                       tfidf_matrix_train_pikle_path):
    test_set = (test_set_sentence, "")

    try:
        ##--------------to use------------------#
        f = open(tfidf_vectorizer_pikle_path, 'rb')
        tfidf_vectorizer = pickle.load(f)
        f.close()

        f = open(tfidf_matrix_train_pikle_path, 'rb')
        tfidf_matrix_train = pickle.load(f)
        f.close()
        # ----------------------------------------#
    except:
        # ---------------to train------------------#
        tfidf_vectorizer, tfidf_matrix_train = train_chat(json_file_path, tfidf_vectorizer_pikle_path,
                                                          tfidf_matrix_train_pikle_path)
        # -----------------------------------------#

    tfidf_matrix_test = tfidf_vectorizer.transform(test_set)

    cosine = cosine_similarity(tfidf_matrix_test, tfidf_matrix_train)

    cosine = np.delete(cosine, 0)
    max = cosine.max()
    response_index = 0
    if (max > minimum_score):
        new_max = max - 0.01
        list = np.where(cosine > new_max)
        response_index = random.choice(list[0])
    else:
        return "Je n'ai pas d'informations sur cela", 0

    j = 0

    with open(json_file_path, "r") as sentences_file:
        reader = json.load(sentences_file)
        for row in reader:
            j += 1
            if j == response_index:
                # if delimeter in row[1]:
                #    # get newest suggestion
                #    answer_row = row[1].split(delimeter)
                #    row[1] = answer_row[1]

                # else:  # add new suggestion
                #    note = "just return old original suggestion"

                return row["response"], max
                break


def train_chat(json_file_path, tfidf_vectorizer_pikle_path, tfidf_matrix_train_pikle_path):
    i = 0
    sentences = []
    # enter your test sentence
    sentences.append(" Pas toi.")
    sentences.append(" Pas toi.")

    start = timeit.default_timer()

    # enter jabberwakky sentence
    with open(json_file_path, "r") as sentences_file:
        reader = json.load(sentences_file)
        for row in reader:
            sentences.append(row["message"])
            i += 1

    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix_train = tfidf_vectorizer.fit_transform(sentences)  # finds the tfidf score with normalization
    stop = timeit.default_timer()
    print("training time took was : ")
    print(stop - start)

    f = open(tfidf_vectorizer_pikle_path, 'wb')
    pickle.dump(tfidf_vectorizer, f)
    f.close()

    f = open(tfidf_matrix_train_pikle_path, 'wb')
    pickle.dump(tfidf_matrix_train, f)
    f.close()

    return tfidf_vectorizer, tfidf_matrix_train
    # -----------------------------------------#


def previous_chats(query):
    minimum_score = 0.7
    file = "previous_chats.json"
    tfidf_vectorizer_pikle_path = "previous_tfidf_vectorizer.pickle"
    tfidf_matrix_train_path = "previous_tfidf_matrix_train.pickle"
    query_response, score = talk_to_cb_primary(query, minimum_score, file, tfidf_vectorizer_pikle_path,
                                               tfidf_matrix_train_path)
    return query_response


api = Flask(__name__)


@api.route('/<inputtext>', methods=['GET'])
def get_chat(inputtext):
    try:
        return json.dumps(previous_chats(inputtext))
    except EOFError:
        return json.dumps("EOFError")


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    api.run(host='0.0.0.0', port=port)