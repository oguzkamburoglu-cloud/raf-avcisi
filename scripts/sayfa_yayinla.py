#!/usr/bin/env python3
"""Adds or replaces pages on a Firebase Hosting site without touching anything else.

Clones the live version, lays the given files over it and releases the result, so every
file that is not in the folder stays exactly as it is on the live site.

usage: sayfa_yayinla.py <site_id> <domain> <folder> <slash:1|0> [changed-files.txt]
  folder             mirrors the site root (folder/liste/x/index.html -> /liste/x/index.html)
  changed-files.txt  optional list of repo paths; only those inside <folder> are published
env: SA_JSON = path of the service account JSON. DRY=1 prints the plan and calls nothing.
"""
import gzip, hashlib, json, os, sys, time, urllib.error, urllib.request

SID, DOMAIN, ROOT, SLASH = sys.argv[1], sys.argv[2].rstrip('/'), sys.argv[3].rstrip('/'), sys.argv[4] == '1'
ONLY = sys.argv[5] if len(sys.argv) > 5 else None
DRY = os.environ.get('DRY') == '1'
API = 'https://firebasehosting.googleapis.com/v1beta1/'
TOK = None


def token():
    from google.oauth2 import service_account
    import google.auth.transport.requests
    c = service_account.Credentials.from_service_account_file(
        os.environ['SA_JSON'], scopes=['https://www.googleapis.com/auth/cloud-platform'])
    c.refresh(google.auth.transport.requests.Request())
    return c.token


def call(method, url, body=None, raw=None, ctype='application/json'):
    h = {'Authorization': 'Bearer ' + TOK, 'Content-Type': ctype}
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(url if url.startswith('http') else API + url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        return {'_error': e.code, '_body': e.read().decode()[:300]}


def get(u):
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:  # network trouble must not hide the result of the release
        return 0, str(e)


paths = []
if ONLY and os.path.exists(ONLY):
    for line in open(ONLY, encoding='utf-8'):
        p = line.strip()
        if p.startswith(ROOT + '/') and os.path.isfile(p):
            paths.append(p)
else:
    for d, _, fs in os.walk(ROOT):
        paths += [os.path.join(d, f) for f in fs]
changed = {}
for p in sorted(paths):
    rel = p[len(ROOT):]
    if os.path.basename(p).startswith('.') or rel == '/README.md':
        continue
    changed[rel] = open(p, 'rb').read()
if not changed:
    print('nothing to publish')
    sys.exit(0)
print('files', len(changed))
urls = sorted(DOMAIN + (p[:-len('index.html')] if SLASH else (p[:-len('/index.html')] or '/'))
              for p in changed if p.endswith('/index.html'))
print('pages', len(urls))

if '/sitemap.xml' not in changed:
    code, sm = get(DOMAIN + '/sitemap.xml')
    if code == 200 and '</urlset>' in sm:
        have = set(x.split('</loc>')[0].strip() for x in sm.split('<loc>')[1:])
        add = [u for u in urls if u not in have]
        if add:
            sm = sm.replace('</urlset>', ''.join(f'<url><loc>{u}</loc></url>\n' for u in add) + '</urlset>')
            changed['/sitemap.xml'] = sm.encode('utf-8')
        print('sitemap add', len(add))
    else:
        print('sitemap not touched (status', code, ')')

if DRY:
    for p in sorted(changed):
        print(' ', p, len(changed[p]))
    sys.exit(0)

TOK = token()
r = call('GET', f'sites/{SID}/releases?pageSize=1')
if 'releases' not in r:
    sys.exit('STOP: cannot read releases ' + str(r))
live = r['releases'][0]['version']['name']
print('live version', live)
files = {p: (hashlib.sha256(gzip.compress(b, mtime=0)).hexdigest(), gzip.compress(b, mtime=0)) for p, b in changed.items()}
op = call('POST', f'sites/{SID}/versions:clone', {'sourceVersion': live, 'finalize': False})
if '_error' in op:
    sys.exit('STOP clone ' + str(op))
while not op.get('done'):
    time.sleep(2)
    op = call('GET', op['name'])
    if '_error' in op:
        sys.exit('STOP clone wait ' + str(op))
if 'error' in op:
    sys.exit('STOP clone ' + str(op['error']))
ver = op['response']['name']
print('cloned to', ver)
pf = call('POST', f'{ver}:populateFiles', {'files': {k: v[0] for k, v in files.items()}})
if '_error' in pf:
    sys.exit('STOP populate ' + str(pf))
need = set(pf.get('uploadRequiredHashes', []))
print('upload', len(need))
for k, (h, gz) in files.items():
    if h in need:
        r = call('POST', pf['uploadUrl'] + '/' + h, raw=gz, ctype='application/octet-stream')
        need.discard(h)
        if '_error' in r:
            sys.exit('STOP upload failed ' + k + str(r))
st = call('PATCH', f'{ver}?update_mask=status', {'status': 'FINALIZED'})
print(st.get('status', st))
if st.get('status') != 'FINALIZED':
    sys.exit('STOP: not finalized, live site unchanged')
r = call('POST', f'sites/{SID}/releases?versionName={ver}', {'message': 'GitHub ' + os.environ.get('GITHUB_SHA', '')[:7]})
if 'name' not in r:
    sys.exit('STOP release ' + str(r))
print('release', r['name'])
time.sleep(8)
bad = 0
for u in urls:
    c = get(u)[0]
    print(c, u)
    bad += c != 200
print('sitemap urls', get(DOMAIN + '/sitemap.xml')[1].count('<loc>'))
if bad:
    sys.exit(f'{bad} page(s) did not answer 200 after the release')
