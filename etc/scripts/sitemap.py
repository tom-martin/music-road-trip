from pymongo import Connection
import urllib

c = Connection()
db = c["music_tour"]
result_cache = db["results_cache"]


print """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">"""

for result in result_cache.find():
  print "<url>"
  print "<loc>http://musicroadtrip.com/musictour/" + urllib.quote(result["results"][0]["name"].encode("utf-8")) + "/to/" + urllib.quote(result["results"][-1]["name"].encode("utf-8"))+"</loc>"
  print "</url>"

  print "<url>"
  print "<loc>http://musicroadtrip.com/musictour/" + urllib.quote(result["results"][-1]["name"].encode("utf-8")) + "/to/" + urllib.quote(result["results"][0]["name"].encode("utf-8"))+"</loc>"
  print "</url>"
print "</urlset>"
