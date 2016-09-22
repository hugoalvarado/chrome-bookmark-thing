#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from nltk.stem.snowball import SnowballStemmer
from string import punctuation
import re


def get_bookmark_file():
    __path = 'C:\\Users\\Hugo Alvarado\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Bookmarks'
    return io.open(__path, 'r', encoding='utf-8')



'''
Traverse the chrome bookmark data and return the leafs with urls
'''
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

'''
Remove punctuation, convert to lower case, remove start and end spaces and tabs
'''
def clean_string(a_string):
    cleaned_string = a_string.lower().strip()

    for p in list(punctuation):
        cleaned_string = cleaned_string.replace(p,'')

    return cleaned_string


'''
Parse the site content with Beautiful Soup, avoiding stop words and covert each work to it's
base stemmed form
'''
def tokenize_content(content):
    soup = BeautifulSoup(content, 'html.parser')

    #logging.debug('title %s' % soup.title)

    # count words skipping stop words
    site_words = []

    # tags = soup.find_all(['p', 'a', 'h1', 'h2', 'h3', 'h4'])
    tags = soup.find_all(['p','title'])

    for tag in tags:
        # print(tag)
        # print(tag.string)
        if None is tag.string:
            continue

        cleaned_string = clean_string(tag.string)

        for word in word_tokenize(cleaned_string):
            if valid_word(word):
                site_words.append(word)

    stemmed_site_words = [stemmer.stem(t) for t in site_words]
    return stemmed_site_words


'''
Return true if the word token is not a stop word, not a number and longer than 2 characters
'''
def valid_word(word):
    return word not in stop_words and len(word) > 2 and None is not re.search('[a-zA-Z]', word)


'''
Main entry point
'''
if __name__ == '__main__':

    stemmer = SnowballStemmer("english")

    stop_words = get_stop_words('en')
    stop_words.append(None)
    stop_words.extend(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'])

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

    logging.info('Total bookmarks found: %s' % len(bookmarks_list))

    # TODO remove duplicates

    bookmarks_list = [{'url':'http://www.sitepoint.com/author/agervasio/'},
                      {'url':'http://docs.python-guide.org/en/latest/dev/virtualenvs/'}]



    logging.debug('Using stopwords:')
    logging.debug(stop_words)

    most_common_words = []

    for bookmark in bookmarks_list:
        #print(bookmark.keys())

        logging.info("Checking %s" % (bookmark['url']))

        try:
            page = requests.get(bookmark['url'])
        except:
            logging.exception('%s not found' % bookmark['url'])
            continue

        if 404 == page.status_code:
            logging.info("Not found %s" % bookmark['url'])
            bookmark['status'] = 'not found'
        else:
            logging.info("Found %s" % bookmark['url'])
            bookmark['status'] = 'found'

            site_words = tokenize_content(page.content)

            words_by_count = Counter(site_words).most_common(20)


            bookmark['most_common'] = words_by_count

            for word in words_by_count:
                logging.info(word)
                most_common_words.append(word[0])

    #print(bookmarks_list)

