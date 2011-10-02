from pymongo import Connection
import urllib

c = Connection()
db = c["music_tour"]
result_cache = db["results_cache"]

for result in result_cache.find():
  print "http://musicroadtrip.com/musictour/" + urllib.quote(result["results"][0]["name"].encode("utf-8")) + "/to/" + urllib.quote(result["results"][-1]["name"].encode("utf-8"))
  print "http://musicroadtrip.com/musictour/" + urllib.quote(result["results"][-1]["name"].encode("utf-8")) + "/to/" + urllib.quote(result["results"][0]["name"].encode("utf-8"))

