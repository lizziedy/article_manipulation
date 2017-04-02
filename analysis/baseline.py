import datetime
import dateutil.parser
from dateutil.relativedelta import relativedelta

import os
import nltk.data
from nltk import sentiment
import re
from analysis.emolex import EmoSentFinder
import json
import pdb

import masters_project_helper as mph

# installed http://www.nltk.org/
#   after installing, need to download supporting data. open python terminal.
#     # import nltk
#     # nltk.download()
# instsalled beautiful soup
# installed python-dateutil

emolex = EmoSentFinder()

def open_article(article_file):
    with open(article_file) as article:
        article_text = article.read()
    return article_text

def parse_article(article_text):
    article_regex = re.compile('\[\[(P\d+)(S\d+)\]\](.*?)(?=\[\[)')
    
    article_dict = {}
        
    start_index = article_text.index('[[')
    index = start_index
    while True:
        match = article_regex.search(article_text, index)

        if not match:
            break
        
        p_num = match.group(1)
        s_num = match.group(2)
        sentence = match.group(3)

        if p_num not in article_dict:
            article_dict[p_num] = {}
        article_dict[p_num][s_num] = {'sentence':sentence}

        index += len(match.group(0))

    return article_dict

def get_article_id(article_text):
    match = re.match('Id: (.*)', article_text)
    return match.group(1)

def get_statistics(article_dict):
    emotions_d_total = {}
    sentiments_d_total = {}
    emotions_counting_negation_d_total = {}
    sentiments_counting_negation_d_total = {}
    sentiment_word_count_d_total = 0
    non_stopword_count_d_total = 0
    word_count_d_total = 0
    has_negation_d = False

    for p_key, sentences in article_dict.items():
        emotions_p_total = {}
        sentiments_p_total = {}
        emotions_counting_negation_p_total = {}
        sentiments_counting_negation_p_total = {}
        sentiment_word_count_p_total = 0
        non_stopword_count_p_total = 0
        word_count_p_total = 0
        has_negation_p = False
        
        for s_key, content in sentences.items():
            content.update(emolex.get_sentence_statistics(content['sentence']))

            add_to_dict(content['emotions'], emotions_p_total)
            add_to_dict(content['sentiments'], sentiments_p_total)
            add_to_dict(content['emotions_counting_negation'], emotions_counting_negation_p_total)
            add_to_dict(content['sentiments_counting_negation'], sentiments_counting_negation_p_total)
            sentiment_word_count_p_total += content['sentiment_word_count']
            non_stopword_count_p_total += content['non_stopword_count']
            word_count_p_total += content['word_count']
            has_negation_p = has_negation_p or content['has_negation']
    
        sentences['emotions'] = emotions_p_total
        sentences['sentiments'] = sentiments_p_total
        sentences['emotions_counting_negation'] = emotions_counting_negation_p_total
        sentences['sentiments_counting_negation'] = sentiments_counting_negation_p_total
        sentences['sentiment_word_count'] = sentiment_word_count_p_total
        sentences['non_stopword_count'] = non_stopword_count_p_total
        sentences['word_count'] = word_count_p_total
        sentences['has_negation'] = has_negation_p

        add_to_dict(emotions_p_total, emotions_d_total)
        add_to_dict(sentiments_p_total, sentiments_d_total)
        add_to_dict(emotions_counting_negation_p_total, emotions_counting_negation_d_total)
        add_to_dict(sentiments_counting_negation_p_total, sentiments_counting_negation_d_total)
        sentiment_word_count_d_total += sentiment_word_count_p_total
        non_stopword_count_d_total += non_stopword_count_p_total
        word_count_d_total += word_count_p_total
        has_negation_d = has_negation_d or has_negation_p

    article_dict['emotions'] = emotions_d_total
    article_dict['sentiments'] = sentiments_d_total
    article_dict['emotions_counting_negation'] = emotions_counting_negation_d_total
    article_dict['sentiments_counting_negation'] = sentiments_counting_negation_d_total
    article_dict['sentiment_word_count'] = sentiment_word_count_d_total
    article_dict['non_stopword_count'] = non_stopword_count_d_total
    article_dict['word_count'] = word_count_d_total
    article_dict['has_negation'] = has_negation_d
            
    return article_dict

def add_to_dict(new_dict, accumulator_dict):
    for key, value in new_dict.items():
        if key in accumulator_dict:
            accumulator_dict[key] += value
        else:
            accumulator_dict[key] = value

def get_neutral_words(article_path):
    article_text = mph.read_file(article_path)
    article_id, article_dict = mph.parse_article(article_text)

    for p_key, sentences in article_dict.items():
        for s_key, content in sentences.items():
            if emolex.get_sentence_neutral_words(content['sentence']):
                print(article_path)
                    
            
def get_article_baseline(article_path, topic):
    article_text = mph.read_file(article_path)
    article_id, article_dict = mph.parse_article(article_text)
    
    article_dict = get_statistics(article_dict)
    article_dict['id'] = article_id

    article_json_name = os.path.splitext(os.path.basename(article_path))[0] + ".json"
    with open('baseline/' + topic + '/' + article_json_name, 'w') as f:
        f.write(json.dumps(article_dict, indent=2, separators=(',', ': '), sort_keys=True))
    print('wrote: ' + article_json_name)

def get_baselines(topics = ['stock', 'immigration', 'education'], year_range = range(2007, 2017)):
    for topic in topics:
        for year in year_range:
            with open('articles/' + topic + '/' + str(year) + '_' + str(year+1) + '.json') as f:
                file_metadata_dict = json.load(f)

            for file_metadata in file_metadata_dict.values():
                # get_neutral_words(file_metadata['file_path'])
                try:
                    get_article_baseline(file_metadata['file_path'], topic)
                except:
                    print('error getting baseline for ' + file_metadata['file_path'])
    
            
if __name__ == '__main__':
    topic = "stock"
    for year in range(2007, 2017):
        with open('articles/' + topic + '/' + str(year) + '_' + str(year+1) + '.json') as f:
            file_metadata_dict = json.load(f)

        for file_metadata in file_metadata_dict.values():
            # get_neutral_words(file_metadata['file_path'])
            try:
                get_article_baseline(file_metadata['file_path'], topic)
            except:
                print('error getting baseline for ' + file_metadata['file_path'])
    
    ## topic = 'stock'
    ## get_article_baseline('articles/stock/after-election-defeats-india-congress-party-takes-stock.txt')
    
    ## topic = 'immigration'
    ## get_article_baseline('articles/immigration/immigration-bill-goes-down.txt')

