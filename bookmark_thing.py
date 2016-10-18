#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import os
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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import pandas as pd
import pickle
import matplotlib.pyplot as plt

def get_bookmark_file():
    __path = os.path.join(os.getenv('LOCALAPPDATA') , 'Google\\Chrome\\User Data\\Default\\Bookmarks')
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
Remove punctuation, convert to lower case, remove start and end spaces and tabs nad encode to utf-8
'''
def clean_string(a_string):
    cleaned_string = a_string.lower().strip()

    for p in list(punctuation):
        cleaned_string = cleaned_string.replace(p,'')

    return cleaned_string.encode('utf-8').decode("utf-8", "ignore")


'''
Parse the site content with Beautiful Soup, avoiding stop words and covert each work to it's
base stemmed form
'''
def tokenize_html_content(content):
    soup = BeautifulSoup(content, 'html.parser')

    logging.debug('title %s' % soup.title)

    # count words skipping stop words
    site_words = []

    # tags = soup.find_all(['p', 'a', 'h1', 'h2', 'h3', 'h4'])
    tags = soup.find_all(['p','title','h1', 'h2', 'h3', 'h4','pre','a'])


    for tag in tags:

        if None is tag.string:
            continue

        # print(tag)
        #logging.debug(tag.string)

        cleaned_string = clean_string(tag.string)

        for word in word_tokenize(cleaned_string):
            if valid_word(word):
                site_words.append(word)


    stemmed_site_words = [stemmer.stem(t) for t in site_words]

    #logging.debug(stemmed_site_words)

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

    html_documents = []
    urls = []

    stemmer = SnowballStemmer("english")

    stop_words = get_stop_words('en')
    stop_words.append(None)
    stop_words.extend(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'])

    #logging.basicConfig(filename='bookmark.log',
    #                    filemode='w',
    #                    level=logging.DEBUG,
    #                    format='%(levelname)s:%(message)s')

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler('bookmark.log', 'w', 'utf-8')
    handler.setFormatter = logging.Formatter('%(levelname)s:%(message)s')
    # or %(name)-12s: %(levelname)-8s %(message)s
    # or %(asctime)s %(name)-12s %(levelname)-8s %(message)s
    root_logger.addHandler(handler)

    root_logger.info('Starting bookmark analysis.')

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

    root_logger.info('Total bookmarks found: %s' % len(bookmarks_list))

    # TODO remove duplicates

    #bookmarks_list = [{'url':'http://www.sitepoint.com/author/agervasio/'},
    #                  {'url':'http://docs.python-guide.org/en/latest/dev/virtualenvs/'}]


    root_logger.debug('Using stopwords:')
    root_logger.debug(stop_words)

    most_common_words = []


    if os.path.isfile('pickle_html_documents.p'):
        html_documents = pickle.load(open("pickle_html_documents.p", "rb"))
        urls = pickle.load(open("pickle_urls.p", "rb"))
    else:
        for bookmark in bookmarks_list:
            #break
            #print(bookmark.keys())

            if None == bookmark:
                root_logger.debug("Found None bookmark")
                continue

            root_logger.info("")
            root_logger.info("Checking %s" % (bookmark['url']))

            try:
                page = requests.get(bookmark['url'])
            except:
                root_logger.exception('%s not found' % bookmark['url'])
                continue

            if 404 == page.status_code:
                root_logger.info("Not found %s" % bookmark['url'])
                bookmark['status'] = 'not found'
            else:
                root_logger.info("Found %s" % bookmark['url'])
                bookmark['status'] = 'found'

                html_documents.append(page.content.decode('utf-8', "ignore"))
                urls.append(bookmark['url'])

                #site_words = tokenize_html_content(page.content)

                #words_by_count = Counter(site_words).most_common(20)


                #bookmark['most_common'] = words_by_count

                #for word in words_by_count:
                #    root_logger.info(word)
                #    most_common_words.append(word[0])

        #print(bookmarks_list)

        pickle.dump(html_documents, open( "pickle_html_documents.p", "wb" ))
        pickle.dump(urls, open("pickle_urls.p", "wb"))

    #html_documents = html_documents[0:20]
    #urls = urls[0:20]


    # document term matrix / term frequency matrix (dtm)
    # define vectorizer parameters
    tfidf_vectorizer = TfidfVectorizer(max_df=0.8,
                                       max_features=200000,
                                       min_df=0.2,
                                       stop_words='english',
                                       use_idf=True,
                                       ngram_range=(1,3),
                                       tokenizer=tokenize_html_content
                                       )

    tfidf_matrix = tfidf_vectorizer.fit_transform(html_documents)

    terms = tfidf_vectorizer.get_feature_names()

    dist = 1 - cosine_similarity(tfidf_matrix)



    # k-means

    km_cluster = KMeans(n_clusters=10)

    km_cluster.fit(tfidf_matrix)

    clusters = km_cluster.labels_.tolist()



    #next up, create pandas dataframe and visualizations

    bookmarks = {'url': urls, 'cluster': clusters}

    frame = pd.DataFrame(bookmarks, index = [clusters], columns = ['url', 'cluster'])

    print(frame['cluster'].value_counts())

    #grouped = frame['????????']

    from sklearn.manifold import MDS

    MDS()
    mds = MDS(n_components=2, dissimilarity="precomputed", random_state=1)

    pos = mds.fit_transform(dist)  # shape (n_components, n_samples)

    print(type(pos))
    xs, ys = pos[:, 0], pos[:, 1]

    print(pos)

    #visualize clusters

    df = pd.DataFrame(dict(x=xs, y=ys, label=clusters, url=urls))
    groups = df.groupby('label')

    fig, ax = plt.subplots(figsize=(17, 9))  # set size
    ax.margins(0.05)  # Optional, just adds 5% padding to the autoscaling

    print(groups)

    for name, group in groups:
        print(name)
        ax.plot(group.x, group.y, marker='o', linestyle='', ms=12,
                #label=cluster_names[name], color=cluster_colors[name],
                mec='none')
        ax.set_aspect('auto')
        ax.tick_params( \
            axis='x',  # changes apply to the x-axis
            which='both',  # both major and minor ticks are affected
            bottom='off',  # ticks along the bottom edge are off
            top='off',  # ticks along the top edge are off
            labelbottom='off')
        ax.tick_params( \
            axis='y',  # changes apply to the y-axis
            which='both',  # both major and minor ticks are affected
            left='off',  # ticks along the bottom edge are off
            top='off',  # ticks along the top edge are off
            labelleft='off')

    ax.legend(numpoints=1)  # show legend with only 1 point

    # add label in x,y position with the label as the film title
    #for i in range(len(df)):
    #   ax.text(df.ix[i]['x'], df.ix[i]['y'], df.ix[i]['url'], size=8)

    plt.show()  # show the plot





