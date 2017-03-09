from googleapiclient.discovery import build
from oauth2client.client import Credentials
import boto3
import httplib2
import datetime
import requests

def getConfigValue(key):
    return __dynamoClient.get_item(TableName='Config', Key={'Key': {'S': key}})['Item']['Value']['S']

def week():
    '''
    Since isoformat() returns time in ISO 8601 format, and Google expects RFC3339 (mandatory timezone), add Z to the output
    '''
    return (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat() + 'Z'

def now():
    '''
    Since isoformat() returns time in ISO 8601 format, and Google expects RFC3339 (mandatory timezone), add Z to the output
    '''
    return datetime.datetime.utcnow().isoformat() + 'Z'

def format_time(time):
    return datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S UTC')

__dynamoClient = boto3.client('dynamodb')

def handler(event, context):
    print event
    calendarId = getConfigValue('GoogleCalendarId')
    credentialJson = getConfigValue('GoogleOAuth2Credentials')
    discordWebhookUri = getConfigValue('DiscordWebhookUri')
    credentials = Credentials.new_from_json(credentialJson)
    http_auth = credentials.authorize(httplib2.Http())
    calendar = build('calendar', 'v3', http=http_auth)
    content = "The Maximum Overchill stream calendar has updated! Here are the streams for the next week:\n\n"
    for item in calendar.events().list(calendarId=calendarId, timeMin=now(), timeMax=week(), singleEvents=True, orderBy='startTime').execute()['items']:
        itemContent = ""
        itemContent = itemContent + 'Title:\t' + item['summary'] + '\n'
        itemContent = itemContent + 'Start:\t' + format_time(item['start']['dateTime']) + '\n'
        itemContent = itemContent + 'End:\t' + format_time(item['end']['dateTime']) + '\n'
        if ('description' in item):
            itemContent = itemContent + item['description'] + '\n'
        itemContent = itemContent + '\n'
        if ((len(itemContent) + len(content)) >= 2000):
            r = requests.post(discordWebhookUri, data={'content': content})
            content = itemContent
        else:
            content = content + itemContent
    r = requests.post(discordWebhookUri, data={'content': content})

if __name__ == "__main__":
    handler(None, None)
