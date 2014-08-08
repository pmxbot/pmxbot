import sys
import urllib.parse
import pymongo

url = sys.argv[1]
db_name = urllib.parse.urlparse(url).path.lstrip('/')
db = pymongo.MongoClient(url)[db_name]
for entry in db.karma.find():
	entry['names'] = list(set(entry['names']))
	db.karma.save(entry)
