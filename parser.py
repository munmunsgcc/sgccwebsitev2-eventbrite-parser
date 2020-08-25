from dateutil.parser import *
from dateutil.rrule import *
from datetime import *
from fractions import Fraction
import coursesInfo
import os

# Converts date to unix milliseconds


def convertDateToUnixMS(date):
    utctimestamp = datetime.utcfromtimestamp(0)
    return int((date - utctimestamp).total_seconds() * 1000)

# Converts number to corresponding day of the week


def intToDay(number):
    if number == 0:
        return 'Mon'
    elif number == 1:
        return 'Tue'
    elif number == 2:
        return 'Wed'
    elif number == 3:
        return 'Thu'
    elif number == 4:
        return 'Fri'
    elif number == 5:
        return 'Sat'
    elif number == 6:
        return 'Sun'

# Converts number to corresponding month


def intToMonth(number):
    if number == 1:
        return 'Jan'
    elif number == 2:
        return 'Feb'
    elif number == 3:
        return 'Mar'
    elif number == 4:
        return 'Apr'
    elif number == 5:
        return 'May'
    elif number == 6:
        return 'Jun'
    elif number == 7:
        return 'July'
    elif number == 8:
        return 'Aug'
    elif number == 9:
        return 'Sep'
    elif number == 10:
        return 'Oct'
    elif number == 11:
        return 'Nov'
    elif number == 12:
        return 'Dec'

# Returns the type of courses


def getCourseType(nameList, date):
    courseType = ''

    for word in nameList:
        if courseType == '' and word.find('Holiday') > -1 or word.find('holiday') > -1 or word.find('Camp') > - 1 or word.find('camp') > -1:
            courseType = 'Holiday Camp'
        if word.find('Sat') > -1 or word.find('Sun') > -1 or word.find('sat') > -1 or word.find('sun') > -1:
            courseType = 'Weekend Weekly'

    if courseType == '':
        courseType = 'Weekday Weekly'

    return courseType

# Based on course type, return the correct course prices


def getCoursePrices(courseNameId, courseType, courseLocation, prices=coursesInfo.prices):
    price = ''
    courseNamePrice = prices[courseNameId]
    earlyBirdDiscount = prices['earlyBirdDiscount']
    weekdayDiscount = prices['weekdayDiscount']
    earlyBird = False

    if courseLocation == 'Not applicable':
        price = 0
        earlyBird = False
    elif courseType == 'Weekend Weekly':
        price = courseNamePrice['weekly']
        earlyBird = courseNamePrice['earlyBird']['weekly'] if 'earlyBird' in courseNamePrice and 'weekly' in courseNamePrice['earlyBird'] else False
    elif courseType == 'Weekday Weekly':
        price = courseNamePrice['weekly'] - weekdayDiscount
        earlyBird = courseNamePrice['earlyBird']['weekly'] if 'earlyBird' in courseNamePrice and 'weekly' in courseNamePrice['earlyBird'] else False
    elif courseType == 'Holiday Camp':
        price = courseNamePrice['camp']
        earlyBird = courseNamePrice['earlyBird']['camp'] if 'earlyBird' in courseNamePrice and 'camp' in courseNamePrice['earlyBird'] else False

    return {'main': price, 'earlyBird': earlyBird}

# Get course's time, date and day of the week


def getCourseTiming(localDate, strUTCDate):
    return {
        "date": convertDateToUnixMS(strUTCDate),
        "day": intToDay(localDate.weekday()),
        "time": localDate.strftime('%I:%M%p').lstrip('0').lower()
    }

# Sets the course session length
# Format in total hours and minutes are in fraction


def getCourseSessionLength(start, end, type):
    courseHourLength = end.hour - start.hour
    courseMinuteLength = end.minute - start.minute

    if type == 'Holiday Camp' and courseHourLength >= 4:
        return '{}'.format(4)
    elif courseMinuteLength > 0:
        courseMinuteLength = format(Fraction(courseMinuteLength * 1/60))
        return '{} {}'.format(courseHourLength, courseMinuteLength)
    else:
        return '{}'.format(courseHourLength)

# Accepts data from the EventBrite API call response, any skipped days from
# the CLI argument and an outside object for us to add events to.


def standardJSONParser(data, skippedDays, parsedResponses):
    nameList = data['name']['text'].split(' ')
    fullEventDates = []
    set = rruleset()
    unixSkippedDays = []
    nameThreeWords = "Introduction to Junior Python"

    # Set how best we should parse the name
    # Usually it's Basics 2 or Principles 2, but lately we have Junior Python 1
    selectedArr = nameList[0:3] if nameList[0] in nameThreeWords else nameList[0:2]

    # Set course name and id, whatever needed to identify the course
    courseNameTitle = ' '.join(selectedArr)
    courseNameId = (''.join(selectedArr).lower()).replace(':', '')

    # Set other course info, such as the url to buy ticket, the location
    courseLocation = 'Marine Parade' if ('@MP' in nameList) else 'Bukit Timah'
    if 'ONLINE:' in nameList or 'ONLINE' in nameList or 'online' in nameList:
        courseLocation = 'Not applicable'
    elif '@MP' in nameList:
        courseLocation = 'Marine Parade'
    else:
        courseLocation = 'Bukit Timah'

    courseId = data['id']
    courseURL = data['url']

    # Set course start timing
    courseStart = parse(data['start']['local'])
    courseStartTiming = getCourseTiming(
        courseStart, parse(data['start']['utc'].replace('Z', '')))
    courseStartObject = datetime.combine(
        courseStart.date(), courseStart.min.timetz())

    # Set course end timing
    courseEnd = parse(data['end']['local'])
    courseEndTiming = getCourseTiming(
        courseEnd, parse(data['end']['utc'].replace('Z', '')))

    # Is the course a Holiday Camp or a Weekendly Weekly?
    # Also sets the course pricing
    courseType = getCourseType(nameList, courseStart)
    coursePrice = getCoursePrices(courseNameId, courseType, courseLocation)

    # Get total days and dates of the course length
    # For holiday camps, it is done daily, else it is on every week
    if courseType == 'Holiday Camp':
        setRule = rrule(DAILY, interval=1, until=courseEnd,
                        dtstart=courseStartObject)
    else:
        setRule = rrule(DAILY, interval=7, until=courseEnd,
                        dtstart=courseStartObject)

    set.rrule(setRule)

    # We have the dates already, so we just need to convert them to Unix milliseconds
    for day in skippedDays:
        set.exdate(parse(day, dayfirst=True))
        unixSkippedDays.append(convertDateToUnixMS(parse(day, dayfirst=True)))

    for date in list(set):
        fullEventDates.append(convertDateToUnixMS(date))

    # Set recommenderOnly, and other info such as subtitles, names, etc.
    # This is for overall course info.
    if courseNameTitle not in parsedResponses:
        # Add events array
        parsedResponses[courseNameTitle] = {
            "events": []
        }

    # Add the dates for the event
    # This is for the course's 1 event. Events are stored in an array.
    fullDates = {
        "startDate": courseStartTiming['date'],
        "endDate": courseEndTiming['date'],
        "startDay": courseStartTiming['day'],
        "endDay": courseEndTiming['day'],
        "sessionLength": getCourseSessionLength(courseStart, courseEnd, courseType),
        "sessionNumOfDays": len(fullEventDates),
        "day": "Weekends" if courseStartTiming['day'] in ["Sat", "Sun"] else "Weekdays",
        "full": fullEventDates,
    }

    # Does this event have skipped days? Only added if yes.
    if len(unixSkippedDays) > 0:
        fullDates['skipped'] = unixSkippedDays

    # Add the event to the array
    parsedResponses[courseNameTitle]['events'].append(
        {
            "type": courseType if courseType == 'Holiday Camp' else 'Weekly Classes',
            "dates": fullDates,
            "time": {
                "start": courseStartTiming['time'],
                "end": courseEndTiming['time']
            },
            "location": courseLocation,
            "price": coursePrice,
            "url": courseURL
        })

    # return the passed in object
    return parsedResponses


def customJSONParser(data, skippedDays, parsedResponses):
    nameList = data['name']['text'].split(' ')
    fullEventDates = []
    set = rruleset()
    unixSkippedDays = []

    # Set course name
    courseNameTitle = data['name']['text']

    # Set other course info
    courseLocation = 'Marine Parade' if '@MP' in nameList else 'Bukit Timah'
    courseId = data['id']
    courseURL = data['url']

    # Set course start timing
    courseStart = parse(data['start']['local'])
    courseStartTiming = getCourseTiming(
        courseStart, parse(data['start']['utc'].replace('Z', '')))
    courseStartObject = datetime.combine(
        courseStart.date(), courseStart.min.timetz())

    # Set course end timing
    courseEnd = parse(data['end']['local'])
    courseEndTiming = getCourseTiming(
        courseEnd, parse(data['end']['utc'].replace('Z', '')))

    # Is the course a Holiday Camp or a Weekendly Weekly?
    courseType = getCourseType(nameList, courseStart)
    coursePrice = {"main": "", "earlyBird": False}

    # Get total days and dates of the course length
    # For holiday camps, it is done daily, else it is on every week
    if courseType == 'Holiday Camp':
        setRule = rrule(DAILY, interval=1, until=courseEnd,
                        dtstart=courseStartObject)
    else:
        setRule = rrule(DAILY, interval=7, until=courseEnd,
                        dtstart=courseStartObject)

    set.rrule(setRule)

    # We have the dates already, so we just need to convert them to Unix milliseconds
    for day in skippedDays:
        set.exdate(parse(day, dayfirst=True))
        unixSkippedDays.append(convertDateToUnixMS(parse(day, dayfirst=True)))

    for date in list(set):
        fullEventDates.append(convertDateToUnixMS(date))

    # This is for overall course info.
    if courseNameTitle not in parsedResponses:
        parsedResponses[courseNameTitle] = {
            "events": []
        }

    # Add the dates for the event
    fullDates = {
        "startDate": courseStartTiming['date'],
        "endDate": courseEndTiming['date'],
        "startDay": courseStartTiming['day'],
        "endDay": courseEndTiming['day'],
        "sessionLength": getCourseSessionLength(courseStart, courseEnd, courseType),
        "sessionNumOfDays": len(fullEventDates),
        "day": "Weekends" if courseStartTiming['day'] in ["Sat", "Sun"] else "Weekdays",
        "full": fullEventDates,
    }

    # Does this event have skipped days? Only added if yes.
    if len(unixSkippedDays) > 0:
        fullDates['skipped'] = unixSkippedDays

    # Add the event to the array
    parsedResponses[courseNameTitle]['events'].append(
        {
            "type": courseType if courseType == 'Holiday Camp' else 'Weekly Classes',
            "dates": fullDates,
            "time": {
                "start": courseStartTiming['time'],
                "end": courseEndTiming['time']
            },
            "location": courseLocation,
            "price": coursePrice,
            "url": courseURL
        })

    # return the passed in object
    return parsedResponses


def chooseParser(data, skippedDays, parsedResponses):
    courseName = data['name']['text']
    foundCourse = False

    for name in coursesInfo.standardCourses:
        if name in courseName and foundCourse == False:
            foundCourse = True

    if foundCourse == True:
        return standardJSONParser(data, skippedDays, parsedResponses)
    else:
        return customJSONParser(data, skippedDays, parsedResponses)
