import os
import pickle
import time
from base64 import urlsafe_b64decode
from django.shortcuts import get_object_or_404, redirect, render
from functools import wraps

import os
# import pandas as pd
from bs4 import BeautifulSoup
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import logging
logger = logging.getLogger(__name__)


# If you modified scopes, delete the file token.json and re-authenticate!
SCOPES = ('https://mail.google.com/',)
current_dir = os.path.dirname(os.path.abspath(__file__))
client_id = os.environ.get('GAPI_CLIENT_ID')
project_id = os.environ.get('GAPI_PROJECT_ID')
client_secret = os.environ.get('GAPI_CLIENT_SECRET')

# Validate required credentials
if not all([client_id, project_id, client_secret]):
    logger.warning("Missing Google API credentials - some functionality may be limited")

DEFAULT_CREDENTIALS = {"installed":
                       {"client_id": client_id,
                        "project_id": project_id,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_secret": client_secret,
                        "redirect_uris": ["http://127.0.0.1:8000/"]
                        # "redirect_uris": ["https://www.codanalytics.net"]
                        }
                       }

# DEFAULT_CREDENTIALS = os.path.join(current_dir, 'creds/credentials.json')

DEFAULT_TOKEN = os.path.join(current_dir, 'creds/token.pickle')


def retry_on_failure(max_retries=3, delay=2):
    """Decorator to retry failed API operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Final attempt failed for {func.__name__}: {str(e)}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}, retrying in {delay}s...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


def get_service(scopes=SCOPES, service_name='gmail', service_version='v1', token=DEFAULT_TOKEN, credentials=DEFAULT_CREDENTIALS):
    """Get Google API service with enhanced security and error handling"""
    try:
        # Validate credentials before proceeding
        if not all([client_id, project_id, client_secret]):
            logger.error("Missing Google API credentials")
            raise ValueError("Missing Google API credentials. Please set GAPI_CLIENT_ID, GAPI_PROJECT_ID, and GAPI_CLIENT_SECRET environment variables.")
        
        # Validate scopes
        if not scopes or not isinstance(scopes, (tuple, list)):
            logger.error("Invalid scopes provided")
            raise ValueError("Invalid scopes provided")
        
        creds = None
        # the file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time
        if os.path.exists(token):
            try:
                with open(token, "rb") as token_file:
                    creds = pickle.load(token_file)
            except (pickle.PickleError, EOFError) as e:
                logger.warning(f"Error loading token file: {e}")
                # Remove corrupted token file
                try:
                    os.remove(token)
                except OSError:
                    pass
                creds = None
        
        # if there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Credentials refreshed successfully")
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds:
                try:
                    # flow = InstalledAppFlow.from_client_secrets_file(credentials, scopes)
                    flow = InstalledAppFlow.from_client_config(credentials, scopes)
                    creds = flow.run_local_server(port=0)
                    logger.info("New authentication flow completed")
                except Exception as e:
                    logger.error(f"Authentication flow failed: {e}")
                    raise
        
        # save the credentials for the next run
        if creds:
            try:
                with open(token, "wb") as token_file:
                    pickle.dump(creds, token_file)
                logger.debug("Credentials saved successfully")
            except Exception as e:
                logger.warning(f"Could not save credentials: {e}")
        
        # Build and return the service
        service = build(service_name, service_version, credentials=creds)
        logger.info(f"Google API service '{service_name}' v{service_version} created successfully")
        return service
        
    except Exception as e:
        logger.error(f"Failed to create Google API service: {e}")
        raise


@retry_on_failure(max_retries=3, delay=2)
def search_messages(service, query):
    """Search Gmail messages with retry logic and enhanced error handling"""
    try:
        if not service:
            raise ValueError("Service object is required")
        
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        
        result = service.users().messages().list(userId='me', q=query).execute()
        messages = []
        
        if 'messages' in result:
            messages.extend(result['messages'])
        
        # Handle pagination
        while 'nextPageToken' in result:
            page_token = result['nextPageToken']
            result = service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
            if 'messages' in result:
                messages.extend(result['messages'])
        
        logger.info(f"Found {len(messages)} messages for query: {query}")
        return messages
        
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        raise


@retry_on_failure(max_retries=3, delay=2)
def get_message(service, msg_id):
    """Get Gmail message with retry logic and enhanced error handling"""
    try:
        if not service:
            raise ValueError("Service object is required")
        
        if not msg_id:
            raise ValueError("Message ID is required")
        
        # Mark message as read
        msg = service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={
                'addLabelIds': [],
                'removeLabelIds': ['UNREAD'],
            },
            x__xgafv='1').execute()

        # Get message data
        msg = service.users().messages().get(userId='me', id=msg_id).execute()
        if not msg:
            logger.error(f'Message not found: {msg_id}')
            return None

        logger.info(f"Message {msg_id} retrieved successfully")
        return msg
        
    except Exception as e:
        logger.error(f"Error getting message {msg_id}: {e}")
        raise


'''Importing the required libraries'''


def getdata(file):
    '''Get the html content'''
    HTMLFile = open(file, "r")
  
    # Reading the file
    index = HTMLFile.read()

    #parsing into beautifulsoup
    soup = BeautifulSoup(index, 'html.parser')
    return soup

def GetProfileName(soup):
    '''Profile Name'''
    try:
        profile = soup.find('div', {'class' : 'text profile-name'}).text
        return profile.strip()
    except:
        pass
    try:
        profile = soup.find('div', {'class' : 'text'}).text
        return profile.strip()
    except:
        pass

def gettable_data(soup):
    '''Table Data which contains the detailed information'''
    dict_ = {}
    dict_['Destination'] = 'cashapp'
    try:
        parent_tag = soup.find('td', {'class': 'divider-top detail-list-padding'})
        table_data = parent_tag.find_all('tr', {'class' : 'detail-row'})
        for i in table_data:
            label = i.find('div', {'class' : 'label'}).text.strip()
            value = i.find('div', {'class' : 'value'}).text.strip()
            try:
                if label == 'Amount':
                    dict_[label] = value
                if label == 'Identifier':
                    dict_[label] = value
                if label == 'To':
                    dict_[label] = value
                if label == 'From':
                    dict_[label] = value
                else:
                    pass
            except:
                dict_['Amount'] = '0'

    except TypeError as e:
        # If key is not present, will add to dictionary
        # try:
        #     keynote = soup.find('div', {'class' : 'text note'}).text.strip()
        #     dict_['key_note'] = keynote
        # except:
        #     pass
        
        # #if only description is given
        # try:
        #     keynote = soup.find('div', {'class' : 'subtitle text'}).text.strip()
        #     dict_['key_note'] = keynote
        # except:
        #     pass

        # #if only description is given
        # try:
        #     keynote = soup.find('td', {'class' : 'mobBodyStandardFontSize mobBodyStandardLineHeight'})
        #     txt = keynote.find('span').text.strip()
        #     dict_['key_note'] = txt
        # except:
        #     dict_['key_note'] = ''
        print(f"Error caused {e}")

    return dict_

def cashapp_main(path):
    # '''Reading and writing the files'''
    # folderpath = r"gapi\stored_mails"
    # filepaths  = [os.path.join(folderpath, name) for name in os.listdir(folderpath)]
    # print("MY CASHAPP FUNCTION")
    # details = []
    # for path in filepaths:
    #     #process only the html files
    #     try:
    #         if path.endswith('html'):
    #             print(path)
    #             soup = getdata(path)
    #             name = GetProfileName(soup)
    #             table_data = gettable_data(soup)
    #             table_data['name'] = name
    #             table_data['path'] = path
    #             if table_data['name'] == 'Uber':
    #                 table_data['To'] = 'Uber'
    #                 table_data['From'] = 'CHRISTOPHER C MAGHAS'
                
    #             print(table_data)
    #     except:
    #         return redirect('main:layout')
    if path.endswith('html'):
        dict_ = {
                'From' : "None",
                'Amount' : 0,
                'To' : "None"
                }
        try:
            soup = getdata(path)
            name = GetProfileName(soup)
            print(name)
            table_data = gettable_data(soup)
            # table_data['name'] = name
            # table_data['path'] = path
            # if table_data['name'] == 'Uber':
            #     table_data['To'] = 'Uber'
            #     table_data['From'] = 'CHRISTOPHER C MAGHAS'
            dict_['To'] = table_data['To']
            dict_['From'] = table_data['From']
            dict_['Amount'] = table_data['Amount']
            return dict_
        except:
            return dict_
    else:
        pass


