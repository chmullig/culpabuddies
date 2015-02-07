import os
from pymongo import MongoClient
import pymongo
import cPickle
from bson.binary import Binary

from sklearn.feature_extraction.text import TfidfVectorizer

mongouri = os.environ['MONGOLAB_URI']
client = MongoClient(mongouri)
db = client.heroku_app33788183

reviews = []
review_texts = []
for review in db.reviews.find().sort("_id", 1):
	reviews.append(review)
	review_texts.append(review["review_text"])


#train the thingie

print "data fetched, doing training."
tfidf_vect = TfidfVectorizer()
reviews_tfidf = tfidf_vect.fit_transform(review_texts)
print "tfidf done"

print reviews[1], reviews_tfidf[1]

for i, review in enumerate(reviews):
	review['review_tfidf'] = Binary(cPickle.dumps(reviews_tfidf[i], protocol=2))
	db.reviews.save(review)

