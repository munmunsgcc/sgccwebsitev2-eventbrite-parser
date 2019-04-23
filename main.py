
import sys
import json
import urllib.request
from datetime import *
from JSONParser import JSONParser

# Open and read the input.txt for list of links
links = open('input.txt', 'r').readlines()
# Open and read the token.txt for the Eventbrite API token
token = open('token.txt', 'r').readline()

# Init variables to store items
eventIds = []
eventBriteResponses = []
eventBriteToken = '?token=' + token
eventBriteAPIURL = 'https://www.eventbriteapi.com/v3/events/'
skippedDays = sys.argv[1:] or []
parsedResponses = {}

# Returns event ID from the url


def getEventId(url):
    return url.split('-')[-1].strip()


# Get all event IDs
for link in links:
    eventIds.append(getEventId(link))

# Ping the Eventbrite servers and store their response in eventBriteResponses list
for eventId in eventIds:
    fullURL = eventBriteAPIURL + eventId + eventBriteToken
    response = urllib.request.urlopen(fullURL).read()
    formattedResponse = json.loads(response)
    eventBriteResponses.append(formattedResponse)

# parse the responses one by one, while passing in the parsedResponses object
# again and again
for eventBriteResponse in eventBriteResponses:
    parsedResponses = JSONParser(
        eventBriteResponse, skippedDays, parsedResponses)

# We have now completely parsed the returned Eventbrite responses.
# Convert it to json and add it into a json file
with open('output.json', 'w') as outputFile:
    json.dump(parsedResponses, outputFile)
