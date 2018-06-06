import string
import pymorphy2
import operator

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from flask import Flask, render_template, jsonify, abort
from stop_words import get_stop_words
from flask_pymongo import PyMongo

app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False

app.config['MONGO_DBNAME'] = 'lab'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/lab'

mongo = PyMongo(app)


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/messages')
def get_all_messages():
    messages = mongo.db.messages.find({})
    output = []
    for message in messages:
        item = {'id': str(message['_id']), 'author': message['author'], 'text': message['text'],
                'date': message['date'].strftime("%d/%m/%y %H:%M"), 'theme': message['theme']}

        output.append(item)

    return jsonify(output)


@app.route('/tags')
def get_tags():
    return jsonify(tf_idf_vectorization_with_kmeans(get_messages()))


def normalize_text(text):

    text = text.lower()
    #remove all digits
    #remove all punctuation
    exclude = set(string.punctuation)

    new_text = ""
    for ch in text:
        if ch.isdigit() or (ch in exclude):
            new_text += ' '
        else:
            new_text += ch

    return new_text


def basic_morph_from_and_remove_stop_words(texts):

    morph_analyzer_ru = pymorphy2.MorphAnalyzer()

    stop_words_ru = get_stop_words("russian")
    stop_words_uk = get_stop_words("ukrainian")

    new_texts = []

    for text in texts:
        new_text = ""
        for word in text.split():
            normal_word = morph_analyzer_ru.parse(word)[0].normal_form
            if normal_word not in stop_words_ru and normal_word not in stop_words_uk:
                new_text += normal_word + " "
        new_texts.append(new_text)

    return new_texts


def get_messages():
    messages = mongo.db.messages.find({})
    texts = []
    for message in messages:
        texts.append(message['text'])

    new_texts = []
    for text in texts:
        new_texts.append(normalize_text(text))

    new_texts = basic_morph_from_and_remove_stop_words(new_texts)

    return new_texts


def tf_idf_vectorization_with_kmeans(texts):

    vectorizer = TfidfVectorizer(stop_words='english')

    X = vectorizer.fit_transform(texts)
    idf = vectorizer.idf_
    true_k = 2
    model = KMeans(n_clusters=true_k, init='k-means++', max_iter=300, n_init=1)
    model.fit(X)

    print("Top terms per cluster:")
    order_centroids = model.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names()

    tags = []
    for ind in order_centroids[0, :20]:
        tags.append(terms[ind])

    return tags
