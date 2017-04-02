import copy
import random
import json

def get_articles(article_file):
    '''
    returns a list of articles with its metadata from the file
    '''
    articles = {}
    try:
        with open(article_file) as f:
            articles = json.load(f)
    except Exception as e:
        # file does not yet exist
        print(e)

    return articles

def write_word_counts(word_counts, word_count_file):
    output_string = json.dumps(word_counts, indent=2, separators=(',', ': '))
    f = open(word_count_file, 'w')
    f.write(output_string)
    f.close()

def get_article_word_count(article_path):
    article_path = article_path.replace('articles/', 'baseline/')
    article_path = article_path.replace('.txt', '.json')

    with open(article_path) as f:
        article_info = json.load(f)

    return article_info['word_count']

def get_word_counts():
    topics = ['immigration', 'stock', 'education']
    years = range(2007, 2017)
    
    for topic in topics:
        for year in years:
            in_file_path = 'articles/' + topic + '/' + str(year) + '_' + str(year + 1) + '.json'
            out_file_path = 'articles/' + topic + '/word_counts_' + str(year) + '_' + str(year + 1) + '.json'

            word_counts = {}
            articles = get_articles(in_file_path)

            for article_id, article_info in articles.items():
                try:
                    word_count = get_article_word_count(article_info['file_path'])
                    word_counts[article_id] = {'file_path': article_info['file_path'],
                                               'title': article_info['title'],
                                               'id': article_id,
                                               'word_count': word_count}
                except Exception as e:
                    print(year)
                    print(article_info['file_path'])
                    print(str(e))

            write_word_counts(word_counts, out_file_path)

def average_word_counts():
    topics = ['immigration', 'stock', 'education']
    years = range(2007, 2017)

    article_count = 0
    word_count_sum = 0
    
    for topic in topics:
        for year in years:
            file_path = 'articles/' + topic + '/word_counts_' + str(year) + '_' + str(year + 1) + '.json'
            
            articles = get_articles(file_path)

            for article_id, article_info in articles.items():
                article_count += 1
                word_count_sum += article_info['word_count']

    print(word_count_sum / float(article_count))


if __name__ == "__main__":
    #get_word_counts()
    average_word_counts()
