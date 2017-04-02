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

import pdb

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
#SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret_drive2.json'
APPLICATION_NAME = 'Survey Creator'

SURVEY_DIRECTORY_ID = '0B723H8z8KF1JYnkybk9YTkZaQm8'
QUESTIONNAIRE_TEMPLATE_ID = '1jW78-nS9RIPMPGKne-di0AYS0ClWl6HzfDMIyVKY9lE'

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

@rate_limiter.RateLimited(1.6)
def create_new_folder(drive_service, folder_name, parent_id):
    file_metadata = {
        'name' : folder_name,
        'mimeType' : 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = drive_service.files().create(body=file_metadata,
                                          fields='id').execute()
    return folder.get('id')

@rate_limiter.RateLimited(1.6)
def create_new_spreadsheet(drive_service, file_name, parent_id):
    file_metadata = {
        'name' : file_name,
        'mimeType' : 'application/vnd.google-apps.spreadsheet',
        'parents': [parent_id]
    }
    file = drive_service.files().create(body=file_metadata,
                                        fields='id').execute()
    return file.get('id')

def get_folder_id(drive_service, folder_name, parent_id):
    page_token = None
    response = drive_service.files().list(q="name='" + folder_name + "'" +
                                            " and " +
                                            "'" + parent_id + "' in parents" +
                                            " and " +
                                            "mimeType='application/vnd.google-apps.folder'",
                                         spaces='drive',
                                         pageToken=page_token).execute()
    if len(response.get('files', [])) > 0:
        return response.get('files', [])[0].get('id')
    return None

def get_spreadsheet_id(drive_service, file_name, parent_id):
    page_token = None
    response = drive_service.files().list(q="name='" + file_name + "'" +
                                            " and " +
                                            "'" + parent_id + "' in parents" +
                                            " and " +
                                            "mimeType='application/vnd.google-apps.spreadsheet'",
                                         spaces='drive',
                                         pageToken=page_token).execute()
    if len(response.get('files', [])) > 0:
        return response.get('files', [])[0].get('id')
    return None

def get_services():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    sheets_service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    drive_service = discovery.build('drive', 'v3', http=http)
    return sheets_service, drive_service

def get_spreadsheet(sheets_service, file_id):
    return sheets_service.spreadsheets().get(spreadsheetId=file_id).execute()

@rate_limiter.RateLimited(1.6)
def delete_all_other_sheets(sheets_service, file_id, keepSheetId):
    spreadsheet = get_spreadsheet(sheets_service, file_id)
    requests = []
    for sheet in spreadsheet.get('sheets'):
        sheetId = sheet.get('properties').get('sheetId')
        if sheetId != keepSheetId:
            requests.append({
                'deleteSheet': {
                    'sheetId':sheetId
                }
            })

    if len(requests) > 0:
        body = {
            'requests': requests
        }
        response = sheets_service.spreadsheets().batchUpdate(spreadsheetId=file_id,
                                                             body=body).execute()
        spreadsheet = get_spreadsheet(sheets_service, file_id)

@rate_limiter.RateLimited(1.6)  
def rename_sheet(sheets_service, file_id, sheet_id):
    requests = []
    requests.append({
        'updateSheetProperties': {
            'properties': {
                'sheetId': sheet_id,
                'title': 'Questionnaire'
            },
            'fields': 'title'
        }
    })    
    body = {
        'requests': requests
    }
    response = sheets_service.spreadsheets().batchUpdate(spreadsheetId=file_id,
                                                         body=body).execute()

@rate_limiter.RateLimited(1.6)
def copy_sheet(sheets_service, file_id):
    sheet = sheets_service.spreadsheets().sheets().copyTo(
        spreadsheetId=QUESTIONNAIRE_TEMPLATE_ID,
        sheetId=0,
        body={"destinationSpreadsheetId": file_id}
        ).execute()
    return sheet

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

@rate_limiter.RateLimited(1.6)
def add_article(drive_service, article_name, article_path, parent_id):
    print("Adding article")
    file_metadata = {
      'name' : article_name,
      'parents':[parent_id]
    }
    media = MediaFileUpload(article_path,
                            mimetype='text/plain')
    file = drive_service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
    print('File ID: %s' % file.get('id'))
    print("Done adding article")

def create_survey(article_path, article_name, folder_id, sheets_service, drive_service):
    print("Creating file " + article_name)
    file_id = get_spreadsheet_id(drive_service, article_name, folder_id)
    if not file_id:
        file_id = create_new_spreadsheet(drive_service, article_name, folder_id)
    print("Done creating file " + article_name)

    print("Copying template")
    sheet = copy_sheet(sheets_service, file_id)
    print("Deleting other sheets")
    delete_all_other_sheets(sheets_service, file_id, sheet.get('sheetId'))
    print("Renaming sheet")
    rename_sheet(sheets_service, file_id, sheet.get('sheetId'))
    print("Done copying template")

    print("Adding article ids")
    article_ids = get_article_ids(article_path)

    body={'range':"Questionnaire!A2:A" + str(2 + len(article_ids)),
          'majorDimension':"COLUMNS",
          'values':[article_ids]}

    result = sheets_service.spreadsheets().values().update(
        spreadsheetId=file_id,
        range='Questionnaire!A2:A' + str(2 + len(article_ids)),
        valueInputOption="RAW",
        body=body).execute()
    print("Done adding article ids")

def get_or_create_folder(drive_service, name, parent_id):
    print("Creating directory " + name)
    folder_id = get_folder_id(drive_service, name, parent_id)
    if not folder_id:
        folder_id = create_new_folder(drive_service, name, parent_id)
    print("Done creating directory " + name)
    return folder_id
        
def create_surveys():
    topic = "immigration"

    error_file = open('write_errors.txt', 'w')
    errors = []

    sheets_service, drive_service = get_services()
    topic_folder_id = get_or_create_folder(drive_service, topic, SURVEY_DIRECTORY_ID)
    print()

    for year in range(2007, 2017):
        with open('articles/' + topic + '/' + str(year) + '_' + str(year+1) + '.json') as f:
            file_metadata_dict = json.load(f)

        
        for file_metadata in file_metadata_dict.values():
            try:
                print("YEAR: " + str(year))
                print()

                article_path = file_metadata['file_path']
                article_name = os.path.splitext(os.path.basename(article_path))[0]

                folder_id = get_or_create_folder(drive_service, article_name, topic_folder_id)

                create_survey(article_path, article_name, folder_id, sheets_service, drive_service)

                #add_article(drive_service, article_name, article_path, folder_id)
                print()
            except Exception as e:
                error = {}
                error['id'] = file_metadata['id']
                error['article_name'] = article_name
                error['year'] = year
                error['error'] = str(e)

                errors.append(error)

                print(str(e))

                time.sleep(2)

    
    error_string = json.dumps(errors, indent=2, separators=(',', ': '))
    error_file.write(error_string)
    error_file.close()

def redo_errors():
    error_file = 'write_errors.txt'
    articles = []
    try:
        with open(error_file) as f:
            articles = json.load(f)
    except Exception as e:
        print(e)

    error_file = open('write_errors.txt', 'w')

    sheets_service, drive_service = get_services()
    topic = 'immigration'
    topic_folder_id = get_or_create_folder(drive_service, topic, SURVEY_DIRECTORY_ID)
    print()

    errors = []
    file_metadata_dict = {}
    year = 0
    for article in articles:
        if year != article['year']:
            year = article['year']
            with open('articles/' + topic + '/' + str(year) + '_' + str(year+1) + '.json') as f:
                file_metadata_dict = json.load(f)

        file_metadata = file_metadata_dict[article['id']]
        try:
            print("YEAR: " + str(year))
            print()

            article_path = file_metadata['file_path']
            article_name = os.path.splitext(os.path.basename(article_path))[0]

            folder_id = get_or_create_folder(drive_service, article_name, topic_folder_id)

            create_survey(article_path, article_name, folder_id, sheets_service, drive_service)

            #add_article(drive_service, article_name, article_path, folder_id)
            print()
        except Exception as e:
            error = {}
            error['id'] = file_metadata['id']
            error['article_name'] = article_name
            error['year'] = year
            error['error'] = str(e)

            errors.append(error)

            print(str(e))

            time.sleep(2)

    error_string = json.dumps(errors, indent=2, separators=(',', ': '))
    error_file.write(error_string)
    error_file.close()
    
def main():
    #create_surveys()
    redo_errors()
    
if __name__ == '__main__':
    main()
