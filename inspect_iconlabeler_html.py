import urllib.request
h = urllib.request.urlopen('http://127.0.0.1:5050/').read().decode('utf-8','replace')
idx = h.find('sequence_order')
start = max(0, idx-120)
end = min(len(h), idx+220)
snippet = h[start:end]
print('Around sequence_order:')
print(repr(snippet))
# Also output the exact chars around the join call
j = h.find('.join(', idx)
if j != -1:
    print('Join-call window:')
    print(repr(h[j:j+20]))
    # Show the next few characters to see if there is a backslash or newline
    k = j + 6
    print('After .join(:', [ord(c) for c in h[k:k+6]], h[k:k+6].encode('unicode_escape'))
else:
    print('No .join(')
