from __future__ import print_function
import os
import re
# Optional import - removed during optimization to reduce slug size
try:
    from bs4 import BeautifulSoup
    BS4_AI_AVAILABLE = True
except ImportError:
    BeautifulSoup = None
    BS4_AI_AVAILABLE = False
import json
import psycopg2
import requests
from django.http import JsonResponse
from ai_services.models import DynamicExcelData
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
# Optional import - removed during optimization to reduce slug size
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False
from datetime import datetime, time
import mimetypes

from django.db.models import Max
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import date,datetime, timedelta
from marketing.models import Whatsapp_Groups
from professional_services.models import UserAnswerStatus,Prep_Questions
from django.core.management.base import BaseCommand
from finance.models import (Transaction, CodaBudget, BudgetCategory,
                            BudgetSubCategory,WebCategory,WebSubCategory
                            )
from accounts.models import Department
from main.models import Company

from django.contrib.auth import get_user_model
# To encode the data
from base64 import urlsafe_b64decode
import logging
logger = logging.getLogger(__name__)
#libraries for Options_play data extraction

from coda_project.settings import dba_values ,source_target #dblocal,herokudev,herokuprod
# from testing.utils import dblocal,herokudev,herokuprod
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://mail.google.com/']

#DB VARIABLES
# host,dbname,user,password=herokudev() #herokudev() #dblocal() #,herokuprod()
host,dbname,user,password=dba_values() #herokudev() #dblocal() #,herokuprod()

#DB VARIABLES
(source_host, source_dbname, source_user, source_password,target_db_path) = source_target()



def fetch_and_insert_data():
    (source_host, source_dbname, source_user, source_password, target_db_path) = source_target()

    # Connect to the source database
    source_conn = psycopg2.connect(
        host=source_host,
        dbname=source_dbname,
        user=source_user,
        password=source_password
    )
    source_cursor = source_conn.cursor()

    # Connect to the target database
    target_conn = psycopg2.connect(target_db_path)
    target_cursor = target_conn.cursor()

    source_tables = ['investing_shortput', 'investing_credit_spread', 'investing_covered_calls',] #'investing_oversold','investing_ticker_data'
    target_tables = ['investing_shortput', 'investing_credit_spread', 'investing_covered_calls',] #'investing_oversold','investing_ticker_data'

    try:
        # Iterate over source and target tables
        for source_table, target_table in zip(source_tables, target_tables):
            # Fetch the structure of the source table
            source_cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{source_table}'")
            columns = source_cursor.fetchall()

            # Get unique column names and their corresponding data types
            unique_columns = {}
            for column in columns:
                column_name = column[0]
                column_data_type = column[1]
                if column_name not in unique_columns:
                    unique_columns[column_name] = column_data_type

            # Create the target table if it doesn't exist
            create_table_query = f"CREATE TABLE IF NOT EXISTS {target_table} ("
            column_names = set()  # Track column names to avoid duplicates
            for column_name, column_data_type in unique_columns.items():
                if column_name not in column_names:
                    create_table_query += f"{column_name} {column_data_type}, "
                    column_names.add(column_name)
            create_table_query = create_table_query.rstrip(", ") + ")"
            target_cursor.execute(create_table_query)

            # Fetch data from the source table
            source_cursor.execute(f"SELECT * FROM {source_table}")
            rows = source_cursor.fetchall()

            # Insert or update data in the target table
            for row in rows:
                # import pdb; pdb.set_trace()
                placeholders = "%s, " * len(row)
                placeholders = placeholders.rstrip(", ")
                
                column_list = tuple('{element}' for element in tuple(unique_columns.keys()))
                column_list = ', '.join(f'{key}' for key in unique_columns.keys())

                # Use INSERT ... ON CONFLICT to insert or update the data
                # target_cursor.execute(f"INSERT INTO {target_table} VALUES ({placeholders}) ON CONFLICT DO NOTHING", row)
                target_cursor.execute(
                    f"INSERT INTO {target_table} ({column_list}) "
                    f"SELECT {placeholders} WHERE NOT EXISTS (SELECT 1 FROM {target_table} WHERE symbol = %s)",
                    row + (row[0],)  # Add an extra element to the tuple
                )


            cut_off_date = datetime.now() - timedelta(days=10)
            print(cut_off_date.date())
            target_cursor.execute("SET datestyle TO 'MDY'")

            # Delete rows with earning date in the past
            target_cursor.execute(
                f"DELETE FROM {target_table} WHERE to_date(left(earnings_date, 10), 'MM/DD/YYYY') < %s",
                (cut_off_date.date().strftime('%m/%d/%Y'),)
            )

        source_cursor.execute("DELETE FROM investing_overboughtsold WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days';")
        target_cursor.execute("DELETE FROM investing_overboughtsold WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days';")

        # Commit the changes in the target database
        target_conn.commit()
        source_conn.commit()

        print("Data transfer successful!")
    except Exception as e:
        print(f"Data transfer failed: {str(e)}")

    # Close the database connections
    source_conn.close()
    target_conn.close()

# def process_file(csv_file,url):
# 	if not csv_file.name.endswith(".csv"):
# 		return url
# 		# messages.warning(
# 		# 	request, "The wrong file type was uploaded, it should be a csv file"
# 		# )
# 		# return render(request, "ai_services/uploaddata.html")
# 		# return HttpResponseRedirect(request.path_info)
# 	else:
# 		file = csv_file.read().decode("ISO-8859-1")
# 		file_data = file.split("\n")
# 		csv_data = [line for line in file_data if line.strip() != ""]
    # Define the date formats to try
    # date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]  # Add more formats as needed

# 	return csv_data,date_formats
def convert_excel_dates(date_str, expiry_str):
    # Define the date formats to try
    date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%Y"]
    
    # Iterate over the date formats
    for format in date_formats:
        try:
            # Parse the Excel date strings using the current format
            entry_date = datetime.strptime(date_str, format).strftime("%Y-%m-%d")
            expiry_date = datetime.strptime(expiry_str, format).strftime("%Y-%m-%d")
            # Return the formatted dates if parsing succeeds
            return entry_date, expiry_date
        except ValueError:
            pass  # Continue to the next format if parsing fails
    
    # Return None for both dates if parsing fails for all formats
    return None, None


def compute_stock_values(stockdata):
    date_today = date.today()
    row = None  # Initialize row to None
    iv = rr = ar = sp = num_days = date_expiry = days_to_exp = None  # Initialize variables
    for current_row in stockdata:
        try:
            iv = current_row.Implied_Volatility_Rank
            rr = current_row.Raw_Return
            ar = current_row.Annualized_Return
            sp = current_row.Stock_Price
            num_days = current_row.Days_To_Expiry
            date_expiry = current_row.Expiry.date()  # Assign the datetime object directly
            days_to_exp = (date_expiry - date_today).days

            if isinstance(iv, str):
                iv = iv.replace('%', '')
            if isinstance(rr, str):
                rr = rr.replace('%', '')
            if isinstance(ar, str):
                ar = ar.replace('%', '')
            if isinstance(sp, str):
                sp = sp[1:]

            row = current_row  # Update row with the current valid row
        except (ValueError, AttributeError):
            continue

    return row, iv, rr, ar, sp, num_days, date_expiry, days_to_exp




def row_value():
    putsrow_value=3
    callsrow_value=3
    id_value=3
#     rows = Editable.objects.all()
#     if rows:
#         first_row = rows[0]  # get the first object in the QuerySet
#         putsrow_value = first_row.putsrow  # get the value of the `putsrow` field
#         callsrow_value = first_row.callsrow  # get the value of the `callsrow` field
#         id_value=first_row.id
#         # print(putsrow_value,callsrow_value,id_value)
#     else:
#         print("No objects found with id=1")
#         putsrow_value=1
#         callsrow_value=1
#         id_value=1
    return putsrow_value,callsrow_value,id_value

def get_gmail_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credential_file='gapi/creds/robincredentials.json'
            # CURR_DIR = os.path.dirname(os.path.realpath(__file__))
            # credential_file=str(CURR_DIR)+'/credentials.json'  #may need backslash in windows
            flow = InstalledAppFlow.from_client_secrets_file(
                credential_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        if not labels:
            print('No labels found.')
            return
        print('Labels:')
        for label in labels:
            print(label['name'])

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')
    return service

def search_messages(service, query):
    result = service.users().messages().list(userId='me', q=query).execute()
    messages = [ ]
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages']) 
    return messages

def get_message(service, msg_id):
    # mark that mail as read.
    msg = service.users().messages().modify(
        userId='me',
        id=msg_id,
        body={
            'addLabelIds': [],
            'removeLabelIds': ['UNREAD'],
        },
        x__xgafv='1').execute()

    # get all the data about msg.
    msg = service.users().messages().get(userId='me', id=msg_id).execute()
    if not msg:
        logger.error('message not found!')
        return

    msg_payload = msg.get('payload')

    headers = msg_payload.get('headers')

    for header in headers:
        if header.get('name') == 'Date':
            received_date = header.get('value')
        if header.get('name') == 'From':
            from_mail = header.get('value')
        if header.get('name') == 'To':
            to_mail = header.get('value')
        if header.get('name') == 'Subject':
            subject = header.get('value')
    try:
        html_part = msg_payload.get('parts')[1]
        encoded_data = html_part.get('body').get('data')

        decoded_str = str(urlsafe_b64decode(encoded_data),'UTF-8')
        file_name = 'mail-'+msg_id+'.html'
        # html_path = os.path.join('stored_mails', file_name)

        # if not os.path.exists(html_path):

        with open(file_name, 'w+') as out:
            file = out.write(decoded_str)
    except:
        return 
    
    # return {
    #     'id': msg_id,
    #     'from_mail': from_mail,
    #     'to_mail': to_mail,
    #     'subject': subject,
    #     'text_mail': decoded_str,
    #     'received_date': received_date,
    #     'file_name' : file_name
    # }
    return file_name

#inserting data into database
def stock_data(symbol,action,qty, unit_price, total_price,date):
    #Database connection 
    try:
        with psycopg2.connect(
                                host = host,
                                dbname = dbname,
                                user = user,
                                password = password,
                                port = 5432
                            ) as conn:
            with conn.cursor() as cursor:
                #Creating database named RobinhoodEmailInfo
                creating_db = '''CREATE TABLE IF NOT EXISTS getdata_stockmarket (
                    symbol varchar(250),
                    action varchar(200),
                    qty int,
                    unit_price float,
                    total_price float,
                    date date
                )'''
                cursor.execute(creating_db)

                insert_query = '''INSERT INTO getdata_stockmarket(symbol,action,qty,unit_price,total_price,date) VALUES (%s,%s,%s,%s,%s,%s)'''
                values = (symbol,action, qty,unit_price,total_price,date)
                cursor.execute(insert_query,vars = values)
    except Exception as err:
        print(err)


#inserting data into cryptodatabase
def crypto_data(symbol,action,unit_price, total_price,date):
    try:
        with psycopg2.connect(
                                host = host,
                                dbname = dbname,
                                user = user,
                                password = password,
                                port = 5432
                            ) as conn:
            with conn.cursor() as cursor:
                #getdata_cryptomarket
                creating_db = '''CREATE TABLE IF NOT EXISTS getdata_cryptomarket(
                    symbol varchar(250),
                    action varchar(200),
                    unit_price float,
                    total_price float,
                    date date
                )'''
                cursor.execute(creating_db)

                insert_query = '''INSERT INTO getdata_cryptomarket(symbol,action,unit_price,total_price,date) VALUES (%s,%s,%s,%s,%s)'''
                values = (symbol,action,unit_price,total_price,date)
                cursor.execute(insert_query,vars = values)
        
    except Exception as err:
        print(err)

def getdata(file):
    '''Get the html content'''
    if not BS4_AI_AVAILABLE:
        return None
        
    try:
        HTMLFile = open(file, "r")
    
        # Reading the file
        index = HTMLFile.read()
        #parsing into beautifulsoup
        soup = BeautifulSoup(index, 'html.parser')
    except:
        return 0
    return soup

#Fetch the header option
def GetSubject(soup):
    '''Profile Name'''
    try:
        name = soup.find_all('div', {'class' : 'mj-section-rh'})
        subject = name[1].find('div').text
        sub_pat = re.compile(r'Order Executed|Option Order Executed')
        sub_match = sub_pat.findall(subject)
        subject = sub_match[0].strip()
        print(subject)

        return subject
    except:
        return None

def populate_table_from_json_file(file_path):
    try:
        # Read the text file containing JSON data
        with open(file_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
        #  Extract data into a list of dictionaries
        data_list = [{
            'id': item['id'][:-15] + ('-' if '-' not in item['id'][-15:] else '') + item['id'][-15:],
        	'name': item.get('name', 'default_name'), 
        	'participants': len(item.get('participants', []))
        } for item in json_data['data']]

        for data in data_list:
            Whatsapp_Groups.objects.update_or_create(
                group_id=data['id'],
                defaults={
                    'group_name': data['name'],
                    'participants': data['participants']
                }
            )

    except FileNotFoundError:
        return JsonResponse({'error': 'File not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)


class Run_Command(BaseCommand):
    help = 'Fetch WhatsApp groups and populate the database'

    def handle(self, *args, **kwargs):
        # Your code to fetch WhatsApp groups here
        whatsapp_groups_data = self.fetch_whatsapp_groups()

        # Iterate over the fetched data and add new groups to the database
        for group_data in whatsapp_groups_data:
            self.create_or_update_group(group_data)

    def fetch_whatsapp_groups(self):
        # Use the requests library to fetch WhatsApp groups from the API
        product_id = os.environ.get('MAYTAPI_PRODUCT_ID')
        screen_id = os.environ.get('MAYTAPI_SCREEN_ID')
        token = os.environ.get('MAYTAPI_TOKEN')
        url = f"https://api.maytapi.com/api/{product_id}/{screen_id}/getGroups"
        headers = {"x-maytapi-key": token}
        response = requests.get(url, headers=headers)

        # Check for errors and return the data as a list of dictionaries
        if response.status_code == 200:
            return response.json()
        else:
            self.stdout.write(self.style.ERROR(f"Failed to fetch WhatsApp groups. Status code: {response.status_code}"))
            return []

    def create_or_update_group(self, group_data):
        # Check if the group already exists in the database
        group_id = group_data.get("group_id")
        if Whatsapp_Groups.objects.filter(group_id=group_id).exists():
            print(group_id)
            self.stdout.write(self.style.SUCCESS(f"Group with ID {group_id} already exists. Skipping."))
        else:
            # Create a new Whatsapp_Groups object with the fetched data
            Whatsapp_Groups.objects.create(
                group_id=group_data.get("group_id"),
                slug=group_data.get("slug"),
                group_name=group_data.get("group_name"),
                participants=group_data.get("participants"),
                category=group_data.get("category"),
                type=group_data.get("type"),
            )
            self.stdout.write(self.style.SUCCESS(f"Added new group with ID {group_id} to the database."))

def move_questions_to_user_answer_status(username):
    # Step 1: Identify the records in the Prep_Questions table
    prep_questions_to_move = Prep_Questions.objects.filter(is_answered=True)

    # Step 2: Create new UserAnswerStatus objects for each identified record
    for prep_question in prep_questions_to_move:
        # Determine the user for the UserAnswerStatus object
        user = prep_question.questioner if prep_question.questioner else username
        # Create a new UserAnswerStatus object
        user_answer_status = UserAnswerStatus.objects.create(
            user=user,
            question=prep_question,
            role=prep_question.position,
            answer=prep_question.response,
            is_answered=True
        )

        # Optionally, update the is_answered field in the Prep_Questions table
        prep_question.is_answered = False
        prep_question.save()


table_contents=[
    {
        "topic": "Overview",
        "description": "Project Description |What the Use case is about"
    },
    {
        "topic": "Practical Demonstration",
        "description":  "Hardware/Software Requirements,Business Requirements,Technical Requirements"
    },
   
    {
        "topic": "Development",
        "description": "Modeling/Data Dictionary, Functional Components,Implementing Functional Components,Testing Functional Components"
    },
    
    {
        "topic": "Deployment",
        "description": "Heroku Environment,Github/Version Control"
    }
]

Hardware_Software_Req=[
     {
        "topic":"CODA Website",
        "link":"www.codanalytics/net"
      },
     {
        "topic":"CODA Google Drive",
        "link":"https://drive.google.com/drive/u/0/home"
      },
     {
        "topic":"Chatgpt",
        "link":"https://chatgpt.com/"
      },
     {
        "topic":"Python",
        "link":"https://www.python.org/downloads/"
      },
     {
        "topic":"Postgres",
        "link":"https://www.postgresql.org/"
      },
     {
        "topic":"VS CODE",
        "link":"https://code.visualstudio.com/download"
      },
     {
        "topic":"GIT",
        "link":"https://git-scm.com/"
      },
     {
        "topic":"GitHub",
        "link":"https://github.com/"
      },
     {
        "topic":"Heroku",
        "link":"https://id.heroku.com/login"
      },
     {
        "topic":"AWS(S3 Bucket)",
        "link":"https://aws.amazon.com"
      },
]


User = get_user_model()
# =============================FINANCE APP=========================
def populate_budget_categories(cat):
    # web_categories = [
    #     'Services',
    #     'Registration',
    #     'Reporting',
    #     'Financial',
    #     'Training',
    #     'Management',
    #     'Other',
    # ]
    web_categories = [
        'Design and Development',
        'Content Management',
        'SEO and Digital Marketing',
        'Hosting and Infrastructure',
        'Security and Compliance',
        'E-commerce',
        'Analytics and Reporting',
        'Customer Support',
        'Maintenance and Support',
        'Third-Party Integrations',
    ]
    coda_categories = [
        'Salaries and Wages',
        'Marketing and Advertising',
        'Sales Commissions',
        'Rent',
        'Utilities',
        'Office Supplies',
        'Travel and Entertainment',
        'Professional Services',
        'Insurance',
        'Depreciation and Amortization',
        'Training and Development',
        'IT and Software',
        'Maintenance and Repairs',
        'Taxes',
        'Miscellaneous Expenses',
        'Operational Expenses',
        'Research and Development (R&D)',
        'Human Resources',
        'Inventory and Supplies',
        'Facilities and Equipment',
        'Logistics and Shipping',
        'Customer Service',
        'Security',
        'Compliance and Regulatory'
    ]
    if cat=="web":
        for category_name in web_categories:
            if not WebCategory.objects.filter(name=category_name).exists():
                WebCategory.objects.create(name=category_name, description=f'description')
    else:
        for category_name in web_categories:
            if not WebCategory.objects.filter(name=category_name).exists():
                WebCategory.objects.create(name=category_name, description=f'description')

    print('Successfully populated BudgetCategory table')


def populate_budget_subcategories(subcat):
    web_subcategories = {
        'Design and Development': [
            'Website Design',
            'Front-end Development',
            'Back-end Development',
            'User Experience (UX) Design',
            'User Interface (UI) Design',
            'Responsive Design',
        ],
        'Content Management': [
            'Content Creation',
            'Blogging',
            'Copywriting',
            'Video Production',
            'Graphic Design',
            'Content Updates',
        ],
        'SEO and Digital Marketing': [
            'Search Engine Optimization (SEO)',
            'Pay-Per-Click (PPC) Advertising',
            'Social Media Marketing',
            'Email Marketing',
            'Influencer Marketing',
            'Marketing Automation',
        ],
        'Hosting and Infrastructure': [
            'Web Hosting',
            'Domain Registration',
            'SSL Certificates',
            'Content Delivery Network (CDN)',
            'Cloud Storage',
            'Backup Services',
        ],
        'E-commerce': [

            'Shopping Cart Integration',
            'Payment Gateway Integration',
            'Product Management',
            'Order Management',
            'Customer Relationship Management (CRM)',
            'Subscription Services'
            ],
        'Analytics and Reporting': [

            'Google Analytics',
            'Custom Reporting Tools',
            'User Behavior Analysis',
            'Conversion Rate Optimization (CRO)',
            'A/B Testing',
            'Dashboard Development'
            ],
        'Customer Support': [

            'Live Chat Integration',
            'Chatbots',
            'Email Support',
            'Phone Support',
            'Help Desk Software',
            'Knowledge Base'
            ],
        'Maintenance and Support': [

            'Regular Updates',
            'Bug Fixes',
            'Technical Support',
            'Performance Optimization',
            'Server Monitoring',
            'SLA Agreements'
            ],
        'Third-Party Integrations': [

            'API Integrations',
            'Social Media Integrations',
            'Email Marketing Integrations',
            'CRM Integrations',
            'ERP Integrations',
            'Payment Gateway Integrations',
            ],
        'Security and Compliance': [
                    'SSL Certificates',
                    'Web Application Firewalls',
                    'Security Audits',
                    'GDPR Compliance',
                    'PCI Compliance',
                    'Two-Factor Authentication',
                    'Compliance audits',
                    'Cybersecurity Measures',
                    'Data Security'
                ]
    }
    coda_subcategories = {
        'Salaries and Wages': [
            'Regular employee salaries',
            'Overtime pay',
            'Bonuses',
            'Employee benefits (health insurance, retirement plans)'
        ],
        'Marketing and Advertising': [
            'Digital advertising (Google Ads, Facebook Ads)',
            'Print advertising (newspapers, magazines)',
            'Event sponsorships',
            'Social media promotions',
            'Marketing materials (brochures, flyers)'
        ],
        'Sales Commissions': [
            'Commissions for sales staff',
            'Bonuses based on sales performance'
        ],
        'Rent': [
            'Office rent',
            'Warehouse rent',
            'Equipment rental'
        ],
        'Utilities': [
            'Electricity',
            'Water',
            'Gas',
            'Internet and phone services'
        ],
        'Office Supplies': [
            'Stationery',
            'Printer ink and paper',
            'General office supplies'
        ],
        'Travel and Entertainment': [
            'Business travel expenses (flights, hotels, car rentals)',
            'Client entertainment (meals, events)',
            'Employee meals during business trips'
        ],
        'Professional Services': [
            'Legal fees',
            'Accounting services',
            'Consulting fees'
        ],
        'Insurance': [
            'General liability insurance',
            'Health insurance',
            'Property insurance'
        ],
        'Depreciation and Amortization': [
            'Depreciation of fixed assets',
            'Amortization of intangible assets'
        ],
        'Training and Development': [
            'Employee training programs',
            'Professional development courses',
            'Certifications'
        ],
        'IT and Software': [
            'Website Maintenance',
            'Hosting Fees',
            'Communication Tools',
            'Software Licenses',
            'Cloud Services',
            'IT Support and Maintenance'
        ],
        'Maintenance and Repairs': [
            'Office maintenance',
            'Equipment repairs',
            'Building maintenance'
        ],
        'Taxes': [
            'Income tax',
            'Property tax',
            'Sales tax'
        ],
        'Miscellaneous Expenses': [
            'Bank fees',
            'Subscriptions and memberships',
            'Donations and charitable contributions'
        ],
        'Operational Expenses': [
            'Office Utilities',
            'Communication Services',
            'Equipment Rentals and Maintenance',
            'Food and Groceries'
        ],
        'Research and Development (R&D)': [
            'Product development',
            'Testing and prototyping',
            'Market research'
        ],
        'Human Resources': [
            'Recruitment costs',
            'Employee relations',
            'Payroll services'
        ],
        'Inventory and Supplies': [
            'Raw materials',
            'Finished goods',
            'Packaging materials'
        ],
        'Facilities and Equipment': [
            'Office furniture',
            'Office equipment (computers, printers)',
            'Manufacturing equipment'
        ],
        'Logistics and Shipping': [
            'Shipping costs',
            'Freight charges',
            'Warehousing'
        ],
        'Customer Service': [
            'Customer support services',
            'Return and refund management'
        ],
        'Security': [
            'Physical security (guards, security systems)',
            'Cybersecurity measures'
        ],
        'Compliance and Regulatory': [
            'Compliance audits',
            'Regulatory fees',
            'Industry certifications'
        ]
    }
   
    if subcat=="web":
        for category_name, subcategory_names in web_subcategories.items():
            try:
                print(f'Category "{category_name}" First')
                category = WebCategory.objects.get(name=category_name)
                print(f'Category "{category}" second')
                for subcategory_name in subcategory_names:
                    # Check if the subcategory exists before creating it
                    if not WebSubCategory.objects.filter(category=category, name=subcategory_name).exists():
                        WebSubCategory.objects.create(
                            category=category,
                            name=subcategory_name,
                            # description=f'{subcategory_name} description'  # Optionally add descriptions
                        )
            except WebSubCategory.DoesNotExist:
                print(f'Category "{category_name}" does not exist')
    else:
        for category_name, subcategory_names in coda_subcategories.items():
            try:
                category = BudgetCategory.objects.get(name=category_name)
                for subcategory_name in subcategory_names:
                    # Check if the subcategory exists before creating it
                    if not BudgetSubCategory.objects.filter(category=category, name=subcategory_name).exists():
                        BudgetSubCategory.objects.create(
                            category=category,
                            name=subcategory_name,
                            # description=f'{subcategory_name} description'  # Optionally add descriptions
                        )
            except BudgetCategory.DoesNotExist:
                print(f'Category "{category_name}" does not exist')


    print('Successfully populated BudgetSubCategory table')



# def transfer_transactions_to_codabudget(current_user):
#     transactions = Transaction.objects.all()

#     for transaction in transactions:
#         # Ensure the transaction has a department
#         if not hasattr(transaction, 'department') or transaction.department is None:
#             continue

#         # Find or create corresponding Department
#         department, created = Department.objects.get_or_create(name=transaction.department.name)

#         # Find or create corresponding BudgetCategory
#         category_name ='Other' # transaction.category.replace('_', ' ')
#         category, created = BudgetCategory.objects.get_or_create(
#             name=category_name,
#             defaults={'description': 'Default description'}  # Provide a default description
#         )

#         # Find or create corresponding BudgetSubCategory
#         subcategory, created = BudgetSubCategory.objects.get_or_create(name="Other", category=category)

#         # Find or create a default Company
#         company, created = Company.objects.get_or_create(name='Default Company')

#         # Get the budget lead
#         budget_lead = transaction.sender if transaction.sender is not None else current_user

#         # Truncate fields to avoid exceeding the max length
#         truncated_description = (transaction.description or 'No description provided')[:1000]
#         truncated_item = transaction.type[:100]
#         truncated_receipt_link = transaction.receipt_link[:255] if transaction.receipt_link else None

#         # Debug prints to check field lengths
#         print(f"Description length: {len(truncated_description)}")
#         print(f"Item length: {len(truncated_item)}")
#         print(f"Receipt link length: {len(truncated_receipt_link) if truncated_receipt_link else 'None'}")

#         # Ensure the budget lead is not null
#         # if budget_lead is None:
#         #     print(f"Skipping transaction {transaction.id} because budget_lead is None")
#         #     continue

#         # Create TestBudget instance
#         coda_budget=CodaBudget.objects.create(
#             budget_lead=budget_lead,
#             company=company,
#             department=department,
#             category=category,
#             subcategory=subcategory,
#             item=truncated_item,
#             cases=1,  # Default value
#             qty=transaction.qty,
#             unit_price=transaction.amount,
#             created_at=transaction.transaction_date,
#             description=truncated_description,
#             receipt_link=truncated_receipt_link
#         )
#         # Set the created_at field and save the instance again
#         coda_budget.created_at = transaction.transaction_date
#         coda_budget.save(update_fields=['created_at'])

#     return "Successfully transferred data from Transaction to TestBudget"


def transfer_transactions_to_codabudget(current_user):
    """
    Transfers only new transactions from `Transaction` to `CodaBudget`,
    starting from the last transferred `created_at` date.
    """
    print('Transfers only new transactions from `Transaction` to `CodaBudget`')
    
    # Step 1: Get the last created_at date from CodaBudget
    last_transfer_date = CodaBudget.objects.aggregate(last_date=Max('created_at'))['last_date']
    print(last_transfer_date)
    return 
    if last_transfer_date:
        print(f"Last transfer date: {last_transfer_date}")
        transactions = Transaction.objects.filter(transaction_date__gt=last_transfer_date)
    else:
        print("No previous transactions found, transferring all available data.")
        transactions = Transaction.objects.all()  # First time migration

    for transaction in transactions:
        # Ensure the transaction has a department
        if not hasattr(transaction, 'department') or transaction.department is None:
            continue

        # Find or create corresponding Department
        department, created = Department.objects.get_or_create(name=transaction.department.name)

        # Find or create corresponding BudgetCategory
        category_name = 'Other'
        category, created = BudgetCategory.objects.get_or_create(
            name=category_name,
            defaults={'description': 'Default description'}
        )

        # Find or create corresponding BudgetSubCategory
        subcategory, created = BudgetSubCategory.objects.get_or_create(name="Other", category=category)

        # Find or create a default Company
        company, created = Company.objects.get_or_create(name='Default Company')

        # Get the budget lead
        budget_lead = transaction.sender if transaction.sender is not None else current_user

        # Truncate fields to avoid exceeding max length
        truncated_description = (transaction.description or 'No description provided')[:1000]
        truncated_item = transaction.type[:100]
        truncated_receipt_link = transaction.receipt_link[:255] if transaction.receipt_link else None

        # Debug prints
        print(f"Processing transaction {transaction.id} from {transaction.transaction_date}")

        # **Check if the record already exists before creating**
        existing_record = CodaBudget.objects.filter(
            budget_lead=budget_lead,
            company=company,
            department=department,
            category=category,
            subcategory=subcategory,
            item=truncated_item,
            qty=transaction.qty,
            unit_price=transaction.amount,
            created_at=transaction.transaction_date,
        ).exists()

        if existing_record:
            print(f"Skipping existing transaction for item {truncated_item} on {transaction.transaction_date}")
            continue  # Skip if already transferred

        # Create new CodaBudget entry
        coda_budget = CodaBudget.objects.create(
            budget_lead=budget_lead,
            company=company,
            department=department,
            category=category,
            subcategory=subcategory,
            item=truncated_item,
            cases=1,
            qty=transaction.qty,
            unit_price=transaction.amount,
            created_at=transaction.transaction_date,
            description=truncated_description,
            receipt_link=truncated_receipt_link
        )

    return f"Successfully transferred {transactions.count()} new transactions from Transaction to CodaBudget."



company_details = {
    "name": "CODA ANALYTICS",
    "tagline": "Business Intelligence, Web Development, AI, Automation, Consultancy",
    "approach": "Client-focused, turning your vision into scalable, user-friendly solutions.",
    "services": {
        "Web Development": "Creating top-tier web applications.",
        "AI and Automation": "Streamlining processes with AI.",
        "IT Training": "Project-based and data analysis training.",
        "Interview Practice": "Mock interviews and self-paced sessions.",
        "Consultancy": "Expert advice on modern business challenges."
    },
    "why_us": {
        "Experience": "12+ years tackling complex projects.",
        "Client_Centric": "Transparent, timely, and collaborative.",
        "Tech_Stack": "MERN, Django, Python, AWS, MySQL."
    }
}

#Excel data fetching 
def handle_non_serializable(data):
    """
    Convert non-serializable objects such as datetime and time to a serializable format.
    """
    if not PANDAS_AVAILABLE:
        return data
        
    for key, value in data.items():
        if isinstance(value, (datetime, pd.Timestamp)):
            data[key] = value.isoformat()
        elif isinstance(value, time):
            data[key] = value.strftime('%H:%M:%S')
    return data

def process_excel_file(file_path):
    """
    Process the Excel file and save data to the database.
    """
    if not PANDAS_AVAILABLE:
        print("Pandas not available - Excel processing disabled during optimization")
        return
        
    print('file',file_path)
    mime_type, _ = mimetypes.guess_type('/home/mehboob/coda/task/cores/data/Bangalore Dental - 1385.xlsx')
    print(f"MIME type: {mime_type}")
    try:
        df = pd.read_excel(file_path, engine='openpyxl') # Use 'xlrd' for .xls files if needed

        # Delete previous records
        DynamicExcelData.objects.all().delete()
        if 'Email' not in df.columns and 'Email1' not in df.columns:
            print("Neither 'Email' nor 'Email1' column found in the Excel file.")
            return


        # Process and save data
        for _, row in df.iterrows():
            email = row.get('Email')
            email1 = row.get('Email1')

            # Check if either 'Email' or 'Email1' is not empty or NaN
            if (pd.notna(email) and email != '') or (pd.notna(email1) and email1 != ''):
                data = row.to_dict()

            data = row.to_dict()
            # Handle non-serializable data
            data = handle_non_serializable(data)
            json_data = json.dumps(data)  # Serialize data to JSON
            DynamicExcelData.objects.create(data=json_data)
    except Exception as e:
        print(f"Error processing the file: {e}")

### Download recordings
from io import BytesIO
def download_recording(direct_download_url):
    """
    Downloads the recording from the direct download URL.
    Returns the binary content of the file.
    """
    try:
        response = requests.get(direct_download_url, stream=True)
        response.raise_for_status()
        
        # Read the content in chunks to handle large files
        file_content = BytesIO()
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file_content.write(chunk)
        
        return file_content.getvalue()  # Returns the binary content of the file
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading recording from {direct_download_url}: {e}")
        return None
    

## Drive function 

from googleapiclient.http import MediaIoBaseUpload

def upload_to_google_drive(service, file_content, filename, folder_id=None):
    """
    Uploads a file to Google Drive.
    :param service: Authorized Google Drive service instance.
    :param file_content: Binary content of the file.
    :param filename: Desired name of the file on Google Drive.
    :param folder_id: (Optional) ID of the folder to upload the file into.
    :return: File ID if successful, None otherwise.
    """
    file_metadata = {'name': filename}
    if folder_id:
        file_metadata['parents'] = [folder_id]

    media = MediaIoBaseUpload(BytesIO(file_content), mimetype='video/mp4')

    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        logger.info(f"File {filename} uploaded to Google Drive with ID {file.get('id')}.")
        return file.get('id')
    except Exception as e:
        logger.error(f"Error uploading file {filename} to Google Drive: {e}")
        return None    
    

activity_mapping = {
            '708385093': "PBR sessions",
            '632884285': "BI Sessions",
            '123530685': "DAF SESSION",
            '994131389': "General Meeting",
            '616024597': "PROJECT SESSION",
            '199103181': "SPRINT SESSION",
            '905794573': "REQUEST SESSION",
            '967944357': "BOG",
            '884917357': "BUDGET REVIEW MEETING",
            '931282277': "RECRUTMENT(APPLICANTS & DEVELOPERS)",
            '396508029': "APPROVAL SESSION",
    }    