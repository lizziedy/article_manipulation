import json
import os
import numpy as np
import matplotlib.pyplot as plt
import re

PARAGRAPH_RE = re.compile("^P\d+$")
SENTENCE_RE = re.compile("^S\d+$")
SUBJECTIVE_RE = re.compile("subjective")


def parse_baseline(file_path):
    if file_path.endswith('.DS_Store'):
        return None
    print(file_path)
    with open(file_path) as f:
        file_info = json.load(f)
    return file_info

def get_sent_over_total(baseline_info):
    if float(baseline_info['non_stopword_count']) > 0:
        return baseline_info['sentiment_word_count']/float(baseline_info['non_stopword_count'])
    else:
        return None

def get_sentiment_numbers(file_paths, level="article"):
    sents = []
    for file_path in file_paths:
        for filename in os.listdir(file_path):
            article_info = parse_baseline(file_path + filename)
            if not article_info:
                continue
            if level == "article":
                sent_percent = get_sent_over_total(article_info)
                if sent_percent != None:
                    sents.append(sent_percent)
            else:
                for sub_id, sub_info in article_info.items():
                    if PARAGRAPH_RE.search(sub_id):
                        paragraph_info = sub_info
                        if level == "paragraph":
                            sent_percent = get_sent_over_total(paragraph_info)
                            if sent_percent != None:
                                sents.append(sent_percent)
                        else:
                            for subsub_id, subsub_info in paragraph_info.items():
                                if SENTENCE_RE.search(subsub_id):
                                    sentence_info = subsub_info
                                    sent_percent = get_sent_over_total(sentence_info)
                                    if sent_percent != None:
                                        sents.append(sent_percent)

    sents = np.sort(sents)
    return sents

def graph_occurrences(sentiment_numbers):
    min_num = sentiment_numbers[0]
    max_num = sentiment_numbers[-1]
    step = (max_num - min_num)/20

    sents_index = 0
    xs = []
    ys = []
    
    for i in range(0, 20):
        min_range = i*step + min_num
        max_range = (i+1)*step + min_num
        count = 0

        # assumes sorted sentiment_numbers
        while sents_index < len(sentiment_numbers):
            if sentiment_numbers[sents_index] >= min_range and sentiment_numbers[sents_index] < max_range:
                sents_index += 1
                count += 1
            else:
                xs.append(min_range)
                ys.append(count)
                break

    mean = np.mean(sentiment_numbers)
    std = np.std(sentiment_numbers)

    max_count = np.max(ys)
    
    plt.plot(xs, ys)
    plt.plot((mean, mean), (-10, max_count + 10), 'r')
    plt.plot((mean+std, mean+std), (-10, max_count + 10), 'r')
    plt.plot((mean-std, mean-std), (-10, max_count + 10), 'r')
    plt.plot((mean+std*2, mean+std*2), (-10, max_count + 10), 'r')
    plt.plot((mean-std*2, mean-std*2), (-10, max_count + 10), 'r')
    
    plt.show()
            
def sentiment_info(sentiment_numbers):
    mean = np.mean(sentiment_numbers)
    std = np.std(sentiment_numbers)

    sents_index = 0
    for i in range(-2,3):
        count = 0
        while sents_index < len(sentiment_numbers):
            if sentiment_numbers[sents_index] < mean + std * i:
                count += 1
                sents_index += 1
            else:
                print(str(i) + ": " + str(count))
                break

    print('X: ' + str(len(sentiment_numbers) - sents_index))

    print()
    print('mean: ' + str(mean))
    print('std: ' + str(std))

def add_sentiment_info(content_info, sent_stat, mean_sent, std_sent):
    if sent_stat != None:
        if sent_stat < mean_sent - 2*std_sent:
            content_info['subjective_or_objective'] = 'very objective'
        elif sent_stat < mean_sent - 1*std_sent:
            content_info['subjective_or_objective'] = 'objective'
        elif sent_stat < mean_sent + 1*std_sent:
            content_info['subjective_or_objective'] = 'neither'
        elif sent_stat < mean_sent + 2*std_sent:
            content_info['subjective_or_objective'] = 'subjective'
        else:
            content_info['subjective_or_objective'] = 'very subjective'
    else:
        content_info['subjective_or_objective'] = 'not enough information'            

def add_manipulative_info(content_info):
    if content_info['subjective_or_objective'] == 'very subjective':
        if content_info['sentiments_counting_negation']['negative'] > content_info['sentiments_counting_negation']['positive']:
            top_emotion = 0
            for key, value in content_info['emotions_counting_negation'].items():
                if value > top_emotion:
                    top_emotion = value
            if top_emotion > 0:
                if content_info['emotions_counting_negation']['anger'] == top_emotion or  content_info['emotions_counting_negation']['fear'] == top_emotion:
                    content_info['manipulative_or_persuasive'] = 'manipulative'

        if 'manipulative_or_persuasive' not in content_info:
            content_info['manipulative_or_persuasive'] = 'persuasive'
    else:
        content_info['manipulative_or_persuasive'] = 'neither'
        
def add_manipulative_to_files(file_paths):
    for file_path in file_paths:
        for filename in os.listdir(file_path):
            
            article_info = parse_baseline(file_path + filename)
            if not article_info:
                continue

            add_manipulative_info(article_info)

            if article_info['subjective_or_objective'] == 'very subjective':
                print(filename)
                print(article_info['manipulative_or_persuasive'])
                print(article_info['emotions_counting_negation'])
                print(article_info['sentiments_counting_negation'])
                
            for sub_id, sub_info in article_info.items():
                if PARAGRAPH_RE.search(sub_id):
                    paragraph_info = sub_info
                    add_manipulative_info(paragraph_info)
                    
                    for subsub_id, subsub_info in paragraph_info.items():
                        if SENTENCE_RE.search(subsub_id):
                            sentence_info = subsub_info
                            add_manipulative_info(sentence_info)
                
            with open(file_path + filename, 'w') as f:
                f.write(json.dumps(article_info, indent=2, separators=(',', ': '), sort_keys=True))
            #print('wrote: ' + file_path + filename)
    
        
def add_sentiment_to_files(file_paths, sentiment_numbers, level="article"):
    mean = np.mean(sentiment_numbers)
    std = np.std(sentiment_numbers)
    
    for file_path in file_paths:
        for filename in os.listdir(file_path):
            print(filename)
            print(mean)
            print(std)
            article_info = parse_baseline(file_path + filename)
            if not article_info:
                continue

            if level == "article":
                sent_stat = get_sent_over_total(article_info)
                article_info['sentiment_ratio'] = sent_stat
                add_sentiment_info(article_info, sent_stat, mean, std)
            else:
                for sub_id, sub_info in article_info.items():
                    if PARAGRAPH_RE.search(sub_id):
                        paragraph_info = sub_info
                        if level == "paragraph":
                            sent_stat = get_sent_over_total(paragraph_info)
                            paragraph_info['sentiment_ratio'] = sent_stat
                            add_sentiment_info(paragraph_info, sent_stat, mean, std)
                        else:
                            for subsub_id, subsub_info in paragraph_info.items():
                                if SENTENCE_RE.search(subsub_id):
                                    sentence_info = subsub_info
                                    sent_stat = get_sent_over_total(sentence_info)
                                    sentence_info['sentiment_ratio'] = sent_stat
                                    add_sentiment_info(sentence_info, sent_stat, mean, std)
                
            with open(file_path + filename, 'w') as f:
                f.write(json.dumps(article_info, indent=2, separators=(',', ': '), sort_keys=True))
            #print('wrote: ' + file_path + filename)

def add_sentiments(file_paths = ['baseline/education/', 'baseline/stock/', 'baseline/immigration/']):
    sents = get_sentiment_numbers(file_paths, "article")
    add_sentiment_to_files(file_paths, sents, "article")
    sents = get_sentiment_numbers(file_paths, "paragraph")
    add_sentiment_to_files(file_paths, sents, "paragraph")
    sents = get_sentiment_numbers(file_paths, "sentence")
    add_sentiment_to_files(file_paths, sents, "sentence")

def get_sentiment_graphs(file_paths):
    sents = get_sentiment_numbers(file_paths, "sentence")
    graph_occurrences(sents)
    sents = get_sentiment_numbers(file_paths, "paragraph")
    graph_occurrences(sents)
    sents = get_sentiment_numbers(file_paths, "article")
    graph_occurrences(sents)
    
def add_manipulation(file_paths = ['baseline/education/', 'baseline/stock/', 'baseline/immigration/']):
    add_manipulative_to_files(file_paths)
            
if __name__ == '__main__':
    file_paths = ['baseline/education/', 'baseline/stock/', 'baseline/immigration']
    #add_sentiments(file_paths)
    #add_manipulation(file_paths)
    
    sents = get_sentiment_numbers(file_paths, "sentence")
    graph_occurrences(sents)
    sents = get_sentiment_numbers(file_paths, "paragraph")
    graph_occurrences(sents)
    #sentiment_info(sents)

    ## sents = np.sort(sents)
    ## print(sents)
    ## print('mean: ' + str(np.mean(sents)))
    ## print('std: ' + str(np.std(sents)))
    ## print('var: ' + str(np.var(sents)))
    ## plt.plot(sents)
    ## plt.show()
    
