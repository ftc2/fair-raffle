#!/usr/bin/env python
# -*- coding: utf-8 -*-
# provably fair raffle
import argparse, os, csv, json
from hashlib import sha256
from datetime import datetime, timedelta
from time import time
from calendar import timegm
from urllib2 import urlopen

class InvalidTimeError(Exception):
  pass
  
parser = argparse.ArgumentParser(description='Provably Fair Raffle Generator', epilog='Generates a raffle ticket chain for the entrants provided. If an NIST Randomness Beacon (https://beacon.nist.gov/home) pulse is specified, the raffle drawing is conducted. Raffle tickets and (optionally) sorted results are written to CSV files.')
parser.add_argument('user_path', metavar='ENTRANTS', help='path to text file containing raffle entrants (one name per line, lines beginning with "#" are ignored)')
grp_pulse = parser.add_mutually_exclusive_group()
grp_pulse.add_argument('-i', metavar='PULSE', dest='pulse_index', help='index of NIST Randomness Beacon pulse used to select winners')
grp_pulse.add_argument('-u', metavar='PULSE', dest='pulse_unixtime', type=int, help='Unix timestamp (in ms) of NIST Randomness Beacon pulse used to select winners')
grp_pulse.add_argument('-t', metavar='PULSE', dest='pulse_time', help='timestamp of NIST Randomness Beacon pulse used to select winners. format: "year-month-day hour-minute timezone", e.g. "2018-11-28 16:03 -0600" or "2018-11-28 22:03 +0000"')
grp_pulse.add_argument('-l', action='store_const', const=True, dest='pulse_last', help='use latest available NIST Randomness Beacon pulse to select winners')

args = parser.parse_args()

headers = ['User', 'Index', 'Hash [sha256(user+i)]', 'Ticket [sha256(ticket(i-1)+hash(i))]', 'Result [sha256(ticket(i)+pulse)]']

raffle_name = os.path.splitext(args.user_path)[0]

# strip trailing/leading whitespace, ignore empty lines and comments
users = [line.strip() for line in open(args.user_path) if line.strip() and not line.startswith('#')]
print 'Parsed {} raffle entrants.'.format(len(users))

index = map(str, range(1, len(users) + 1))

hashes = [sha256(''.join(x)).hexdigest() for x in zip(users, index)]

tickets = [hashes[0]]
for i,h in enumerate(hashes):
  if i > 0: tickets.append(sha256(tickets[i - 1] + h).hexdigest())

ticket_path = '{}-ticketchain.csv'.format(raffle_name)
with open(ticket_path, 'wb') as csvfile:
  cwriter = csv.writer(csvfile)
  cwriter.writerow(headers[0:-1])
  for row in zip(users, index, hashes, tickets):
    cwriter.writerow(row)

nist_url_prefix = 'https://beacon.nist.gov/beacon/2.0/'
unixtime = None
nist_url = None

if args.pulse_time:
#   example: 2018-12-10 20:41 -0600'
  timestamp = args.pulse_time[:-6]
  tz_sign = args.pulse_time[-5]
  tz_hr = int(args.pulse_time[-4:-2])
  tz_min = int(args.pulse_time[-2:])
  offset = timedelta(hours=tz_hr, minutes=tz_min)
  dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M')
  if tz_sign == '+': dt -= offset
  elif tz_sign == '-': dt += offset
  else: raise InvalidTimeError('invalid timezone')
  unixtime = timegm(dt.timetuple()) * 1000
elif args.pulse_unixtime:
  unixtime = args.pulse_unixtime

if unixtime:
  if unixtime > int(time()) * 1000:
    raise InvalidTimeError('specified time {} is in the future'.format(unixtime))
  nist_url = '{}pulse/time/{}'.format(nist_url_prefix, unixtime)

if args.pulse_index:
  nist_url = '{}chain/1/pulse/{}'.format(nist_url_prefix, args.pulse_index)

if args.pulse_last:
  nist_url = '{}pulse/last'.format(nist_url_prefix)

if nist_url:
  print 'Fetching {} ...'.format(nist_url)
  pulse = json.loads(urlopen(nist_url).read())['pulse']
  print 'NIST Randomness Beacon output for pulse index {} ({}): {}'.format(pulse['pulseIndex'], pulse['timeStamp'], pulse['uri'])
  print '  {}'.format(pulse['outputValue'])

  results = [sha256(x).hexdigest() for x in (t + pulse['outputValue'] for t in tickets)]

  output = sorted(zip(users, index, hashes, tickets, results), key = lambda x: x[-1])

  result_path = '{}-results-{}.csv'.format(raffle_name, pulse['pulseIndex'])
  with open(result_path, 'wb') as csvfile:
    cwriter = csv.writer(csvfile)
    cwriter.writerow(headers)
    for row in output:
      cwriter.writerow(row)

  print 'Winner: {} (for details, see {})'.format(output[0][0], result_path)
