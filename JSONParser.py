from dateutil.parser import *
from dateutil.rrule import *
from datetime import *
from fractions import Fraction
import coursesInfo


def convertDateToUnixMS(date):
    utctimestamp = datetime.utcfromtimestamp(0)
    result = str((date - utctimestamp).total_seconds() * 1000)

    return result.replace(".0", "")


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


def getCourseType(nameList, date):
    courseType = ''

    if 'Holiday' in nameList or 'Camp' in nameList:
        courseType = 'Holiday Camp'
    elif 'Weekly' in nameList and (intToDay(date.weekday()) == 'Sat' or intToDay(date.weekday()) == 'Sun'):
        courseType = 'Weekend Weekly'
    else:
        courseType = 'Weekday Weekly'

    return courseType


def getCoursePrices(courseNameId, courseType, prices=coursesInfo.prices):
    price = ''
    courseNamePrice = prices[courseNameId]
    earlyBirdDiscount = prices['earlyBirdDiscount']
    weekdayDiscount = prices['weekdayDiscount']
    earlyBird = False

    if courseType == 'Weekend Weekly':
        price = f"SGD{courseNamePrice['weekly']}"
        earlyBird = courseNamePrice['earlyBird']['weekly'] if 'earlyBird' in courseNamePrice and 'weekly' in courseNamePrice['earlyBird'] else False
    elif courseType == 'Weekday Weekly':
        price = f"SGD{courseNamePrice['weekly'] - weekdayDiscount}"
        earlyBird = courseNamePrice['earlyBird']['weekly'] if 'earlyBird' in courseNamePrice and 'weekly' in courseNamePrice['earlyBird'] else False
    elif courseType == 'Holiday Camp':
        price = f"SGD{courseNamePrice['camp']}"
        earlyBird = courseNamePrice['earlyBird']['camp'] if 'earlyBird' in courseNamePrice and 'camp' in courseNamePrice['earlyBird'] else False

    return {'main': price, 'earlyBird': earlyBird}


def getCourseTiming(localDate, strUTCDate):
    return {
        "date": convertDateToUnixMS(strUTCDate),
        "day": intToDay(localDate.weekday()),
        "time": localDate.strftime('%I:%M%p').lstrip('0').lower()
    }


def JSONParser(data, skippedDays, parsedResponses):
    nameList = data['name']['text'].split(' ')
    fullEventDates = []
    set = rruleset()
    unixSkippedDays = []

    courseNameTitle = ' '.join(nameList[0:2])
    courseNameId = ''.join(nameList[0:2]).lower()
    courseLocation = 'Marine Parade' if ('@MP' in nameList) else 'Bukit Timah'
    courseId = data['id']
    courseURL = data['url']

    courseStart = parse(data['start']['local'])
    courseStartTiming = getCourseTiming(
        courseStart, parse(data['start']['utc'].replace('Z', '')))
    courseStartObject = datetime.combine(
        courseStart.date(), courseStart.min.timetz())

    courseEnd = parse(data['end']['local'])
    courseEndTiming = getCourseTiming(
        courseEnd, parse(data['end']['utc'].replace('Z', '')))

    courseType = getCourseType(nameList, courseStart)
    coursePrice = getCoursePrices(courseNameId, courseType)

    courseHourLength = courseEnd.hour - courseStart.hour
    courseMinuteLength = courseEnd.minute - courseStart.minute

    print(courseHourLength, courseMinuteLength)

    if courseMinuteLength > 0:
        courseMinuteLength = Fraction(courseMinuteLength * 1/60)

    if courseType == 'Holiday Camp':
        setRule = rrule(DAILY, interval=1, until=courseEnd,
                        dtstart=courseStartObject)
    else:
        setRule = rrule(DAILY, interval=7, until=courseEnd,
                        dtstart=courseStartObject)

    set.rrule(setRule)

    for day in skippedDays:
        set.exdate(parse(day, dayfirst=True))
        unixSkippedDays.append(convertDateToUnixMS(parse(day)))

    for date in list(set):
        fullEventDates.append(convertDateToUnixMS(date))

    if courseNameTitle not in parsedResponses:
        parsedResponses[courseNameTitle] = {"events": []}

    parsedResponses[courseNameTitle]['events'].append(
        {
            "type": courseType,
            "dates": {
                "startDate": courseStartTiming['date'],
                "endDate": courseEndTiming['date'],
                "startDay": courseStartTiming['day'],
                "endDay": courseEndTiming['day'],
                "sessionLength": "{} {}".format(courseHourLength, '' if courseMinuteLength == 0 else courseMinuteLength),
                "sessionNumOfDays": len(fullEventDates),
                "day": "Weekends" if courseStartTiming['day'] in ["Sat", "Sun"] else "Weekdays",
                "full": fullEventDates,
                "skipped": unixSkippedDays or [],
            },
            "time": {
                "start": courseStartTiming['time'],
                "end": courseEndTiming['time']
            },
            "location": courseLocation,
            "price": coursePrice,
            "url": courseURL
        })

    return parsedResponses
