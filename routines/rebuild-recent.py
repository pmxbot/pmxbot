import sys
import urllib.parse
import pymongo


def run():
    url = sys.argv[1]
    db_name = urllib.parse.urlparse(url).path.lstrip('/')
    db = pymongo.MongoClient(url)[db_name]
    for entry in db.logs.find():
        entry['ref'] = entry.pop('_id')
        spec = dict(channel=entry['channel'])
        db.recent.update(spec, entry, upsert=True)


if __name__ == '__main__':
    run()
