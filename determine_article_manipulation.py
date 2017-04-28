import masters_project_helper as mph

import analysis.document_statistics as ds
import analysis.baseline as bl
import analysis.get_reviewer_analysis as gra
import analysis.baseline_match as blm
import analysis.machine_learn_reviews as mlr
import analysis.test_article_features as taf

import news_retrieval.news_url_retriever as nur
import news_retrieval.news_getter as ng
import news_retrieval.collect_word_counts as cwc

import questionnaires.survey_creator as sc
import questionnaires.create_test_set as cts
import questionnaires.assign_reviewers as ar
'''

Getting the articles
--------------------

The articles are retrieved by first getting the urls. The bing api is used with a search term,
a set of query dates, and the news organization to search (in this case, fox news).

Next the articles themselves need to be retrieved and parsed. The http from the urls is
processed into a text format. Each sentence and paragraph are tagged with identifiers to make
labeling as clear as possible. The articles are output along with a summary document for each
year and topic.

Next a set of word counts are determined. This is a post-processing step that could have been
done earlier but wasn't thought of until later so was added at the end so the documents didn't
need to be re-retrieved.


Baseline analysis
-----------------


Creating the questionnaires
---------------------------


Creating the test set and assigning reviewers
---------------------------------------------


Performing analysis on the reviews
----------------------------------


'''

def get_articles():
    nur.retrieve_news_urls()
    ng.get_all_articles()
    cwc.get_word_counts()

def do_baseline_analysis():
    bl.get_baselines()
    ds.add_sentiments()
    ds.add_manipulation()

def create_questionnaires():
    sc.create_surveys()

def create_or_expand_test_set():
    cts.create_test_articles()

def assign_reviewers_to_questionnaires(test_articles_path,
                                       num_articles,
                                       max_num_reviewers_per_article,
                                       reviewers):
    emails = ar.assign_reviewers_to_articles(test_articles_path,
                                        num_articles,
                                        max_num_reviewers_per_article,
                                        reviewers)
    for email in emails:
        print(email)
        print()

def retrieve_reviews():
    gra.get_article_reviews()

def analyze_reviews():
    gra.get_reviewer_agreement_statistics()
    gra.create_master()
    gra.get_other_agreement_statistics('articles/master_reviews.json', 'articles/master_agreement_stats.json')

def analyze_automated_reviews():
    blm.transform_baselines()
    gra.get_other_agreement_statistics('baseline/test_articles.json', 'articles/automated_agreement_stats.json')
    gra.get_other_agreement_statistics('baseline/test_articles.json', 'articles/automated_master_agreement_stats.json', review_path='articles/master_reviews.json', has_reviewers=False)

def do_machine_learning():
    mlr.article_data()
    mlr.train_feature_data()

    # with same dataset
    mlr.create_train_test_sets()
    mlr.article_data_preset()
    mlr.train_feature_data_preset()
    mlr.test_baseline()

    
    
if __name__ == '__main__':
    print("Hello!")
    #get_articles()
    #do_baseline_analysis()
    #create_questionnaires()
    #create_or_expand_test_set()
    #assign_reviewers_to_articles('articles/test_articles.json', 3, 3, [{'name':'Dawn Stapleton'},])
    #retrieve_reviews()
    #analyze_reviews()
    #analyze_automated_reviews()
    #do_machine_learning()
    
    #blm.transform_baselines(output='baseline/test_articles_annotated_results.json', use_annotated_results=True)
    #gra.json_data_to_csv('articles/master_reviews.json', 'articles/master_reviews.csv')
    #gra.json_data_to_csv('baseline/test_articles_annotated_results.json', 'baseline/test_articles_annotated_results.csv')
    #gra.json_data_to_csv('baseline/test_articles.json', 'baseline/test_articles.csv')
    #mlr.create_train_test_sets()

    #master_reviews =  mph.read_json('articles/master_reviews.json')
    #taf.get_article_features("articles/immigration/immigration-bill-goes-down.txt", "immigration", master_reviews)
    #taf.get_test_article_features()
    #mlr.train_feature_data('features/immigration/immigration-bill-goes-down.csv')
    #mlr.train_feature_data(csv_file='features/train_features.csv')
    #mlr.article_data()
    #mlr.train_feature_data_preset(csv_file='features/train_features.csv')
    #mlr.article_data_preset()
    mlr.test_baseline()

    #ds.get_sentiment_graphs(['baseline/education/', 'baseline/stock/', 'baseline/immigration/'])
    #gra.get_reviewer_agreement_statistics()
