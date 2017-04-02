from __future__ import print_function
import httplib2
import os
import re
import json

import pdb

PARAGRAPH_RE = re.compile("^P\d+$")
SENTENCE_RE = re.compile("^P\d+S\d+$")
SENTENCE_ONLY_RE = re.compile("^S\d+$")
ARTICLE_RE = re.compile("^Article$")

ID = 'Identifier'
NA = 'Not Applicable'
EMO_1 = 'Primary Emotion'
EMO_2 = 'Secondary Emotion'
SENT = 'Sentiment'
OPINION = 'Opinion Stated as Fact'
GEN_ATTR =  'Generalized Attribution'
QUOTE = 'Quote Used or Referenced'
NON_NEUT = 'Non-Neutral Word Used'
SUBJ_OBJ = 'Subjective, Objective, or Neither'
PERS_MAN = 'Persuasive, Manipulative, or Neither'

def apply_function_to_article_metadata(start_year, end_year, topics, func):
    '''
    start_year inclusive
    end_year non-inclusive
    '''
    for topic in topics:
        for year in range(start_year, end_year):
            with open('articles/' + topic + '/' + str(year) + '_' + str(year+1) + '.json') as f:
                file_metadata_dict = json.load(f)

            for file_metadata in file_metadata_dict.values():
                func(file_metadata)

def get_article_name(article_info):
    article_name = os.path.splitext(os.path.basename(article_info['file_path']))[0]
    return article_name

def get_article_path(article_info):
    return article_info['file_path']

def get_article_topic(article_info):
    path_list = article_info['file_path'].split(os.sep)
    return path_list[1]

def read_json(file_path):
    with open(file_path) as f:
        return json.load(f)

def read_file(file_path):
    with open(file_path) as read_file:
        text = read_file.read()
    return text

def write_json(content, file_path):
    output_string = json.dumps(content, indent=2, separators=(',', ': '))
    f = open(file_path, 'w')
    f.write(output_string)
    f.close()

def print_json(content):
    output_string = json.dumps(content, indent=2, separators=(',', ': '))
    print(output_string)

def parse_article(article_text):
    '''
    Gets the id of the article.
    Parses the article text that is tagged with paragraph and sentence identifiers into a dictionary.
    Returns: article_id, article_dict
    '''
    article_id = re.match('Id: (.*)', article_text).group(1)
    
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

    return article_id, article_dict
