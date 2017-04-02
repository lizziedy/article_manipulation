import copy
import random
import json
import masters_project_helper as mph

MAX_WORD_COUNT = 562 # determined by looking at average word counts across articles

def get_articles_under_word_count(article_file, word_count_file):
    articles = get_articles(article_file)
    word_counts = get_articles(word_count_file)

    return_articles = {}

    for article_id, word_count_info in word_counts.items():
        if word_count_info['word_count'] < MAX_WORD_COUNT and word_count_info['word_count'] > 100:
            return_articles[article_id] = articles[article_id]
            return_articles[article_id]['word_count'] = word_count_info['word_count']

    return return_articles

def get_articles(article_file):
    '''
    returns a list of articles with its metadata from the file
    '''
    articles = {}
    try:
        articles = mph.read_json(article_file)
    except Exception as e:
        print(article_file + " does not yet exist. Returning empty file set.")

    return articles

def remove_test_articles(articles, test_articles):
    '''
    grabs all the articles from the article listing files (with appropriate metadata) and
    removes articles that already exist in the test_articles_file.
    '''
    non_test_articles = copy.copy(articles)
    
    for key, value in test_articles.items():
        non_test_articles.pop(key, None)

    return non_test_articles

def select_random_articles(articles, num_to_select):
    '''
    returns a random array of num_to_select articles from article_list.
    '''
    random_articles = {}
    random_keys = random.sample(list(articles), num_to_select)

    for key in random_keys:
        article = articles[key]
        article['reviewers'] = []
        random_articles[key] = article

    return random_articles

def create_test_articles(topics = ['immigration', 'stock', 'education'], year_range = range(2007, 2017), test_file_path = 'articles/test_articles.json', base_article_path = 'articles', num_new_test_articles=40):
    '''
    adds num_new_test_articles test articles to the file list of test articles
    '''
    random.seed()
    
    test_articles = get_articles(test_file_path)

    all_articles = {}
    for topic in topics:
        for year in year_range:
            file_path = base_article_path + '/' + topic + '/' + str(year) + '_' + str(year + 1) + '.json'
            word_count_file_path = base_article_path +'/' + topic + '/word_counts_' + str(year) + '_' + str(year + 1) + '.json'
            all_articles.update(get_articles_under_word_count(file_path, word_count_file_path))

    non_test_articles = remove_test_articles(all_articles, test_articles)
    new_test_articles = select_random_articles(non_test_articles, num_new_test_articles)
    test_articles.update(new_test_articles)
    mph.write_json(test_articles, test_file_path)
    return test_articles

if __name__ == "__main__":
    test_articles = create_test_articles(40)
    print("total of " + str(len(test_articles)) + " test articles")
