#!/usr/bin/env python2

from __future__ import print_function #run on py 2 & 3
import datetime
import pickle
import json
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar']
GMT_OFF = 'Asia/Kuala_Lumpur'
CALID = "k26iavm5k4vpfieeg0ne8937us@group.calendar.google.com" #Taylor's Calendar ID

def main():
    service = auth()
    #addEv(service)
    delAllEv(service)

def addEv(service):
    f = open("eveId.txt", "a+")
    with open("localization.json","r") as schedfile:
        schedule = json.load(schedfile)

    for c in schedule['classes']:
        curdict = {
            'summary':c['summary'],
            'location':c['location'],
            'description':c['description'],
            'start': {
                'dateTime':str(c['start']['dateTime']),
                'timeZone': GMT_OFF,
            },
            'end': {
                'dateTime':str(c['end']['dateTime']),
                'timeZone': GMT_OFF,
            }
        }
        print(curdict['end'])
        e = service.events().insert(calendarId=CALID,
            sendNotifications=False, body=curdict).execute()
        f.write(e.get('id') + '\n')

def delAllEv(service):
    with open("eveId.txt", "r") as fileHandler:
        line = fileHandler.readline()
        while line:
            print(line.strip())
            service.events().delete(calendarId=CALID, eventId=line.strip()).execute()
            line = fileHandler.readline()
    open("eveId.txt","rw")

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
