import mechanize
import string
from BeautifulSoup import BeautifulSoup
from operator import itemgetter, attrgetter

class Hospitalist(object):
    """Keep track of single hospitalist's data
    """
    
    def __init__(self, name, current, total):
        self.name = name
        self.current = current
        self.total = total

    def __repr__(self):
        return self.name + ': ' + str(self.current) + ' of ' + str(self.total)

def shift_abbrev(long_shift):
    """Return abbreviated form of shift
    
    Arguments:
    - `long_shift`: shift name directly from amion
    """
    # could be improved, but serves our purposes for now

    # strip spaces and last word (usually 7a-6p)
    long_shift = string.join(long_shift.split()[:-1])
    if long_shift.startswith('Hosp'):
        return 'Day'
    return long_shift
    
def parse_schedule(data):
    """Parse HTML page from amion to get a dictionary with the schedule
    
    Arguments:
    - `data`: is the amion response (from mechanize)
    """
    soup = BeautifulSoup(data.get_data())

    # the second <table> has the data we need
    mytable = soup('table')[1]
    schedule = {}

    for tr in mytable('tr'):
        if tr.has_key('bgcolor') and tr['bgcolor'] == '#f6deac':
            # header rows have bgcolor='#f6deac'
            header = [] # will be used to match data rows to proper date
            # skip the first column because it's meaningless
            for td in tr('td')[1:]:
                if td.i:
                    # day of month is inside i & b tag
                    date = int(td.i.b.string)
                else:
                    date = 0
                header.append(date)
                schedule[date] = {}
        else:
            # data row
            # first column is the shift title. clean it up with shift_abbrev()
            shift = shift_abbrev(tr.td.i.string.replace('&nbsp;', ' '))

            # go through each column, using the dates that we got
            # from the header row
            for td, date in zip(tr('td')[1:], header):
                person = None
                if td.contents[0].__class__.__name__ == 'NavigableString':
                    # it's a raw string.
                    if td.contents[0] != '&nbsp;':
                        person = td.contents[0]
                else:
                    # the person we want is within a tag
                    person = td.contents[0].contents[0]

                    # look to see if there is a sticky note
                    if len(td.contents[0].contents) > 1:
                        notes = td.contents[0].contents[1]['title']

                if schedule[date].has_key(shift):
                    # append this person to the shift
                    schedule[date][shift].append(person)
                else:
                    # create the shift
                    schedule[date][shift] = [person]

    del schedule[0]
    return schedule

br = mechanize.Browser()
resp = br.open('file:amion4.html')
schedule = parse_schedule(resp)
resp = br.open('file:amion5.html')
schedule_next = parse_schedule(resp)
resp = br.open('file:amion3.html')
schedule_prev = parse_schedule(resp)

cur_month_length = len(schedule)
prev_month_length = len(schedule_prev)

# append next months schedule
for day in schedule_next:
    schedule[cur_month_length + day] = schedule_next[day]
# prepend last months schedule
for day in schedule_prev:
    schedule[day - prev_month_length] = schedule_prev[day]

# testing
orig = 22
print "April " + str(orig) + ":"
hosp_list = []
for hosp in schedule[orig]['Day']:
    day = orig
    current = total = 1
    while schedule[day-1]['Day'].count(hosp):
        current += 1
        total += 1
        day -= 1
    day = orig
    while schedule[day+1]['Day'].count(hosp):
        total +=1
        day += 1
    hosp_list.append(Hospitalist(hosp, current, total))

# sort by current, then total
hosp_list = sorted(hosp_list, key=attrgetter('total'), reverse=True)
hosp_list = sorted(hosp_list, key=attrgetter('current'))

for hosp in hosp_list:
    print hosp
