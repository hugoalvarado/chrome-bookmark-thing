import io
import json
import requests
from bs4 import BeautifulSoup
from collections import Counter
import sys
import codecs
import logging
from stop_words import get_stop_words
from nltk import word_tokenize

def get_bookmark_file():
    __path = 'C:\\Users\\Hugo Alvarado\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Bookmarks'
    return io.open(__path, 'r', encoding='utf-8')




def get_bookmark_children(node, url_list):
    if node is None:
        return []

    #if type(node) is str:
        #print(len(node))
        #print(node)
        #return []

    if type(node) is list:
        for child_node in node:
            url_list.append(get_bookmark_children(child_node, url_list))
    elif 'folder' in node['type']:
        get_bookmark_children(node['children'], url_list)
    elif 'url' in node['type']:
        #print(node['url'])
        #print(node)
        node['name'] = node['name']
        return node



if __name__ == '__main__':

    logging.basicConfig(filename='bookmark.log', filemode='w', level=logging.DEBUG, format='%(levelname)s:%(message)s')

    logging.info('Starting bookmark analysis.')

    #avoid encoding warnings
    if sys.stdout.encoding != 'utf8':
        sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf8':
        sys.stderr = codecs.getwriter('utf8')(sys.stderr.buffer, 'strict')

    bookmark_data = json.load(get_bookmark_file())

    bookmarks_list = []
    for key,value in bookmark_data['roots'].items():
        if 'sync_transaction_version' != key:
            get_bookmark_children( value, bookmarks_list)

    logging.info( '%s %s' %('Total bookmarks found: ',len(bookmarks_list)))

    # TODO remove duplicates

    bookmarks_list = [{'url':'http://www.sitepoint.com/author/agervasio/'},
                      {'url':'http://docs.python-guide.org/en/latest/dev/virtualenvs/'}]

    stop_words = get_stop_words('en')
    stop_words.append(None)

    logging.debug('Using stopwords:')
    logging.debug(stop_words)

    for bookmark in bookmarks_list:
        #print(bookmark.keys())

        logging.info(bookmark['url'])
        try:
            page = requests.get(bookmark['url'])
        except:
            logging.exception(bookmark['url'], 'not found')
            continue

        if 404 == page.status_code:
            print('not found', bookmark['url'])
            bookmark['status'] = 'not found'
        else:
            print('found:', bookmark['url'])
            bookmark['status'] = 'found'

            soup = BeautifulSoup(page.content, 'html.parser')

            logging.debug('title:',soup.title)

            # count words skipping stop words
            site_words = []

            #tags = soup.find_all(['p', 'a', 'h1', 'h2', 'h3', 'h4'])
            tags = soup.find_all(['p'])

            for tag in tags:
                #print(tag)
                #print(tag.string)
                if None is tag.string:
                    continue

                for word in word_tokenize(tag.string.lower()):
                    if word not in stop_words and len(word) > 2:
                        site_words.append(word.strip())

            words_by_count = Counter(site_words).most_common(20)

            for word in words_by_count:
                print(word)



