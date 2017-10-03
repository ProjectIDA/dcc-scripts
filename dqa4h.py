#!/usr/bin/python

#Author:        James Holland - jholland@usgs.gov
#Copyright:     Public Domain
#Description:   This is used to query the dqaget.py CGI interface on a DQA website.
#               It allows a user to query for specific data.

import argparse
import datetime
import time
import urllib
import urllib2

parser = argparse.ArgumentParser(prog="dqa4h.py")

def date_type(date):
    try:
        return datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.datetime.strptime(date, "%Y-%j")
        except ValueError:
            raise argparse.ArgumentTypeError("".join("Invalid date: \"", date, "\""))


formats = ["Human", "CSV"]
aliases = {"prod": "https://igskgacgvmaslwb.cr.usgs.gov/dqa", "dev": "https://igskgacgvmaslwb.cr.usgs.gov/dqadev"}

parser.add_argument("-C", "--command", help="command for type of data retrieval, EG: -C data, hash, or md5, default is \"data\"", default="data")

parser.add_argument("-w", "--website", help="use website alias or full url. Aliases: prod and dev", required=True)
parser.add_argument("-n", "--network", help="network identifier, EG: -n IU", default="%")
parser.add_argument("-s", "--station", help="station identifier, EG: -s ANMO", default="%")
parser.add_argument("-l", "--location", help="location identifier, EG: -l 00", default="%")
parser.add_argument("-c", "--channel", help="channel identifier, EG: -c BH%%", default="%")
parser.add_argument("-m", "--metric", help="metric name, EG: -m AvailabilityMetric", default="%")
parser.add_argument("-b", "--begin", help="start date EG: 2014-02-15 Default: Current date", type=date_type, default=time.strftime("%Y-%m-%d"))
parser.add_argument("-e", "--end", help="end date EG: 2014-02-15 Default: Current date", type=date_type, default=time.strftime("%Y-%m-%d"))
parser.add_argument("-f", "--format", choices=formats, help="format of output ", default="Human")

parser.add_argument("-g", "--getmetrics", help="get list of metrics stored in database", action="store_true")

args = parser.parse_args()



if(args.getmetrics == True):
    params = urllib.urlencode({"cmd": "metrics",})
else:
    params = urllib.urlencode({"cmd": args.command,
        "network":      args.network,
        "station":      args.station,
        "location":     args.location,
        "channel":      args.channel,
        "metric":       args.metric,
        "sdate":        args.begin,
        "edate":        args.end,
        "format":       args.format})

if(args.website in aliases):
    site = aliases[args.website]
else:
    site = args.website

fullsite = site + "/cgi-bin/dqaget.py?"+params
response = urllib.urlopen(fullsite)

print response.read()

