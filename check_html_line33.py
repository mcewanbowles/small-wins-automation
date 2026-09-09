import urllib.request

html = urllib.request.urlopen('http://127.0.0.1:5050/').read().decode('utf-8', 'replace')
lines = html.split('\n')
for i, line in enumerate(lines[:40], 1):
    print(i, repr(line))
