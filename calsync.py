#!/usr/bin/env python2

from __future__ import print_function #run on py 2 & 3
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar']
GMT_OFF = '+08:00'
EVENT = {
    'summary':'TEST',
    'start': {'dateTime': '2019-04-01T19:00:00%s' % GMT_OFF},
    'end': {'dateTime': '2019-04-01T22:00:00%s' % GMT_OFF}
}
CALID = "k26iavm5k4vpfieeg0ne8937us@group.calendar.google.com"

def main():
    service = auth()

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])

    e = service.events().insert(calendarId=CALID,
        sendNotifications=False, body=EVENT).execute()

    print(e)


def auth():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server()
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

if __name__ == '__main__':
    main()
