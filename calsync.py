#!/usr/bin/env python2
#VS Code commit test

from __future__ import print_function #run on py 2 & 3
import datetime
import time
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
SE_JSON = 'lib/se.json'
CS_JSON = 'lib/cs.json'
HOLIDAYS_JSON = 'lib/holidays.json'
EXCLUDE_WEEK = 7

def main():
    msg = "Hello"
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'u:c:s:ad', ['user=', 'calendar=', 'study=', 'add', 'delete'])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    cal = None
    study = None
    user = None

    service = auth() #Authorize so that the script can write to your account
    try:
        for opt, arg in opts:
            if opt in ('-u', '--user'):
                if arg == "def":
                    user = "aqlan"
                elif arg:
                    user = arg

            elif opt in ('-c', '--calendar'):
                if arg == "def":
                    cal = CALID
                elif arg:
                    cal = arg

            elif opt in ('-s', '--study'):
                if arg == "cs":
                    study = CS_JSON
                if arg == "se":
                    study = SE_JSON

            elif opt in ('-a', '--add'):
                if os.path.isfile(str(user+".txt")):
                    print("Existing schedule has already been loaded.")
                    sys.exit(2)
                else:
                    print("add passed")
                    print(user + cal, study)
                    addClasses(service, user, study, cal)

            elif opt in ('-d', '--delete'):
                f = str("lib/"+user+".txt")
                if os.path.isfile(f):
                    delAllEv(service, f, cal)
                else:
                    print("No event (event IDs) exists to delete")
                    sys.exit(2)
    except:
        notEnoughArg()
        sys.exit(2)

def addClasses(service, user, study, calendar):
    user = str("lib/" + user + ".txt")
    print("Process started at {0}".format(datetime.datetime.now().strftime("%X")))
    print("Adding classes to " + CALID)
    start = time.time()

    weekCount = 0
    with open(study,"r") as schedfile:
        schedule = json.load(schedfile)

    while weekCount < WEEK_COUNT:
        print("Week ", (weekCount+1))
        offset = 7 * weekCount

        #if got week break put here
        if weekCount == (EXCLUDE_WEEK-1):
            weekCount += 1
            print("###### cuti #####")
            continue

        rDay = dtConvert(str(schedule['classes'][0]['start']['dateTime'])) #Referenced from 1st day of class in JSON
        for c in schedule['classes']:
            #tDay is the day read from JSON (Current day on the 1st week of classes)
            #rDay is referenced day, to differentiate today and tomorrow in the context of first week
            tDay = dtConvert(str(c['start']['dateTime']))
            if tDay == rDay:
                addToCal(rDay + datetime.timedelta(days=offset), c, service, calendar, user)
            elif tDay > rDay:
                rDay = tDay
                addToCal(rDay + datetime.timedelta(days=offset), c, service, calendar, user)
            elif tDay < rDay:
                print("Next week")

        weekCount += 1

    end = time.time()
    print("Completed at {0}. Time elapsed {1}s".format(datetime.datetime.now().strftime("%X"), (end-start)))

def addToCal(today, c, service, calendar, user):
    #here u can check specific days -- holiday or not to exclude
    if holiday(today):
        print(str(today.strftime("%a")) + ", " + str(today) + " --Holiday")
    if not holiday(today):
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
        e = service.events().insert(calendarId=calendar,
            sendNotifications=False, body=curdict).execute()
        print(str(today.strftime("%a")) + ", " + str(today) + " --Class | Event created (evId) > " + (e.get('id')))
        with open(user, "a+") as f:
            f.write(e.get('id') + '\n')

def holiday(today):
    with open(HOLIDAYS_JSON,"r") as datelist:
        lists = json.load(datelist)
    #Goes through all values of 'date' to see if today matches.
    #if it matches, return true for today is holiday
    if any(tag['date'] == str(today) for tag in lists['holidays']):
        return True
    else:
        return False

def delAllEv(service, user, calendar):

    print("Process started at {0}".format(datetime.datetime.now().strftime("%X")))
    start = time.time()

    with open(user, "r") as fileHandler:
        line = fileHandler.readline()
        while line:
            service.events().delete(calendarId=calendar, eventId=line.strip()).execute()
            print(line.strip() + " deleted")
            line = fileHandler.readline()
    os.remove(user)

    end = time.time()
    print("Completed at {0}. Time elapsed {1}s".format(datetime.datetime.now().strftime("%X"), (end-start)))

def newDate(old, new):
    time = str(old[10:])
    return str(new)+time

def dtConvert(dateTime):
    year = int(dateTime[0:4])
    month = int(dateTime[5:7])
    day = int(dateTime[8:10])
    return datetime.datetime(year, month, day).date()

def notEnoughArg():
    print("usage: ./calsync.py -u [user] -c [calendar id] -s [class(se/cs)] -a|-d")
    sys.exit(2)

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
