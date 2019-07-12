# sip-concurrency
Find the largest amount of concurrent calls in Twilio's Elastic SIP Trunking offering.

## What it does
This script pulls down all call logs from a date in the past until now and finds the calls which are using Twilio's Elastic SIP Trunking offering. Once logs have been gathered, the calls are parsed to find their begin and end times. Each second between these two times is converted to epoch, and used to increment a counter in a sqlite3 table. After all 'active' timestamps have had their usage logged, a CSV file it output to the directory of the script. This CSV file shows the top 25 timestamps in which concurrent calls took place, along with the value.

## Requirements
- Python 3
- Twilio Python helper library (twilio.com/docs/python/install)
- Privileges to write to disk (db and csv files)

## Flags
`-nocsv` Do not export a CSV file. Useful if only you want to see results on screen or make a sqlite3 db file

`-datestart` Day in past the report should start in this format: YYYY-MM-DD. Will default to yesterday if not defined.

`-account_sid` *REQUIRED* Account SID retrieved from twilio.com/user/account

`-auth_token` *REQUIRED* Auth Token retrieved from twilio.com/user/account

`-verbose` Print full call logs to screen and write to sqlite3 database

## Usage
Getting yesterday's highest concurrent sip calls and writing the result to a CSV file:

- `python3 sip-concurrency.py -account_sid AC1aeaeaeaeaeaeaeaeaeaeaeaeaeaeaea -auth_token 10101001010101010101010101010101`

Getting the highest concurrent sip calls since 5/29/2019. Don't write a CSV file to disk:

- `python3 sip-concurrency.py -datestart 2019-05-29 -nocsv -account_sid AC1aeaeaeaeaeaeaeaeaeaeaeaeaeaeaea -auth_token 10101001010101010101010101010101`

## Output File naming convention
sqlite3 database

- `AC1aeaeaeaeaeaeaeaeaeaeaeaeaea_2019-07-12_run_at_16.39.42.db`

CSV file

- `AC1aeaeaeaeaeaeaeaeaeaeaeaeaea_2019-07-12_run_at_16.39.42.db.csv`

## Output file hygiene
This script writes CSV and DB files to file every time it runs.
For safety, it _DOES NOT_ remove these files after the script has run.
You should set up a cron job or something similar to prune these files at certain intervals.

