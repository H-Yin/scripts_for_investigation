import json
import argparse
import requests

DOMAIN_LIST = [
    'dblp.uni-trier.de',
    'dblp.dagstuhl.de',
    'dblp.org',
]

PROXY = {
    # 'http': 'http://10.0.3.79:5555',
    # 'https': 'https://10.0.100.9:7890'
}

URL = "https://%s/search/publ/api"

parser = argparse.ArgumentParser(description='Demo of argparse')
parser.add_argument('--bht', type=str, help='bth key')
parser.add_argument('--conf', type=str, help='conference')
parser.add_argument('--year', type=str, help='year')


def parse_args():
    cliArgs = parser.parse_args()
    if cliArgs.bht is None:
        if cliArgs.conf is not None and cliArgs.year is not None:
            cliArgs.bht = 'db/conf/%s/%s%s.bht' % (cliArgs.conf, cliArgs.conf, cliArgs.year)
        else:
            print("ERROR: One of '--bht <bht>' and '--conf <conf> --year <year>' must be specified.")
            parser.print_help()
            exit(-1)
    return cliArgs


def download_doc(args, f=0):
    assert len(args.bht) > 0
    data = {
        'q'     : 'toc:%s:' % args.bht,
        'f'     : f,
        'h'     : 500,
        'format': 'json'
    }
    for _ in range(3):
        for domain in DOMAIN_LIST:
            response = requests.get(URL % domain, params=data, proxies=PROXY, timeout=10, )
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


def parse_doc(hits):
    docConf = {}
    docs = []
    for hit in hits:
        try:
            hit = hit['info']
            if hit['type'] == 'Editorship' or 'publisher' in hit:
                docConf['title'] = hit['title']
                if 'venue' not in hit:
                    docConf['venue'] = hit['key'].split("/")[1].upper()
                else:
                    docConf['venue'] = hit['venue'][0] if isinstance(hit['venue'], list) else hit['venue']
                docConf['year'] = hit['year']
                continue

            oneDoc = {
                'title': hit["title"],
                'venue': hit['venue'],
                'year': hit['year'],
                'url': hit['ee'],
                'pages': hit['pages'] if 'pages' in hit else '0-0',
                'authors': []
            }
            if 'authors' in hit:
                authors = hit['authors']['author']
                if isinstance(authors, dict):
                    authors = [authors]
                for au in authors[:3]:
                    words = au['text'].split()
                    if words[-1].isnumeric():
                        author = " ".join(words[:-1])
                    else:
                        author = " ".join(words)
                    oneDoc['authors'].append(author)
                if len(authors) > 3:
                    oneDoc['authors'].append("et al")
            docs.append(oneDoc)
        except Exception as e:
            print(hit, e)
    docs = sorted(docs, key=lambda x: (x['pages'].split("-")[0], x['title']))
    if len(docConf) == 0:
        docConf['title'] = ''
        docConf['venue'] = ''
        docConf['year'] = ''
    return docConf, docs


def write_to_md(docConf, docs, template, filepath):
    lines = []
    for oneDoc in docs:
        pages = '' if oneDoc['pages'] == '0-0' else "%s." % oneDoc['pages']
        ref = "%s. %s in %s(%s' %s). %s [paper](%s)" % (
            ", ".join(oneDoc['authors']), oneDoc['title'], docConf['title'], oneDoc['venue'], oneDoc['year'][-2:],
            pages, oneDoc['url']
        )
        lines.append(template.format(title=oneDoc['title'], ref=ref))

    with open(filepath, 'w', encoding='utf-8') as mdFile:
        mdFile.write("\n".join(lines))


TEMPLATE = '''
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
        with open("res/temp/%s_%d.json" % (filename, start), 'w') as f:
            f.write(json.dumps(doc))
        temp = pre_parse_doc(doc)
        if temp is None:
            continue
        total, first, count, hits = temp
        # print(first, count, len(hits))
        doc_list.extend(hits)
        start = first + count
        if start >= total:
            break
    conf, items = parse_doc(doc_list)
    print(len(doc_list), len(items))
    write_to_md(conf, items, TEMPLATE, "res/%s.md" % filename)
