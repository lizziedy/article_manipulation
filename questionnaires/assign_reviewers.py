from __future__ import print_function
import httplib2
import os
import re
import json
import sys

import google_api_helper as gah
import masters_project_helper as mph

import pdb

SURVEY_DIRECTORY_ID = '0B723H8z8KF1JYnkybk9YTkZaQm8'

def assign_reviewer_to_articles(articles_info, min_assigned_reviewers, max_reviewers, num_articles, reviewer_info):
    if min_assigned_reviewers == max_reviewers:
        print("AT MAXIMUM REVIEWERS")
        sys.exit(0)
        
    articles = []
    for article_info in articles_info.values():
        reviewers = article_info['reviewers']
        if len(reviewers) == min_assigned_reviewers and reviewer_info not in reviewers:
            reviewers.append(reviewer_info)
            articles.append(article_info)
            if len(articles) == num_articles:
                break
    if len(articles) < num_articles:
        articles += assign_reviewer_to_articles(articles_info, min_assigned_reviewers + 1,max_reviewers, num_articles - len(articles), reviewer_info)
    return articles
    
def get_min_assigned_reviewers(articles_info):
    min_assigned_reviewers = sys.maxsize
    for article_info in articles_info.values():
        if len(article_info['reviewers']) < min_assigned_reviewers:
            min_assigned_reviewers = len(article_info['reviewers'])
    return min_assigned_reviewers

def get_test_articles_info(file_path):
    with open(file_path) as f:
        article_info = json.load(f)
    return article_info

def write_test_articles_info(content, file_path):
    output_string = json.dumps(content, indent=2, separators=(',', ': '))
    f = open(file_path, 'w')
    f.write(output_string)
    f.close()
    
def assign_reviewers_to_articles(test_articles_path, num_articles, max_reviewers, reviewers_info):
    test_articles_info = get_test_articles_info(test_articles_path)
    min_assigned_reviewers = get_min_assigned_reviewers(test_articles_info)
    emails = []
    for reviewer_info in reviewers_info:
        print("for reviewer " + str(reviewer_info))
        articles_links = []
        assigned_articles = assign_reviewer_to_articles(test_articles_info,
                                                        min_assigned_reviewers,
                                                        max_reviewers,
                                                        num_articles,
                                                        reviewer_info)
        print("assigned articles:")
        print(str(assigned_articles))
        
        for article in assigned_articles:
            print("creating surveys for")
            print(str(article))
            article_links = create_individualized_survey(article, reviewer_info)
            articles_links.append(article_links)

        email = create_email(reviewer_info, assigned_articles, articles_links)
        print("email:")
        print(email)
        print()
        emails.append(email)
        
    write_test_articles_info(test_articles_info, test_articles_path)
    
    return emails

def create_email(reviewer_info, articles, links):
    email_str_list = []
    email_str_list.append("Subject: News Article Questionnaires for Lizzie's Master's Project\n\n")
    email_str_list.append("Hi " + reviewer_info['name'].split(' ')[0] + ",\n\n")
    email_str_list.append("Thanks for doing this! Below you will find a link to instructions, and then links to articles and their associated questionnaires. Each questionnaire should take between 10 and 30 minutes to complete. If you are unable to complete the questionnaires by March 27, please let me know which ones you were not able to complete. If you were able to complete all of the questionnaires and are interested in doing more, let me know!\n\n")
    email_str_list.append("Best,\n")
    email_str_list.append("Lizzie\n\n")
    
    email_str_list.append("Instructions:\n")
    email_str_list.append("https://docs.google.com/document/d/1Idrx8tQkghCPjEkymNJGNyd4dorTBmBJRBxrpRwRtMg/edit?usp=sharing\n\n")

    email_str_list.append("Questionnaires:\n\n")

    for i in range(len(articles)):
        email_str_list.append(articles[i]['title'] + "\n")
        email_str_list.append("Article: " + links[i]['article_link'] + "\n")
        email_str_list.append("Questionnaire: " + links[i]['survey_link'] + "\n\n")

    return ''.join(email_str_list)
    

def create_individualized_survey(article_info, reviewer_info):
    article_name = mph.get_article_name(article_info)
    article_path = mph.get_article_path(article_info)
    topic = mph.get_article_topic(article_info)
    
    topic_folder = gah.get_drive_object(topic, SURVEY_DIRECTORY_ID, gah.DRIVE_FOLDER_TYPE)
    folder =gah.get_drive_object(article_name, topic_folder['id'], gah.DRIVE_FOLDER_TYPE)
    survey_file = gah.get_drive_object(article_name, folder['id'], gah.DRIVE_SPREADSHEET_TYPE)
    article_file = gah.get_drive_object(article_name, folder['id'], gah.TEXT_TYPE)
    
    reviewer_name = reviewer_info['name'].replace(" ", "_")
    new_name = reviewer_name + "_" + article_name
    new_file = gah.copy_drive_object(survey_file['id'], new_name)
    
    gah.change_drive_object_permissions(new_file['id'], 'writer', 'anyone')
    gah.change_drive_object_permissions(article_file['id'], 'reader', 'anyone')
    
    return {'survey_link': new_file['webViewLink'], 'article_link': article_file['webViewLink']}

def main():
    ## article_path = 'articles/education/access-to-education-challenge-for-ny-immigrants.txt'
    ## article_name = 'access-to-education-challenge-for-ny-immigrants'
    
    ## links = create_individualized_survey({'file_path':article_path}, {'name':'Lizzie Charbonneau'})
    ## print(str(links))

    emails = assign_reviewers_to_articles('articles/test_articles.json',
                                          3, # num articles
                                          3, # max reviewers
                                          [{'name':'Dawn Stapleton'},])

    for email in emails:
        print(email)
        print()
                                          
    
if __name__ == '__main__':
    main()
