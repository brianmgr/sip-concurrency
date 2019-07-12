# twilio.com/docs/python/install
from twilio.rest import Client
import csv
import sqlite3
import argparse
from datetime import datetime, date, timedelta

# Create a table listing all calls, and their details, within requested time period
def callInsert( call ):
    callCursor.execute('''INSERT INTO calls(sid, date_created, start_time, end_time, to_formatted, from_formatted, direction, duration, status)VALUES(?,?,?,?,?,?,?,?,?)''', (call[0],call[1],call[2],call[3],call[4],call[5],call[6],call[7],call[8]))
    db.commit()

# Thought about creating a table of all 86400 seconds in a day, with a value of 0, but it's a bad idea.
# An empty table in a database with 0s takes 40 seconds to create and is 1.2MB in size.
# Will instead only add timestamps used during calls to table
def epochInsert( epoch ):
    epochCursor.execute('''INSERT OR IGNORE INTO epoch(epoch) VALUES(?)''', (epoch,))
    epochCursor.execute('''UPDATE epoch SET count = count + ? WHERE epoch = ?''', (1, epoch))
    db.commit()

# Convert timestamp to epoch
def epoch( stamp ):
    epoch = int(stamp.timestamp())
    return epoch

# Write rows to a CSV file on disk
def csvWriter(row):
    if not args.nocsv:
        with open(outputFile, 'a') as f:
                    writer = csv.writer(f)
                    writer.writerow(row)

# Input arguments
parser = argparse.ArgumentParser()
parser.add_argument('-nocsv', help='Do not export a csv file. Useful if only you want to see results on screen or make a sqlite3 db file.', required=False, action='store_true')
parser.add_argument('-datestart', help='Day in past the report should start in this format: YYYY-MM-DD.', required=False, metavar='')
parser.add_argument('-account_sid', help='Account SID retrieved from twilio.com/user/account', required=False, metavar='')
parser.add_argument('-auth_token', help='Auth Token retrieved from twilio.com/user/account', required=False, metavar='')
parser.add_argument('-verbose', help='Print full call logs to screen and write to sqlite3 database', required=False, action='store_true')
args = parser.parse_args()

# Default to yesterday's date if no date flag specified
yesterday = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')

# Parse input date
dateInput = None
if args.datestart:
    try:
        dateInput = args.datestart
        dateInput = datetime.strptime(dateInput, '%Y-%m-%d')
    except:
        print('\nPlease make sure your timestamp is a real date and is in this format: YYYY-MM-DD.')

# Prompt for credentials if not found
if not (args.account_sid or args.auth_token):
    print('\nPlease provide credentials with the -account_sid and -auth_token flags and try again.\nThese can be found at twilio.com/user/account ')
    quit()


# Make sure user can pull logs before continuing
try:
    # Init Twilio API client
    client = Client(args.account_sid, args.auth_token)
    
    # Get call logs
    calls = None
    if not args.datestart:
        calls = client.calls.list(start_time_after=yesterday)
    else:
        calls = client.calls.list(start_time_after=dateInput)
except:
    print("\nSorry, there was an error retrieving logs. Please check your credentials and try again.")
    quit()

# SQLite3 database naming
now = str(datetime.now())[:19]
now = now.replace(" ", "_run_at_")
now = now.replace(":", ".")
dbName = '%s_%s.db' % (args.account_sid, now)
if not args.nocsv:
    outputFile = '%s.csv' % (dbName)

# Make and open database
db = sqlite3.connect(dbName)
callCursor = db.cursor()
if args.verbose:
    callCursor.execute('''CREATE TABLE IF NOT EXISTS calls(sid TEXT PRIMARY KEY, date_created TEXT, start_time TEXT, end_time TEXT, to_formatted TEXT, from_formatted TEXT, direction TEXT, duration TEXT, status TEXT)''')
epochCursor = db.cursor()
epochCursor.execute('''CREATE TABLE IF NOT EXISTS epoch(epoch INTEGER PRIMARY KEY, count INTEGER NOT NULL DEFAULT 0)''')

# Iterate through call logs
for call in calls:
    # Only look at Elastic SIP Trunking calls that didn't fail
    if "trunking" in call.direction and call.status != "failed":
        epochStart = epoch(call.start_time)
        epochEnd = epoch(call.end_time)
        delta = epochEnd - epochStart # Duration of call
        
        # Put call details in array
        callDetails = [
            call.sid,
            call.date_created,
            call.start_time,
            call.end_time,
            call.to_formatted,
            call.from_formatted,
            call.direction,
            call.duration,
            call.status
        ]

        # Insert call details in table 'calls'
        if args.verbose:
            callInsert(callDetails)
            print(call.sid, epochStart, epochEnd, delta, call.date_created, call.start_time, call.end_time, call.to_formatted, call.from_formatted, call.direction, call.duration, call.status)

        if delta > 0: # Remove 0 second calls
            while epochStart <= epochEnd + 1: # Iterate through seconds of each call
                # For each second of call, lookup epoch second in table and increment it by one
                # eg: if two calls happened on second "1561939200", a SELECT on the timestamp would produce "2"
                epochInsert(epochStart)
                # print(epochStart)
                epochStart += 1

# Get top ten seconds which had concurrent SIP calls happening from 'epoch' table
topSeconds = epochCursor.execute('''SELECT epoch, sum(count) FROM epoch group by epoch ORDER BY CAST(sum(count) AS INTEGER) DESC limit 25''')
print('\nTop seconds in epoch which incurred the most consecutive calls:\n')
print('TIMESTAMP    COUNT')
csvWriter(['TIMESTAMP','COUNT'])

# Iterate through top seconds, print and add to CSV file if necessary
for second in topSeconds:
    timestamp = str(second[0])
    count = str(second[1])
    row = '%s   %s' % (timestamp, count)
    print(row)

    csvWriter([timestamp,count])

# Print reminder to user that they should delete database
print('\nThe following sqlite3 database file has been written to disk for data analysis:\n%s\nTo save space, you may want to delete this.\n' % (dbName))
