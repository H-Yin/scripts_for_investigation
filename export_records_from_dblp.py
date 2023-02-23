import json
import argparse
import requests

DOMAIN_LIST=[
    'dblp.uni-trier.de',
    'dblp.dagstuhl.de',
    'dblp.org',
]

URL="https://%s/search/publ/api"

parser = argparse.ArgumentParser(description='Demo of argparse')
parser.add_argument('--bht', type=str, help='bth key')
parser.add_argument('--conf', type=str, help='conference')
parser.add_argument('--year', type=str, help='year')

def parse_args():
    args = parser.parse_args()
    if args.bht is None:
        if args.conf is not None and args.year is not None:
            args.bht = 'db/conf/%s/%s%s.bht' % (args.conf, args.conf, args.year)
        else:
            print("ERROR: One of '--bht <bht>' and '--conf <conf> --year <year>' must be specified.")
            parser.print_help()
            exit(-1)
    return args

def download_doc(args, f=0):
    assert len(args.bht) > 0
    data = {
        'q': 'toc:%s:' % args.bht,
        'f': f,
        'h': 500,
        'format': 'json'
    }
    for domain in DOMAIN_LIST:
        response = requests.get(URL % domain, params=data)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 500:
            print("ERROR: Server Internal Error")
        else:
            print("request error:\n", response.text)
    exit(-1)

def pre_parse_doc(doc):
    result = doc['result']
    total = int(result['hits']['@total'])
    first = int(result['hits']['@first'])
    count = int(result['hits']['@sent'])
    hits = result['hits']['hit']
    return total, first, count, hits

def parse_doc(hits, args):
    conf = {}
    docs = []
    for hit in hits:
        try:
            hit = hit['info']
            if hit['type'] == 'Editorship' or 'publisher' in hit:
                conf['title'] = hit['title']
                if 'venue' not in hit:
                    conf['venue'] = hit['key'].split("/")[1].upper()
                else:
                    conf['venue'] = hit['venue'][0] if type(hit['venue']) == list else hit['venue']
                conf['year'] = hit['year']
                continue

            doc = {}
            doc['title'] = hit["title"]
            doc['venue'] = hit['venue']
            doc['year'] = hit['year']
            doc['url'] = hit['ee']
            doc['pages'] = hit['pages'] if 'pages' in hit else '0-0'
            doc['authors'] = []
            if 'authors' in hit:
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
        except:
            print(hit)
    docs = sorted(docs, key=lambda x:(int(x['pages'].split("-")[0]), x['title']))
    if len(conf) == 0:
        conf['title'] = ''
        conf['venue'] = ''
        conf['year'] = ''
    return conf, docs

def write_to_md(conf, docs, template, filepath):
    lines = []
    for doc in docs:
        pages = '' if doc['pages'] == '0-0' else "%s." % doc['pages']
        ref = "%s. %s in %s(%s' %s). %s %s" % (
            ", ".join(doc['authors']), doc['title'], conf['title'], doc['venue'], doc['year'][-2:],
            pages, doc['url']
        )
        lines.append(template.format(title=doc['title'], ref=ref))

    with open(filepath, 'w') as f:
        f.write("\n".join(lines))

TEMPLATE='''
- **{title}**
    > {ref}
'''


if __name__ == '__main__':
    args = parse_args()
    print(args)
    filename = args.bht.split("/")[-1].split(".")[0].upper()
    start = 0
    doc_list = []
    while True:
        doc = download_doc(args, f=start)
        with open("res/%s_%d.json"% (filename, start), 'w') as f:
            f.write(json.dumps(doc))
        total, first, count, hits = pre_parse_doc(doc)
        # print(first, count, len(hits))
        doc_list.extend(hits)
        start = first + count
        if start >= total:
            break
    conf, items = parse_doc(doc_list, args)
    print(len(doc_list), len(items))
    write_to_md(conf, items, TEMPLATE, "res/%s.md" % filename)
