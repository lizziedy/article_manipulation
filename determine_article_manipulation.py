import masters_project_helper as mph
import analysis.document_statistics as ds
import analysis.baseline as bl
import news_retrieval.news_url_retriever as nur
import news_retrieval.news_getter as ng

def get_articles():
    nur.retrieve_news_urls()
    ng.get_all_articles()
    

def do_baseline_analysis():
    bl.get_baselines()
    ds.add_sentiments()
    ds.add_manipulation()

if __name__ == '__main__':
    print("Hello!")
    #do_baseline_analysis()
    #get_articles()
