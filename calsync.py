#!/usr/bin/env python2

from __future__ import print_function #run on py 2 & 3
import datetime
import pickle
import json
import os
import getopt
import sys
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar']
GMT_OFF = 'Asia/Kuala_Lumpur'
CALID = "k26iavm5k4vpfieeg0ne8937us@group.calendar.google.com" #Taylor's Calendar ID
WEEK_COUNT = 14
STORE_FILE = "eveId.txt"
SCHEDULE_JSON = "localization.json"
HOLIDAYS_JSON = 'holidays.json'

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'adc:h', ['add', 'delete', 'calId=','help'])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    service = auth() #Authorize so that the script can write to your account
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            printHelp()
            sys.exit(2)
        elif opt in ('-a', '--add'):
            if os.path.isfile(STORE_FILE):
                print("Existing schedule has already been loaded.")
                sys.exit(2)
            else:
                print("Adding classes to " + CALID)
                addClasses(service)
        elif opt in ('-d', '--delete'):
            if os.path.isfile(STORE_FILE):
                delAllEv(service)
            else:
                print("No event (event IDs) exists to delete")
                sys.exit(2)
        else:
            sys.exit(2)

def printHelp():
    print("Hi just chillin here")

def addClasses(service):
    weekCount = 0


    with open(SCHEDULE_JSON,"r") as schedfile:
        schedule = json.load(schedfile)

    while weekCount < WEEK_COUNT:
        print("Week %d", (weekCount+1))
        offset = 7 * weekCount

        #if got week break put here
        if weekCount == 6:
            weekCount += 1
            print("###### cuti #####")
            continue

        rDay = dtConvert(str(schedule['classes'][0]['start']['dateTime'])) #Referenced from 1st day of class in JSON
        for c in schedule['classes']:
            #tDay is the day read from JSON (Current day on the 1st week of classes)
            #rDay is referenced day, to differentiate today and tomorrow in the context of first week
            tDay = dtConvert(str(c['start']['dateTime']))
            if tDay == rDay:
                addToCal(rDay + datetime.timedelta(days=offset), c, service)
            elif tDay > rDay:
                rDay = tDay
                addToCal(rDay + datetime.timedelta(days=offset), c, service)
            elif tDay < rDay:
                print("Next week")

        weekCount += 1


def addToCal(today, c, service):
    #here u can check specific days -- holiday or not to exclude
    if holiday(today):
        print(str(today.strftime("%a")) + ", " + str(today) + " --Holiday")
    if not holiday(today):
        print(str(today.strftime("%a")) + ", " + str(today) + " --Class")
        # print("Old time" + str(item['start']['dateTime']))
        # print("new time" + newDate(item['start']['dateTime'], today))
        curdict = {
            'summary':c['summary'],
            'location':c['location'],
            'description':c['description'],
            'start': {
                'dateTime':newDate(c['start']['dateTime'],today),
                #'dateTime':str(c['start']['dateTime']),
                'timeZone': GMT_OFF,
            },
            'end': {
                'dateTime':newDate(c['end']['dateTime'],today),
                'timeZone': GMT_OFF,
            }
        }
        e = service.events().insert(calendarId=CALID,
            sendNotifications=False, body=curdict).execute()
        with open(STORE_FILE, "a+") as f:
            f.write(e.get('id') + '\n')

def newDate(old, new):
    time = str(old[10:])
    return str(new)+time

def holiday(today):
    with open(HOLIDAYS_JSON,"r") as datelist:
        lists = json.load(datelist)
    #Goes through all values of 'date' to see if today matches.
    #if it matches, return true for today is holiday
    if any(tag['date'] == str(today) for tag in lists['holidays']):
        return True
    else:
        return False

def delAllEv(service):
    with open(STORE_FILE, "r") as fileHandler:
        line = fileHandler.readline()
        while line:
            print(line.strip())
            service.events().delete(calendarId=CALID, eventId=line.strip()).execute()
            line = fileHandler.readline()
    os.remove(STORE_FILE)

def dtConvert(dateTime):
    year = int(dateTime[0:4])
    month = int(dateTime[5:7])
    day = int(dateTime[8:10])
    return datetime.datetime(year, month, day).date()

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
