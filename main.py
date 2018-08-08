import webbrowser
import urllib.request
import httplib2
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from simple_salesforce import Salesforce
import googleapiclient
import configparser

config = configparser.ConfigParser()
config.read('auth.ini')
SANDBOX = True


class gmail_admin:
    def __init__(self):
        1+1


    def login_to_salesforce(self, sandbox=SANDBOX):
        if sandbox is True:
            sf = Salesforce(username=config.get('auth', 'salesforce_username'),
                            domain='test',
                            password=config.get('auth', 'salesforce_password'),
                            security_token=config.get('auth', 'salesforce_token_sandbox'))
            return sf
        elif sandbox is False:
            sf = Salesforce(username=config.get('auth', 'salesforce_username'),
                            password=config.get('auth', 'salesforce_password'),
                            security_token=config.get('auth', 'salesforce_token_live'))
            return sf

    def check_for_new_user(self, sf):
        users = sf.query("SELECT Id, Name, Email, Department, Title, FirstName, LastName, Phone, Payscape_Offices__c FROM User WHERE New__c=TRUE")
        if users['totalSize'] > 0:
            print("%s record(s) found in SF matching the criteria!" % users['totalSize'])
            return users['records']
        else:
            return False



    def create_email(self, SF_Results, auth_code=None):
        self.auth_code = auth_code
        for user in SF_Results:
            if user['Phone'] is not None:
                phone_number = str(user['Phone'])
            else:
                phone_number = ""
            self.data = {
                "name": {
                    "familyName": user['FirstName'],
                    "givenName": user['LastName'],
                    "fullName": user['Name']
                },
                "organizations": [
                    {
                        "name": "Payscape",
                        "title": user['Title'],
                        "primary": True,
                        "customType": "",
                        "description": user['Title'],
                        "department": user['Department']
                    }
                ],
                "phones": [
                    {
                        "value": phone_number,
                        "type": "work"
                    }
                ],
                "primaryEmail": user['Email'],
                "password": "ilovepayscape",
                "changePasswordAtNextLogin": True,
                "includeInGlobalAddressList": True
            }
            try:
                self.google_api_create_user(self.check_stored_token(), self.data)
                print("Stored Token still valid")
            except:
                self.google_api_create_user(self.google_api_authorize(self.auth_code), self.data)
            print("User \"%s\" has been created Google Admin!"  % user['Name'])
            print("Attempting to add user to all group and %s group" % user['Payscape_Offices__c'])
            self.google_api_update_group(self.check_stored_token(), user)
            self.update_user_record(user['Id'])
            print("And the SF record has been updated!")

    def update_user_record(self, user_id):
        try:
            user = self.login_to_salesforce(sandbox=SANDBOX).User.update(user_id, {'New__c': False, 'gmailCreated__c': True})
            return user
        except Exception as e:
            print(e)


    def check_stored_token(self):
        storage = Storage('token.json')
        credentials = storage.get()
        http = httplib2.Http()
        http = credentials.authorize(http)
        service = build('admin', 'directory_v1', http=http)
        return service


    def open_auth(self):
        flow = flow_from_clientsecrets('client_secret.json',
                                       scope=['https://www.googleapis.com/auth/admin.directory.user',
                                              'https://www.googleapis.com/auth/admin.directory.group'],
                                       redirect_uri='urn:ietf:wg:oauth:2.0:oob')
        auth_uri = flow.step1_get_authorize_url()
        webbrowser.open(auth_uri)
        return auth_uri


    def google_api_authorize(self, auth_code=None):
        flow = flow_from_clientsecrets('client_secret.json',
                                   scope=['https://www.googleapis.com/auth/admin.directory.user',
                                          'https://www.googleapis.com/auth/admin.directory.group'],
                                   redirect_uri='urn:ietf:wg:oauth:2.0:oob')
        auth_uri = flow.step1_get_authorize_url()

        print(auth_uri)
        if auth_code is None:
            return "Auth code is not set. Please check info."
        credentials = flow.step2_exchange(auth_code)
        storage = Storage('token.json')
        http = httplib2.Http()
        http = credentials.authorize(http)
        service = build('admin', 'directory_v1', http=http)
        storage.put(credentials)
        return service


    def google_api_create_user(self, service, data):
        # Call the Admin SDK Directory API
        results = service.users().insert(body=data).execute()
        return results

    def google_api_update_group(self, service, user):
        # Call the Admin SDK Directory API
        data = {
            "email": user['Email'], # Email of member (Read-only)
        }
        all = service.members().insert(groupKey="all@payscape.com", body=data).execute()
        print("User Added to \"All\" Group")
        location = service.members().insert(groupKey=user['Payscape_Offices__c'].lower() + "@payscape.com", body=data).execute()
        print("User Added to \"%s\" Group" % user['Payscape_Offices__c'].lower())
