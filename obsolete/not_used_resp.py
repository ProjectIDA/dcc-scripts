#####################################################################
# Script to run manually that moves any files in
# $IDA_DATASCOPE_DBDIR/sensors and moves any that are NOT referenced
# in the datascope DB to a subdir NOT_USED
#####################################################################
import datetime
import glob
import os.path
import shutil
from pathlib import Path
import pandas as pd

def parse_dt(dt_str):
    return datetime.datetime.fromtimestamp(float(dt_str))
    # return pd.to_datetime(float(dt_str), unit='s')


stage_cols = [

    ('sta',       0,   6),
    ('chn',       7,   8),
    ('loc',      16,   2),
    ('begt',     19,  17),
    ('endt',     37,  17),
    ('stageid',  55,   8),
    ('ssident',  64,  16),
    ('gnom',     81,  11),
    ('gcalib',   93,  10),
    ('iunits',  104,  16),
    ('ounits',  121,  16),
    ('izero',   138,  8),
    ('decifac', 147,  8),
    ('srate',   156,  11),
    ('leadfac', 168,  11),
    ('dir',     180,  64),
    ('dfile',   245,  32),
    ('lddate',  278,  17),
]



chan_cols = [
    # name     sta wid
    ('sta',      0,  6),
    ('chn',      7,  8),
    ('loc',     16,  2),
    ('begt',    19, 17),
    ('endt',    37, 17),
    ('edepth',  55,  9),
    ('hang',    65,  6),
    ('vang',    72,  6),
    ('flag',    79,  2),
    ('instype', 82,  6),
    ('nomfreq', 89, 16),
]

date_cnvtrs = {
    'begt': parse_dt,
    'endt': parse_dt
}

col_delim = ' '

header_row = None

chan_colspecs = [(chan_col[1], chan_col[1] + chan_col[2]) for chan_col in chan_cols]
chan_names  = [chan_col[0] for chan_col in chan_cols]

chan_data = pd.read_fwf('IDA.chan', names=chan_names, colspecs=chan_colspecs, header=None,
    converters=date_cnvtrs,
    )
# print('chn: ', chan_data['chn'][0],type(chan_data['chn'][0]))
# print('begt: ', chan_data['begt'][0],type(chan_data['begt'][0]))
# print('endt: ', chan_data['endt'][0],type(chan_data['endt'][0]))

stage_colspecs = [(stage_col[1], stage_col[1] + stage_col[2]) for stage_col in stage_cols]
stage_names  = [stage_col[0] for stage_col in stage_cols]
stage_data = pd.read_fwf('IDA.stage', names=stage_names, colspecs=stage_colspecs, header=None,
    converters=date_cnvtrs
    )
# print('begt: ', stage_data['begt'][0],type(stage_data['begt'][0]))
# print('endt: ', stage_data['endt'][0],type(stage_data['endt'][0]))

# get list of sensor files
sens_files = [fp for fp in sorted(glob.glob('/ida/dcc/db/sensors/*')) if os.path.isfile(fp)]
print('sens files glob count:', len(sens_files))

sens_resp_used_in_db = stage_data.dfile.unique()

moved = []

for senfp in sens_files:
    senname = Path(senfp).name
    if senname not in sens_resp_used_in_db:
        moved.append(senname)
        print('Moving ==> ', senname)
        shutil.move(senfp, '/ida/dcc/db/sensors/NOT_USED')


with open('not_used_sensorfiles.txt', 'w') as file:
    if len(moved) > 0:
        file.write('\n'.join(moved))
    else:
        file.write('No sensor files moved.\n')
