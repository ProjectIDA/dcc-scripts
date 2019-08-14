#!/usr/bin/env python

# import time
# import shutil
import os
import sys
import argparse
import datetime
import requests
from io import StringIO

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


def make_output_dir(root, sta, metric):
    root = os.path.abspath(root)
    metric_clean = metric.replace(':', '_')
    dir = os.path.join(root, sta.lower(), metric_clean)
    if not os.path.exists(dir):
        try:
            os.makedirs(dir, mode=0o0755, exist_ok=True)
        except OSError as e:
            return dir, e
        else:
            return dir, None
    else:
        return dir, None

def output_filename(params, plot_name, fileext):

    if plot_name:
        fn = f'{params["network"]}.{params["station"]}.{params["location"]}.{params["channel"]}.{plot_name}.{fileext}'
    else:
        fn = f'{params["network"]}.{params["station"]}.{params["location"]}.{params["channel"]}'
        fn = f'{fn}.{params["sdate"].strftime("%Y-%m-%d")}.{params["edate"].strftime("%Y-%m-%d")}.{fileext}'

    return fn

def date_type(date):
    try:
        return datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.datetime.strptime(date, "%Y-%j")
        except ValueError:
            raise argparse.ArgumentTypeError("".join("Invalid date: \"", date, "\""))


outputs = ["CSV", "plot"]
dqa_metrics = {
    'ALNMDeviationMetric:18-22': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'ALNMDeviationMetric:4-8': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'AvailabilityMetric': {
        "ymin": 0.0,
        "ymax": 100,
        "yunit": '%'
    },
    'CoherencePBM:18-22': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'CoherencePBM:200-500': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'CoherencePBM:4-8': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'CoherencePBM:90-110': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'DeadChannelMetric:4-8': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'DifferencePBM:18-22': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'DifferencePBM:200-500': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'DifferencePBM:4-8': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'DifferencePBM:90-110': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'EventComparePWaveOrientation': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'EventCompareStrongMotion': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'EventCompareSynthetic': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'GapCountMetric': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'InfrasoundMetric': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'MassPositionMetric': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'NLNMDeviationMetric:0.125-0.25': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'NLNMDeviationMetric:0.5-1': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'NLNMDeviationMetric:18-22': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'NLNMDeviationMetric:200-500': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'NLNMDeviationMetric:4-8': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'NLNMDeviationMetric:90-110': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'PressureMetric': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'StationDeviationMetric:18-22': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'StationDeviationMetric:200-500': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'StationDeviationMetric:4-8': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'StationDeviationMetric:90-110': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'TimingQualityMetric': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
    'VacuumMonitorMetric': {
        "ymin": 0.0,
        "ymax": 1.0,
        "yunit": ""
    },
}

today = datetime.date.today()
delta = datetime.timedelta(days=-365)
yearago = today + delta

parser = argparse.ArgumentParser(prog="gsn-metric-query")

parser.add_argument("metric", choices=dqa_metrics.keys())
parser.add_argument("output", choices=outputs)
parser.add_argument("network")
parser.add_argument("station")
parser.add_argument("channel")
parser.add_argument("location")
parser.add_argument("sdate",
                    help="start date EG: 2014-02-15 Default: 365 days ago",
                    type=date_type, default=yearago.strftime("%Y-%m-%d")
                    )
parser.add_argument("edate",
                    help="start date EG: 2014-02-15 Default: today",
                    type=date_type, default=today.strftime("%Y-%m-%d")
                    )
parser.add_argument("-o", "--outdir",
                    help="directory to which any output should be saved",
                    default="./")
parser.add_argument("-n", "--name",
                    help="Pot name. Used as last filename segment..",
                    default="")
parser.add_argument("-q", "--quiet",
                    help="Disable interactive output",
                    default=False,
                    action="store_true")
parser.add_argument("-s", "--save",
                    help="Save output to disk",
                    default=False,
                    action="store_true")
parser.add_argument("-c", "--save-csv",
                    help="Save CSV data to disk",
                    default=False,
                    action="store_true")
parser.add_argument("-d", "--debug",
                    help="enable debug mode", default=False,
                    action="store_true")

args = parser.parse_args()

metric = args.metric
output = args.output
net = args.network.upper()
sta = args.station.upper()
chan = args.channel.upper()
loc = args.location
sdate = args.sdate
edate = args.edate
name = args.name
debug = args.debug
save = args.save
quiet = args.quiet

if not save and quiet:
    #TODO: log
    sys.exit(0)

outdir, err = make_output_dir(args.outdir, sta, metric)
#TODO: check for error
#TODO: log error & exit

if err:
    #TODO add to logging
    # print(f'ERROR: Could not make directory: {outdir}')
    # print(err)
    sys.exit(1)

DQA_HOST = 'https://dqa.ucsd.edu'
DQA_URLPATH = '/dqa/cgi-bin/dqaget.py'
URL = DQA_HOST + DQA_URLPATH

# if debug and not quiet:
#     #TODO: send output to log
#     print(f'DQA: {metric} {output} {net} {sta} {chan} {loc} ({bdate} - {edate} | {name})')

params = {
    'cmd': 'data',
    'metric': metric,
    'network': net,
    'station': sta,
    'channel': chan,
    'location': loc,
    'sdate': sdate,
    'edate': edate,
    'format': "CSV",
}
resp = requests.get(
    URL,
    stream=True,
    params=params,
)

# if debug and not quiet:
    # TODO: send output to log
    # print(f"Response Status: {resp.status_code}")
    # print(f"Response Content-Type: {resp.headers['Content-Type']}")
    # print(f"Response Headers: {resp.headers}")

recs = resp.content.decode('utf-8').splitlines()
if not recs:
    #todo log error
    # print("No records returned from server")
    sys.exit(1)

if "CSV" == output.upper():
    if save:
        csv_fn = os.path.join(outdir, f'{output_filename(params, name, "csv")}')
        with open(csv_fn, 'wt') as ofl:
            for line in recs:
                ofl.write(line)

    if not quiet:
        for line in recs:
            print(line)

elif "PLOT" == output.upper():
    df = pd.read_csv(StringIO(resp.content.decode('utf-8')),
                     sep=',',
                     header=None,
                     usecols=[0, 6],
                     names=['Date', 'Net', 'Sta', 'Loc', 'Chn', 'Metric', 'Val'],
                     dtype={
                         'Date': str,
                         'Net': str,
                         'Sta': str,
                         'Locl': str,
                         'Chn': str,
                         'Metric': str,
                         'Val': np.float
                     },
                     parse_dates=[0])

    fig, axs = plt.subplots(1, 1, constrained_layout=True, figsize=(10, 5), dpi=100)

    major_locator = mdates.DayLocator(interval=15)  # to get a tick every 4 weeks
    axs.xaxis.set_major_locator(major_locator)  # #interval=28))   #to get a tick every 4 weeks
    axs.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%b-%d'))    # optional formatting

    axs.plot(df['Date'], df['Val'], 'r-', linewidth=0.5)

    title = f'DQA {metric}: {net}.{sta}.{loc}.{chan}.{sdate.strftime("%Y-%m-%d")}.{edate.strftime("%Y-%m-%d")}'
    if name:
        title = f'{title} ({name})'
    axs.set_title(title)
    axs.set_xlabel('Date')
    axs.set_ylabel(f"{metric} {dqa_metrics[metric]['yunit']}")

    # axs.grid()
    # axs.set_yticks([10,30,50,70,90], minor=True)

    # # Customize the major grid
    axs.grid(which='major', linestyle=':', linewidth='1.0', color='black')

    plt.xticks(rotation=90)
    if save:
        image_fn = f'{output_filename(params, name, "png")}'
        plt.savefig(os.path.join(outdir, image_fn))

    if not quiet:
        plt.show()
