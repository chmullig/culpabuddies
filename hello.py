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
from collections import defaultdict

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
	reviews = [dict(x) for x in db.reviews.find().sort("_id", 1) ]

	# reviews = []
	# for csprof in db.professors.find({"departments" : 7}):
	# 	reviews.extend([dict(x) for x in db.reviews.find({"professor_ids" : csprof["_id"]}).sort("_id", 1) ])
	
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
	grams = []
	for i in source_reviews_idx:
		grams.append(linear_kernel(reviews_tfidf[i], reviews_tfidf).flatten())

	gram = numpy.median(numpy.array(grams), axis=0)
	print type(gram)
	prof_scores = defaultdict(float) #maps professor_id -> score
	prof_counts = defaultdict(int) #maps professor_id -> counts
	for i in xrange(len(reviews)):
		for profid in reviews[i]["professor_ids"]:
			#print "looking at review %s. I think it's for professor %s. It had similarity score of %s. It starts with %s" % (i, profid, gram[i], reviews[i]["review_text"][:140])
			prof_scores[profid] += gram[i]
			prof_counts[profid] += 1
	
	for profid in prof_scores.keys():
		prof_scores[profid] = prof_scores[profid] / prof_counts[profid]

	prof = db.professors.find_one({"_id" : professor_id})
	ret = []
	for profid, score in sorted(prof_scores.items(), key=lambda x: x[1], reverse=True)[1:15]:
		ret.append((score, db.professors.find_one({"_id" : profid})))
	return render_template('professor.html', prof=prof, matches=ret, departments=db.departments.find())

if __name__ == '__main__':
    app.run()

