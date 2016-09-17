import os
import io
import json
import requests
from bs4 import BeautifulSoup


__path = 'C:\\Users\\Hugo Alvarado\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Bookmarks'
file = io.open(__path, 'r', encoding='utf-8')


class Bookmark(object):
    def __init__(self):
        pass


class ChromeFSBookmark(object):
    def __init__(self):
        # Chrome bookmark path in win 10
        self.__path = 'C:\\Users\\Hugo Alvarado\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Bookmarks'

        # os.path.isfile

    def contents(self):
        contents = ''

        if os.path.isfile(self.__path):
            file = io.open(self.__path, 'r', encoding='utf-8')
            contents = file.read()
            file.close()

        return contents


# scrappy test spider
# class BookmarkSpider(scrapy.Spider):
#     name = "BookmarkSpider" # Name of the Spider, required value
#     start_urls = ["http://deals.souq.com/ae-en/"]  # The starting url, Scrapy will request this URL in parse
#
#
#     def parse(self, response):
#         for title in response.css('head > title'):
#             yield title




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
        node['name'] = node['name'].encode(encoding='UTF-8')
        return node



if __name__ == '__main__':
    bookmark_data = json.load(file)

    #print(len(bookmark_data['roots']['bookmark_bar']['children'][2]['name']))
    #print(get_bookmark_children(bookmark_data['roots']))

    bookmarks_list = []
    for key,value in bookmark_data['roots'].items():
        if 'sync_transaction_version' != key:
            print(get_bookmark_children( value, bookmarks_list))

   #print(bookmarks_list)
    bookmarks_list = [{'url':'http://www.sitepoint.com/author/agervasio/'},
                      {'url':'http://docs.python-guide.org/en/latest/dev/virtualenvs/'}]

    for bookmark in bookmarks_list:
        #print(bookmark.keys())

        page = requests.get(bookmark['url'])

        if 404 == page.status_code:
            print('not found', bookmark['url'])
            bookmark['status'] = 'not found'
        else:
            print('found:', bookmark['url'])
            bookmark['status'] = 'found'

            soup = BeautifulSoup(page.content, 'html.parser')

            print('title:',soup.title.string.encode(encoding='UTF-8'))
            print(len(soup.find_all(['p','a','h1','h2','h3','h4'])))


            #count words, remove common words
