from __future__ import print_function
import httplib2
import os
import re
import json
import time

from apiclient import discovery
from apiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import rate_limiter

import google_api_helper as gah
import masters_project_helper as mph

import pdb

#SURVEY_DIRECTORY_ID = '0B723H8z8KF1JYnkybk9YTkZaQm8'
SURVEY_DIRECTORY_ID = '0B723H8z8KF1JaDF5LWV0RzR0aWs'
QUESTIONNAIRE_TEMPLATE_ID = '1jW78-nS9RIPMPGKne-di0AYS0ClWl6HzfDMIyVKY9lE'

def get_article_ids(file_path):
    with open(file_path) as f:
        article_text = f.read()
    
    article_regex = re.compile('\[\[(P\d+)(S\d+)\]\](.*?)(?=\[\[)')
    article_ids = []
        
    start_index = article_text.index('[[')
    index = 0
    previous_p_num = ''
    previous_s_num = ''
    while True:
        match = article_regex.search(article_text, index)

        if not match:
            break

        p_num = match.group(1)
        s_num = match.group(2)

        # add paragraph number for previous paragraph if there were 3 or more sentences.
        if p_num != previous_p_num and previous_s_num and int(previous_s_num[1:]) > 2:
            if previous_p_num:
                article_ids.append(previous_p_num)

        previous_s_num = s_num
        previous_p_num = p_num
        
        article_ids.append(p_num + s_num)

        index = match.span()[1] # the match span are the indices in 'article_text' for the match

    # add last paragraph marker if tere were 3 or more sentences
    if int(s_num[1:]) > 2:
        if p_num:
            article_ids.append(p_num)

    # add article identifier
    article_ids.append("Article")
        
    return article_ids

def create_survey(article_info, topic_folder_id, add_article=False):
    article_path = mph.get_article_path(article_info)
    article_name = mph.get_article_name(article_info)
    folder_id = gah.get_or_create_drive_object(article_name, topic_folder_id, gah.DRIVE_FOLDER_TYPE).get('id')
    
    print("Creating file " + article_name)
    file_id = gah.get_or_create_drive_object(article_name, folder_id, gah.DRIVE_SPREADSHEET_TYPE).get('id')
    print("Done creating file " + article_name)

    print("Copying template")
    sheet = gah.copy_sheet(file_id, QUESTIONNAIRE_TEMPLATE_ID)
    print("Deleting other sheets")
    gah.delete_all_other_sheets(file_id, sheet.get('sheetId'))
    print("Renaming sheet")
    gah.rename_sheet(file_id, sheet.get('sheetId'))
    print("Done copying template")

    print("Adding article ids")
    article_ids = get_article_ids(article_path)
    gah.add_sheet_column_data(file_id, 'A', 2, article_ids, 'Questionnaire')
    print("Done adding article ids")

    if add_article:
        print("Adding article")
        gah.add_file_to_drive(article_name, article_path, folder_id, gah.TEXT_TYPE)
        print("Done adding article")

    print()

def create_surveys_for_topic_and_year(topic, year, base_article_dir='articles'):
    errors = []

    topic_folder_id = gah.get_or_create_drive_object(topic, SURVEY_DIRECTORY_ID, gah.DRIVE_FOLDER_TYPE).get('id')
    print()

    for year in range(2007, 2017):
        with open(base_article_dir + '/' + topic + '/' + str(year) + '_' + str(year+1) + '.json') as f:
            file_metadata_dict = json.load(f)


        for file_metadata in file_metadata_dict.values():
            create_survey(file_metadata, topic_folder_id, add_article=True)
            ## try:
            ##     print("YEAR: " + str(year))
            ##     print()

            ##     create_survey(file_metadata, topic_folder_id, add_article=True)

            ##     print()
            ## except Exception as e:
            ##     error = create_error(e, file_metadata, year)
            ##     errors.append(error)

            ##     print(str(e))
            ##     time.sleep(2)
                
    return errors

def create_error(exception, article_info, year):
    error = {}
    error['id'] = article_info['id']
    error['article_name'] = mph.get_article_name(article_info)
    error['year'] = year
    error['error'] = str(exception)
    return error
        
def create_surveys(topics = ['immigration', 'education', 'stock'],
                   year_range=range(2007, 2017),
                   base_article_dir='articles'):

    all_errors = []

    for topic in topics:
        for year in year_range:
            errors = create_surveys_for_topic_and_year(topic, year, base_article_dir)
            all_errors += errors

    limit = 5
    while len(all_errors) > 0 or limit:
        print()
        print()
        print("REDOING ERRORS")
        print()
        print()
        all_errors = redo_errors(all_errors, base_article_dir)
        limit -= 1

    mph.write_json(errors, 'write_errors.txt')

def redo_errors_from_file(error_input_file):
    error_file = 'write_errors.txt'
    articles = []
    try:
        with open(error_file) as f:
            errors = json.load(f)
    except Exception as e:
        print(e)

    limit = 5
    while len(errors) > 0 or limit:
        limit -=1
        errors = redo_errors(errors)

    mph.write_json(errors, 'write_errors.txt')

def redo_errors(errors, base_article_dir='articles'):
    errors = []
    file_metadata_dict = {}
    
    year = 0
    old_topic = ''
    
    for article in errors:
        topic = mph.get_article_topic(article)

        # only re-retrieve the metadata if we need to
        if year != article['year'] or old_topic != topic:
            year = article['year']
            old_topic = topic
            
            topic_folder_id = gah.get_or_create_drive_object(topic, SURVEY_DIRECTORY_ID, gah.DRIVE_FOLDER_TYPE).get('id')
            with open(base_article_dir + '/' + topic + '/' + str(year) + '_' + str(year+1) + '.json') as f:
                file_metadata_dict = json.load(f)

        # grab the particular metadata that errored out
        file_metadata = file_metadata_dict[article['id']]
        try:
            print("YEAR: " + str(year))
            print()
            create_survey(file_metadata, topic_folder_id, add_article=True)
            print()
        except Exception as e:
            error = create_error(e, file_metadata, year)
            errors.append(error)

            print(str(e))

            time.sleep(2)

    return errors
    
def main():
    #create_surveys()
    redo_errors()
    
if __name__ == '__main__':
    main()
