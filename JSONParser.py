from dateutil.parser import *
from dateutil.rrule import *
from datetime import *
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

    if 'Holiday' in nameList:
        courseType = 'Holiday Camp'
    elif 'Weekly' in nameList and (intToDay(date.weekday()) == 'Sat' or intToDay(date.weekday()) == 'Sun'):
        courseType = 'Weekend Weekly'
    else:
        courseType = 'Weekday Weekly'

    return courseType


def getCoursePrices(courseName, courseType, prices=coursesInfo.prices):
    price = {"main": '', "earlyBird": ''}
    courseNamePrice = prices[courseName['id']]
    earlyBirdDiscount = prices['earlyBirdDiscount']
    weekdayDiscount = prices['weekdayDiscount']

    if courseType == 'Weekend Weekly':
        price['main'] = f"SGD{courseNamePrice['weekly']}"
        price['earlyBird'] = f"SGD{courseNamePrice['weekly'] - earlyBirdDiscount}"
    elif courseType == 'Weekday Weekly':
        price['main'] = f"SGD{courseNamePrice['weekly'] - weekdayDiscount}"
        price["earlyBird"] = f"SGD{courseNamePrice['weekly'] - weekdayDiscount - earlyBirdDiscount}"
    elif courseType == 'Holiday Camp':
        price["main"] = f"SGD{courseNamePrice['camp']}"
        price["earlyBird"] = f"SGD{courseNamePrice['camp'] - earlyBirdDiscount}"

    return price


def getCourseTiming(localDate, strUTCDate):
    return {
        "date": convertDateToUnixMS(strUTCDate),
        "day": intToDay(localDate.weekday()),
        "time": localDate.strftime('%I:%M%p').lstrip('0').lower()
    }


def JSONParser(data, skippedDays):
    nameList = data['name']['text'].split(' ')
    fullEventDates = []
    set = rruleset()

    courseName = {"title": ' '.join(nameList[0:2]),
                  "id": ''.join(nameList[0:2]).lower(),
                  "name": ''.join(nameList[0:2])}
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
    coursePrice = getCoursePrices(courseName, courseType)

    courseHourLength = courseEnd.hour - courseStart.hour
    courseMinuteLength = courseEnd.minute - courseStart.minute

    if courseMinuteLength > 0:
        courseMinuteLength = courseMinuteLength * 1/60

    if courseType == 'Holiday Camp':
        setRule = rrule(DAILY, interval=1, until=courseEnd,
                        dtstart=courseStartObject)
    else:
        setRule = rrule(DAILY, interval=7, until=courseEnd,
                        dtstart=courseStartObject)

    set.rrule(setRule)

    for i in range(len(skippedDays)):
        set.exdate(parse(skippedDays[i], dayfirst=True))
        skippedDays[i] = convertDateToUnixMS(parse(skippedDays[i]))

    for date in list(set):
        fullEventDates.append(convertDateToUnixMS(date))

    return {
        "courseName": courseName['name'],
        "courseTitle": courseName['title'],
        "events": [
            {
                "type": courseType,
                "dates": {
                    "startDate": courseStartTiming['date'],
                    "endDate": courseEndTiming['date'],
                    "startDay": courseStartTiming['day'],
                    "endDay": courseEndTiming['day'],
                    "sessionLength": "{}{}".format(courseHourLength, '' if courseMinuteLength == 0 else courseMinuteLength),
                    "sessionNumOfDays": len(fullEventDates),
                    "day": "Weekends" if courseStartTiming['day'] in ["Sat", "Sun"] else "Weekdays",
                    "full": fullEventDates,
                    "skipped": skippedDays or "none",
                },
                "time": {
                    "start": courseStartTiming['time'],
                    "end": courseEndTiming['time']
                },
                "location": courseLocation,
                "price": coursePrice,
                "url": courseURL
            }
        ]
    }
