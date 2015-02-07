import os
import json
import requests
from pymongo import MongoClient
import pymongo
from bson.objectid import ObjectId
import time

mongouri = os.environ['MONGOLAB_URI']
client = MongoClient(mongouri)
db = client.heroku_app33788183

to_fetch_depts = []
#to_fetch_depts = [3, 4, 63, 61, 45, 41, 38, 44, 28, 56, 81, 42, 53, 29, 7, 49, 106, 52, 8, 70, 9, 58, 48, 10, 11, 12, 30, 1, 68, 57, 13, 37, 71, 15, 69, 43, 16, 17, 109, 19, 50, 20, 21, 22, 23, 92, 46, 24, 25, 62, 31, 34, 35, 66, 26, 27, 36, 40, 110, 111, 112, 114, 115]

for deptid in to_fetch_depts:
	response = requests.get('http://api.culpa.info/departments/department_id/%s' % deptid)
	assert response.status_code == 200
	responsevalue = response.json()
	for deptinfo in responsevalue['departments']:
		deptinfo["_id"] = deptinfo.pop("id")

		courseresponse = requests.get('http://api.culpa.info/courses/department_id/%s' % deptid)
		try:
			deptinfo["courses"] = courseresponse.json()["courses"]
		except:
			pass
		try:
			db.departments.insert(deptinfo)
		except pymongo.errors.DuplicateKeyError:
			pass


print "now get the professors by department"
for deptid in to_fetch_depts:
	response = requests.get('http://api.culpa.info/professors/department_id/%s' % deptid)
	assert response.status_code == 200
	responsevalue = response.json()
	if "professors" not in responsevalue:
		continue
	for profinfo in responsevalue['professors']:
		profinfo["_id"] = profinfo.pop("id")
		profinfo["departments"] = [deptinfo]
		try:
			db.professors.insert(profinfo)
		except pymongo.errors.DuplicateKeyError:
			print "Already added professor %s, but adding department %s" % (profinfo, deptid)
			prof = db.professors.find_one({"_id": profinfo["_id"]})
			prof["departments"].append(deptinfo)
			db.professors.save(prof)

print "now get the professors by class"
for dept in db.departments.find():
	toadddept = dept.copy()
	toadddept.pop("courses")
	for course in dept['courses']:
		if 'fetched_professors' not in course:
			response = requests.get('http://api.culpa.info/professors/course_id/%s' % course["id"])
			assert response.status_code == 200
			responsevalue = response.json()
			if "professors" not in responsevalue:
				continue
			for profinfo in responsevalue['professors']:
				profinfo["_id"] = profinfo.pop("id")
				profinfo["departments"] = [toadddept]
				try:
					db.professors.insert(profinfo)
					print "new professor!", profinfo
				except pymongo.errors.DuplicateKeyError:
					pass
					# prof = db.professors.find_one({"_id": profinfo["_id"]})
					# try:
					# 	dept.pop("courses")
					# except KeyError:
					# 	pass
					# if dept not in prof['departments']:
					# 	print "Already added professor %s, but adding department %s" % (profinfo, dept)
					# 	prof = db.professors.find_one({"_id": profinfo["_id"]})
					# 	prof["departments"].append(dept)
					# 	db.professors.save(prof)


print "fetching reviews"
for prof in db.professors.find({'fetched_reviews' : {'$exists': False} }):
	response = requests.get('http://api.culpa.info/reviews/professor_id/%s' % str(prof["_id"]))
	if response.status_code != 200:
		print response, prof
		continue
	responsevalue = response.json()
	if "reviews" not in responsevalue:
			continue
	for review in responsevalue['reviews']:
		try:
			review["_id"] = review.pop("id")
		except:
			continue
		try:
			db.reviews.insert(review)
		except pymongo.errors.DuplicateKeyError:
			pass
	prof["fetched_reviews"] = True
	db.professors.save(prof)
	time.sleep(0.01)

