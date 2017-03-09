from googleapiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow, Credentials
import boto3
import uuid
import webbrowser
import httplib2
import datetime
import time

def getConfigValue(key):
    return __dynamoClient.get_item(TableName='Config', Key={'Key': {'S': key}})['Item']['Value']['S']

def setConfigValue(key, value):
    __dynamoClient.put_item(TableName='Config', Item={'Key': {'S': key}, 'Value': {'S': value}})

def deleteConfigValue(key):
    __dynamoClient.delete_item(TableName='Config', Key={'Key': {'S': key}})

__dynamoClient = boto3.client('dynamodb')

def handle(event, context):
    calendarId = getConfigValue('GoogleCalendarId')
    oauthSecret = getConfigValue('GoogleOAuth2ClientSecret')
    oauthId = getConfigValue('GoogleOAuth2ClientId')
    oauthRedirectUri = getConfigValue('GoogleOAuth2RedirectUri')
    try:
        credentialJson = getConfigValue('GoogleOAuth2Credentials')
    except:
        credentialJson = None
    if (credentialJson is not None):
        credentials = Credentials.new_from_json(credentialJson)
    else:
        flow = OAuth2WebServerFlow(client_id=oauthId, client_secret=oauthSecret, scope='https://www.googleapis.com/auth/calendar', redirect_uri=oauthRedirectUri)
        flow.params['access_type'] = 'offline'
        auth_uri = flow.step1_get_authorize_url()
        webbrowser.open(auth_uri)
        raw_input()
        code = getConfigValue('GoogleOAuth2Code')
        credentials = flow.step2_exchange(code)
        setConfigValue('GoogleOAuth2Credentials', credentials.to_json())
    http_auth = credentials.authorize(httplib2.Http())
    calendar = build('calendar', 'v3', http=http_auth)
    resourceId = getConfigValue('GoogleCalendarResourceId')
    try:
        id = getConfigValue('GoogleCalendarWatchId')
    except:
        id = None
    if id is not None:
        calendar.channels().stop(body={'id': id, 'resourceId': resourceId}).execute()
    id = str(uuid.uuid1())
    setConfigValue('GoogleCalendarWatchId', id)
    expiration = datetime.datetime.utcnow() + datetime.timedelta(days=365)
    expirationUnix = time.mktime(expiration.timetuple()) * 1000
    body = {
            'kind': 'api#channel',
            'address': getConfigValue('GoogleWebhookAddress'),
            'type': 'web_hook',
            'id': id,
            'expiration': expirationUnix
            }
    try:
        print calendar.events().watch(calendarId=__calendarId, body=body).execute()
    except Exception as e:
        deleteConfigValue('GoogleCalendarWatchId')
        raise e

if __name__ == "__main__":
    handle(None, None)
