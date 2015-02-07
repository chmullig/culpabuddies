import os
from flask import Flask, render_template
from pprint import pformat
import numpy
from pymongo import MongoClient
import pymongo
import cPickle
from bson.binary import Binary
from sklearn.metrics.pairwise import linear_kernel
from sklearn.feature_extraction.text import TfidfVectorizer

mongouri = os.environ['MONGOLAB_URI']
client = MongoClient(mongouri)
db = client.heroku_app33788183

app = Flask(__name__)
app.debug = True


if os.path.exists("reviews.pickle"):
	print "loading reviews.pickle"
	(reviews, reviews_tfidf, tfidf_vect) = cPickle.load(open("reviews.pickle", "r"))
else:
	print "loading from db"

	reviews = []
	for csprof in db.professors.find({"departments" : 7}):
		reviews.extend([dict(x) for x in db.reviews.find({"professor_ids" : csprof["_id"]}).sort("_id", 1) ])
	review_texts = []
	for review in reviews:
	    review.pop('review_tfidf')
	    review_texts.append(review["review_text"])

	print "data fetched, doing training."
	tfidf_vect = TfidfVectorizer()
	reviews_tfidf = tfidf_vect.fit_transform(review_texts)

	cPickle.dump((reviews, reviews_tfidf, tfidf_vect), open("reviews.pickle", "w"), protocol=cPickle.HIGHEST_PROTOCOL)


print "done."
@app.route('/')
def index():
	return "hello"

@app.route('/professor_id/<int:professor_id>')
def professor(professor_id):
	source_reviews_idx = [i for i, x in enumerate(reviews) if professor_id in x['professor_ids']]

	pscore = {} #maps id to (n, average of similarities)
	for i in source_reviews_idx:
		gram = linear_kernel(reviews_tfidf[i], reviews_tfidf)
		# for j, review in enumerate(reviews):
		# 	for pid in review["professor_ids"]:
		# 		try:
		# 			z = pscore[pid]
		# 		except KeyError:
		# 			z = (0, 0.0)
		# 		z = (z[0]+1, (gram.flatten()[j] - z[1])/(z[0]+1))
		# 		pscore[pid] = z
	top10 = sorted(pscore.items(), key=lambda x: x[1][1], reverse=True)[:10]

	profs = [db.professors.find_one({"_id" : professor_id})]
	for profid, score in top10:
		match = db.professors.find_one({"_id" : profid})
		profs.append((score, match))
	return pformat(profs)
	#return pformat([reviews[i] for i in top10])

if __name__ == '__main__':
    app.run()

