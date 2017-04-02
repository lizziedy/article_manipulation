import http.client, urllib.request, urllib.parse, urllib.error, base64, json, requests
import os

from bs4 import BeautifulSoup

import datetime
import dateutil.parser
from dateutil.relativedelta import relativedelta

import random

# installed http://www.nltk.org/
# instsalled beautiful soup
# installed python-dateutil

SUBSCRIPTION_KEY = 'abbb1689b20740acba34aae57373181c'

def export_urls(search_term, website, start_year, end_year, out_file):
    delta = 3

    month_delta = relativedelta(months=delta)

    urls = []
    
    for year in range(start_year, end_year):
        for month in range(1, 12, delta):
            url_info = {}
            start_date = datetime.datetime(year, month, 1)
            end_date = start_date + month_delta
            news_urls = get_search_urls(search_term, 60, (start_date, end_date), website)

            url_info['start_date'] = str(start_date)
            url_info['end_date'] = str(end_date)
            url_info['urls'] = news_urls

            urls.append(url_info)

    query_info = {}
    query_info['search_term'] = search_term
    query_info['website'] = website
    query_info['start_year'] = start_year
    query_info['end_year'] = end_year
    query_info['month_delta'] = delta
    query_info['urls'] = urls

    print(query_info)

    output_string = json.dumps(query_info, indent=2, separators=(',', ': '))
    f = open(out_file, 'w')
    f.write(output_string)
    f.close()

    return query_info
    

def get_search_urls(search_term, retrieve_count=10, time_range=None, website=None):
    """ Queries the Bing search engine and returns a list of urls.

    Keyword arguments:
    search_term -- a single word search term to search Bing for.
    retrieve_count -- (optional - defaults to 10) the number of hits to retrieve from the
      search engine.
    select_count -- (optional - defaults to 10) the number of randomly selected hits to
      return.
    time_range -- (optional - defaults to None) a tuple (datetime, datetime) used to
      determine the date range of hits to return. The first eleement in the tuple is the
      start time. The second element in the tuple is the end time. The start time must
      preceed the end time.
    website -- (optional - defaults to None) the website to search within.
    """
    query_params = get_query_params(search_term, retrieve_count, time_range, website)

    data = query_bing(query_params)
        
    urls = parse_urls(data)

    return urls

def get_query_params(search_term, retrieve_count, time_range, website):
    query_params = {
        'offset': '0',
        'mkr': 'en-us',
        'safesearch': 'Moderate',
        'count': str(retrieve_count),
    }

    query_string = ''
    if website:
        query_string += 'site:' + website + ' '
    query_string += 'intitle:' + search_term + " " + search_term
    query_params['q'] = query_string

    if time_range:
        start = days_since_epoch(time_range[0])
        end = days_since_epoch(time_range[1])
        filter_string = 'ex1:"ez5_' + str(start) + '_' + str(end) +'"'
        query_params['filters'] = filter_string

    return query_params

def query_bing(query_params):
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY,
    }

    url_encoded_params = urllib.parse.urlencode(query_params)

    try:
        conn = http.client.HTTPSConnection('api.cognitive.microsoft.com')
        conn.request("GET", "/bing/v5.0/search?%s" % url_encoded_params, '', headers)
        response = conn.getresponse()
        jdata = response.readall().decode('utf-8')
        conn.close()
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

    return json.loads(jdata)  

def parse_urls(data):
    urls = []
    for page_data in data['webPages']['value']:
        redirect_url = page_data['url']
        url_index = redirect_url.index('r=http') + 2
        end_index = redirect_url.index('&p=')
        url = urllib.parse.unquote(redirect_url[url_index:end_index])
        if url != "http://www.foxnews.com/":
            urls.append(url)

    return urls

def random_subset(subset_count, current_list):
    random.seed()

    if subset_count < len(current_list):
        rand_subset = []
        for _ in range(0, subset_count):
            rand_int = random.randint(0, len(current_list)-1)
            rand_subset.append(current_list[rand_int])
            del(current_list[rand_int])
    else:
        rand_subset = current_list
        current_list = []

    return (rand_subset, current_list)
            

def days_since_epoch(date):
    epoch = datetime.datetime(1970,1,1)
    seconds = (date - epoch).total_seconds()
    days = int(seconds / 60 / 60 / 24)
    return days

def retrieve_news_urls(topics = ['education', 'stock', 'immigration'], year_start=2007, year_end=2017, base_directory='websites', news_source = 'foxnews.com'):
    if not os.path.exists(base_directory):
        os.makedirs(base_directory)
    for topic in topics:
        outpath = os.path.join(base_directory, topic + '_' + str(year_start) + '_' + str(year_end) + '.json')
        export_urls(topic, news_source, year_start, year_end, outpath)

if __name__ == '__main__':
    query_info = export_urls('education', 'foxnews.com', 2016, 2017, 'education_2016_2017.json')

