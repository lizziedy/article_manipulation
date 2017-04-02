from __future__ import print_function
import httplib2
import os
import re
import json

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

DRIVE_SPREADSHEET_TYPE = 'application/vnd.google-apps.spreadsheet'
DRIVE_FOLDER_TYPE = 'application/vnd.google-apps.folder'
TEXT_TYPE = 'text/plain'


# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret_drive2.json'
APPLICATION_NAME = 'Survey Creator'

def _get_credentials():
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


def _get_drive_service():
    credentials = _get_credentials()
    http = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http)
    return drive_service

def _get_sheets_service():
    credentials = _get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    sheets_service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    return sheets_service

_drive_service = _get_drive_service()
_sheets_service = _get_sheets_service()

@rate_limiter.RateLimited(1.5)
def create_drive_object(file_name, parent_id, mime_type):
    file_metadata = {
        'name' : file_name,
        'mimeType' : mime_type,
        'parents': [parent_id]
    }
    drive_file = _drive_service.files().create(body=file_metadata,
                                        fields='id, webViewLink').execute()
    return drive_file

@rate_limiter.RateLimited(1.5)
def copy_drive_object(orig_file_id, new_object_name):
    copied_file = {'name': new_object_name}
    file = _drive_service.files().copy(fileId=orig_file_id, body=copied_file, fields='id, webViewLink').execute()
    return file

@rate_limiter.RateLimited(1.5)
def change_drive_object_permissions(file_id, role, permission_type, email=None):
    '''
    roles: 'organizer', 'owner', 'writer', 'commenter', 'reader'
    permission types: 'user', 'anyone'

    use email ony when 'user' is specified
    '''
    body = {'role':role, 'type':permission_type}
    if email:
        body['emailAddress'] = email
        
    _drive_service.permissions().create(fileId=file_id, sendNotificationEmail=False, body=body).execute()

@rate_limiter.RateLimited(1.5)
def add_file_to_drive(article_name, article_path, parent_id, mime_type):
    file_metadata = {
      'name' : article_name,
      'parents':[parent_id]
    }
    media = MediaFileUpload(article_path,
                            mimetype=mime_type)
    file = _drive_service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id, webViewLink').execute()

def get_or_create_drive_object(name, parent_id, mime_type):
    drive_object = get_drive_object(name, parent_id, mime_type)
    if not drive_object:
        drive_object = create_drive_object(name, parent_id, mime_type)
    return drive_object
    
def get_drive_object(name, parent_id, mime_type):
    page_token = None
    response = _drive_service.files().list(q="name='" + name + "'" +
                                            " and " +
                                            "'" + parent_id + "' in parents" +
                                            " and " +
                                            "mimeType='" + mime_type + "'",
                                         spaces='drive',
                                         pageToken=page_token,
                                         fields='files(id,webViewLink)').execute()
    if len(response.get('files', [])) > 0:
        return response.get('files', [])[0]
    return None

def get_sheets_spreadsheet(file_id):
    return _sheets_service.spreadsheets().get(spreadsheetId=file_id).execute()

def get_sheets_values(file_id, sheet_name, data_range, value_keys, key_index = 0):
    range_id = sheet_name + '!' + data_range
    results = _sheets_service.spreadsheets().values().get(
        spreadsheetId=file_id, range=range_id).execute()
    values = results.get('values', [])

    if values:
        values_dict = {}
        for row in values:
            if not row[key_index]: # no key so no more data
                break

            values_dict[row[key_index]] = dict(zip(value_keys, row))
    return values_dict
    
