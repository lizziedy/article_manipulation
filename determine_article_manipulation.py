import masters_project_helper as mph
import analysis.document_statistics as ds
import analysis.baseline as bl
import news_retrieval.news_url_retriever as nur
import news_retrieval.news_getter as ng
import news_retrieval.collect_word_counts as cwc
import questionnaires.survey_creator as sc
import questionnaires.create_test_set as cts

def get_articles():
    nur.retrieve_news_urls()
    ng.get_all_articles()
    cwc.get_word_counts()

def do_baseline_analysis():
    bl.get_baselines()
    ds.add_sentiments()
    ds.add_manipulation()

def create_questionnaires():
    sc.create_surveys(topics=['education'], year_range=range(2010, 2012))

def create_or_expand_test_set():
    cts.create_test_articles()

def assign_reviewers_to_questionnaires():
    pass

if __name__ == '__main__':
    print("Hello!")
    #get_articles()
    #do_baseline_analysis()
    create_questionnaires()
