import http.client, urllib.request, urllib.parse, urllib.error, base64, json, requests

from bs4 import BeautifulSoup

import datetime

import dateutil.parser
from dateutil.relativedelta import relativedelta

import hashlib

import os
import re

import nltk.data

import pdb

import masters_project_helper as mph

# installed http://www.nltk.org/
#   after installing, need to download supporting data. open python terminal.
#     # import nltk
#     # nltk.download()
# instsalled beautiful soup
# installed python-dateutil

URLS_TO_IGNORE = [
    "http://nation.foxnews.com",
    "http://radio.foxnews.com",
    "http://latino.foxnews.com",
    "http://insider.foxnews.com",
    "http://www.foxnews.com/on-air/",
    "http://www.foxnews.com/transcript/",
    "http://www.foxnews.com/health/",
    "http://www.foxnews.com/sports/"
    ]

SENTENCE_DETECTOR = nltk.data.load('tokenizers/punkt/english.pickle')
    
def get_articles(json_file, start_year, end_year, output_base_dir):
    with open(json_file) as json_data:
        article_info = json.load(json_data)
    urls_with_dates = article_info['urls']
    topic = article_info['search_term']

    urls_to_use = []
    for urls_with_date in urls_with_dates:
        start_date = dateutil.parser.parse(urls_with_date['start_date'])
        if start_date.year >= start_year and start_date.year < end_year:
            urls_to_use += urls_with_date['urls']

    metadata = output_urls(urls_to_use, topic)
    output_path = os.path.join(output_base_dir, topic, str(start_year) + '_' + str(end_year) + '.json')
    mph.write_json(metadata, output_path)

def output_urls(urls, topic):
    all_metadata = {}
    for url in urls:
        if url == "http://www.foxnews.com/":
            continue

        ignore = False
        for url_to_ignore in URLS_TO_IGNORE:
            if url.startswith(url_to_ignore):
                ignore = True
                break
        if ignore:
            continue
        
        web_text = get_website(url)
        try:
            print("processing " + url)
            (article_text, metadata) = parse_website(web_text, url, topic)
            file_name = metadata['file_path']
        except:
            print("Error parsing " + url)
            continue
        
        if not os.path.exists(os.path.dirname(file_name)):
            try:
                os.makedirs(os.path.dirname(file_name))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        with open(file_name, 'w') as out_file:
            out_file.write(article_text)

        all_metadata[metadata['id']] = metadata

    return all_metadata
    
def get_website(url):
    try:
        response = requests.get(url)
    except Exception as e:
        print(e)
        return
    
    return response.text

def parse_website(web_text, url, topic):
    soup = BeautifulSoup(web_text, 'html.parser')

    id = hashlib.md5(url.encode('utf-8')).hexdigest()

    try:
        category = soup.article.h2.string
    except:
        category = ""

    try:
        title = soup.article.h1.string
    except:
        title = ""

    try:
        date = dateutil.parser.parse(soup.article.time['datetime'])
    except:
        date = None

    try:
        source_org = soup.find_all('meta', {'name' : 'dc.source'})[0]['content']
    except:
        source_org = ""

    p_paragraphs = soup.article.find_all(class_='article-text')[0].find_all('p')
    paragraphs = []
    tag_regex = re.compile('<[^>]*>')
    for p_index, p in enumerate(p_paragraphs):
        paragraph = tag_regex.sub("", str(p))
        if paragraph != None and paragraph != "":
            sentences = SENTENCE_DETECTOR.tokenize(paragraph)
            out_paragraph = ''.join([' [[P' + str(p_index+1) + 'S' + str(s_index+1) + ']]' +
                                     sentence for s_index, sentence in enumerate(sentences)])
            out_paragraph = ''.join([out_paragraph, '[[P' + str(p_index+1) + ']]', '\n'])
            paragraphs.append(out_paragraph)

    article_text = ""
    article_text += "Id: " + id + "\n\n"
    article_text += "Title: " + title + "\n"
    article_text += "Date: " + str(date) + "\n\n"
    article_text += "Article:\n\n"
    for p in paragraphs:
        article_text += p + "\n\n"


    file_title = url[url.rfind('/') + 1:url.rfind('.')]
    file_name = "articles/" + topic + "/"  + file_title + ".txt"

    metadata = {}
    metadata['url'] = url
    metadata['id'] = id
    metadata['title'] = title
    metadata['date'] = str(date)
    metadata['category'] = category
    metadata['source_org'] = source_org
    metadata['file_path'] = file_name

    return (article_text, metadata)

def get_all_articles(topics = ['education', 'stock', 'immigration'], url_base_directory='websites', url_year_range=range(2007, 2017), output_base_dir='articles', year_range = range(2007, 2017)):
    for topic in topics:
        url_file = os.path.join(url_base_directory, topic + '_' + str(url_year_range[0]) + '_' + str(url_year_range[-1] + 1) + '.json')
        for year in year_range:
            get_articles(url_file, year, year + 1, output_base_dir)

if __name__ == '__main__':
    for year in range(2007, 2017):
        get_articles("websites/immigration_2007_2017.json", year, year + 1, 'articles')
    

