'''
Purpose is to transform the baseline statistics to match the format of the statistics
retrieved from survey takers.
'''

import os
import nltk.data
from nltk import sentiment
import re
from analysis.emolex import EmoSentFinder
import json
import pdb
import operator
import random
import copy

import masters_project_helper as mph

def get_baseline(article_info):
    topic = mph.get_article_topic(article_info)
    article_name = mph.get_article_name(article_info)

    baseline = mph.read_json('baseline/' + topic + '/' + article_name + '.json')

    return baseline

def get_max_count(sorted_pairs):
    max_num = sorted_pairs[0][1]
    max_count = 0

    if max_num == 0:
        return max_count
    
    for sorted_pair in sorted_pairs:
        if sorted_pair[1] == max_num:
            max_count += 1
        else:
            break

    return max_count

def choose_random_max(sorted_pairs):
    max_num = sorted_pairs[0][1]

    rand_list = []
    for sorted_pair in sorted_pairs:
        if sorted_pair[1] == max_num:
            rand_list.append(sorted_pair[0])

    return random.choice(rand_list)

def transform_concept(concept):
    if concept == 'joy':
        return 'Happiness'
    
    if concept.startswith('very '):
        concept = concept[5:]
        
    return concept.title()

def select_max_pair(items, none_name = 'None'):
    sorted_pairs = sorted(items.items(), key = operator.itemgetter(1), reverse=True)
    max_count = get_max_count(sorted_pairs)

    pair_name = none_name
    # if all of the items are the same, we don't have any information so we go with 'none'
    if max_count != len(sorted_pairs):
        if max_count == 1:
            pair_name = sorted_pairs[0][0]
        elif max_count > 1:
            pair_name = choose_random_max(sorted_pairs)

    return pair_name

def get_primary_and_secondary_emotions(emotions):
    emo_1 = 'None'
    emo_2 = 'None'

    emotions = copy.deepcopy(emotions)
    emo_1 = select_max_pair(emotions)
    
    emotions.pop(emo_1, None)
    emo_2 = select_max_pair(emotions)

    return emo_1, emo_2

def get_sentiment(sentiments):
    sent = select_max_pair(sentiments, 'Neutral')
    return sent

def get_subjective_objective(subj_obj):
    return subj_obj

def get_persuasive_manipulative(pers_man):
    return pers_man

def add_manipulative_persuasive(dict, pers_man):
    dict[mph.PERS_MAN] = transform_concept(pers_man)

    if pers_man == 'manipulative':
        dict[mph.PERS_NEI_MAN] = 'Manipulative'
        dict[mph.NEI_PERS_MAN] = 'Manipulative or Persuasive'
    elif pers_man == 'persuasive':
        dict[mph.PERS_NEI_MAN] = 'Neither or Persuasive'
        dict[mph.NEI_PERS_MAN] = 'Manipulative or Persuasive'
    elif pers_man == 'neither':
        dict[mph.PERS_NEI_MAN] = 'Neither or Persuasive'
        dict[mph.NEI_PERS_MAN] = 'Neither'

def transform_statistics(baseline_stats, component_id):
    emo_1, emo_2 = get_primary_and_secondary_emotions(baseline_stats['emotions_counting_negation'])

    sent = get_sentiment(baseline_stats['sentiments_counting_negation'])

    ## emo_1, emo_2 = get_primary_and_secondary_emotions(baseline_stats['emotions'])

    ## sent = get_sentiment(baseline_stats['sentiments'])
    
    subj_obj = get_subjective_objective(baseline_stats['subjective_or_objective'])

    pers_man = get_persuasive_manipulative(baseline_stats['manipulative_or_persuasive'])
    
    new_stats =  {mph.EMO_1: transform_concept(emo_1),
                  mph.EMO_2: transform_concept(emo_2),
                  mph.SENT: transform_concept(sent),
                  mph.SUBJ_OBJ: transform_concept(subj_obj),
                  mph.NA: False,
                  mph.ID: component_id,
                  'old': baseline_stats}
    add_manipulative_persuasive(new_stats, get_persuasive_manipulative(baseline_stats['manipulative_or_persuasive']))
    
    return new_stats

def transform_baseline(baseline):
    tb = {}
    
    for paragraph_id, paragraph in baseline.items():
        if mph.PARAGRAPH_RE.match(paragraph_id): # we're actually looking at a paragraph
            for sentence_id, sentence in paragraph.items():
                if mph.SENTENCE_ONLY_RE.match(sentence_id):
                    component_id = paragraph_id + sentence_id
                    stats = transform_statistics(sentence, component_id)
                    tb[component_id] = stats

            component_id = paragraph_id
            stats = transform_statistics(paragraph, component_id)
            tb[component_id] = stats

    component_id = 'Article'
    stats = transform_statistics(baseline, component_id)
    tb[component_id] = stats

    return tb

def transform_baselines(test_article_path='articles/test_articles.json',
                        output='baseline/test_articles.json'):
    test_articles = mph.read_json(test_article_path)

    baselines = {}
    
    for article_id, article_info in test_articles.items():
        baseline = get_baseline(article_info)
        transformed_baseline = transform_baseline(baseline)
        mph.print_json(transformed_baseline)
        baselines[article_id] = transformed_baseline

    mph.write_json(baselines, output)
    

def main():
    test_articles = mph.read_json('articles/test_articles.json')

    baselines = {}
    
    for article_id, article_info in test_articles.items():
        baseline = get_baseline(article_info)
        transformed_baseline = transform_baseline(baseline)
        mph.print_json(transformed_baseline)
        baselines[article_id] = transformed_baseline

    mph.write_json(baselines, 'baseline/test_articles.json')

if __name__ == '__main__':
    main()
