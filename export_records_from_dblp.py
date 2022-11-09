import json
import argparse
import requests


parser = argparse.ArgumentParser(description='Demo of argparse')
parser.add_argument('--bht', type=str, required=True, help='bth key')

URL="https://dblp.org/search/publ/api"

def download_json(args):
    assert len(args.bht) > 0
    data = {
        'q': 'toc:%s:' % args.bht,
        'h': 1000,
        'format': 'json'
    }
    response = requests.get(URL, params=data)
    if response.status_code == 200:
        return response.json()
    else:
        print("request error:\n", response.text)
        exit(-1)

def parse_json(json, args):
    result = json['result']
    hits = result['hits']['hit']
    conf = {}
    docs = []
    for hit in hits:
        hit = hit['info']
        if 'publisher' in hit:
            conf['title'] = hit['title'].replace("&amp;", "&")
            conf['venue'] = hit['venue']
            continue
        doc = {}
        doc['title'] = hit["title"].replace("&amp;", "&")
        doc['venue'] = hit['venue']
        doc['year'] = hit['year']
        doc['url'] = hit['ee']
        doc['pages'] = hit['pages']
        doc['authors'] = []
        authors = hit['authors']['author']
        if type(authors) == dict:
            authors = [authors]
        for au in authors[:3]:
            words = au['text'].split()
            if words[-1].isnumeric():
                author = " ".join(words[:-1])
            else:
                author = " ".join(words)
            doc['authors'].append(author)
        if len(authors) > 3:
            doc['authors'].append("etc")
        docs.append(doc)
    docs = sorted(docs, key=lambda x:int(x['pages'].split("-")[0]))
    return conf, docs

def write_to_md(conf, docs, template, filepath):
    lines = []
    for doc in docs:
        ref = "%s. %s in %s(%s' %s). %s. %s" % (
            ", ".join(doc['authors']), doc['title'], conf['title'], doc['venue'], doc['year'][-2:],
            doc['pages'], doc['url']
        )
        lines.append(template.format(title=doc['title'], ref=ref))

    with open(filepath, 'w') as f:
        f.write("\n".join(lines))

TEMPLATE='''
- **{title}**
    > {ref}
'''

if __name__ == '__main__':
    args = parser.parse_args()
    print(args)
    json = download_json(args)
    conf, docs = parse_json(json, args)
    write_to_md(conf, docs, TEMPLATE, "res/%s.md" % conf['venue'])
