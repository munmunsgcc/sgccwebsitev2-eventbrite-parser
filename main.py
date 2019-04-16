
import sys
import json
import urllib.request
from datetime import *
from JSONParser import JSONParser

links = open('input.txt', 'r').readlines()
token = open('token.txt', 'r').readline()
eventIds = []
eventBriteResponses = []
eventBriteToken = '?token=' + token
eventBriteAPIURL = 'https://www.eventbriteapi.com/v3/events/'
skippedDays = sys.argv[1:] or []
parsedResponses = {}


# Find a way to get total hours/minutes also
# Convert all dates to UNIX time
# Make a nice JSON object with all events in it instead of looping


def getEventId(url):
    return url.split('-')[-1].strip()


for link in links:
    eventIds.append(getEventId(link))

for eventId in eventIds:
    fullURL = eventBriteAPIURL + eventId + eventBriteToken
    response = urllib.request.urlopen(fullURL).read()
    formattedResponse = json.loads(response)
    eventBriteResponses.append(formattedResponse)

for eventBriteResponse in eventBriteResponses:
    parsedResponses = JSONParser(
        eventBriteResponse, skippedDays, parsedResponses)

with open('output.json', 'w') as outputFile:
    json.dump(parsedResponses, outputFile)
