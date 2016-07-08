#!/usr/bin/python3.4

import sys
import os
import glob
import stat
import shutil
from math import floor

from obspy.core import *
import obspy.imaging
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

import process
import proc_caldata
import ida_config_io
from cross import cross_correlate


rawdir_root = '/ida/cal/raw' #os.getenv('IDA_CAL_RAWDIR_ROOT', None)
prcdir_root = '/ida/cal/rb_testdata' #os.getenv('IDA_CAL_PROCDIR_ROOT', None)
sensresp_dir = '/ida/dcc/db/sensors'
nomiresp_dir = '/ida/dcc/response/NOMINAL_RESPONSES'


if not (rawdir_root or prcdir_root):
    print('rawdir_root or prcdir_root var not set')
else:    
    # get raw directory
    if (len(sys.argv) == 2):
        absrawdir = os.path.abspath(sys.argv[1])
        # station = sys.argv[1]
        # caltype = sys.argv[2]
        # absrawdir = os.path.abspath(os.path.join(rawdir_root, station))

        print(absrawdir)
        if not os.path.exists(absrawdir):
            print('Raw directory not found:', absrawdir, '. Can not continue.')
            sys.exit(1)

        # check that css.wfdisc, cal and log output files and data subdir exist in rawdir
        rawcssfilename = os.path.join(absrawdir, 'css.wfdisc')
        rawmsfilelist = glob.glob(os.path.join(absrawdir, 'CAL-*.ms'))
        rawlogfilelist = glob.glob(os.path.join(absrawdir, 'CAL-*.log'))
        rawdatadir = os.path.join(absrawdir, 'data')

        print('raw ms mfilelist', rawmsfilelist)

        if not os.path.exists(rawcssfilename):
            print("Can't find css.wfdisc file in", absrawdir, '. Can not continue.')
            sys.exit(1)
        if len(rawmsfilelist) == 0:
            print("Can't find CAL-*.ms file in", absrawdir, '. Can not continue.')
            sys.exit(1)
        elif len(rawmsfilelist) > 1:
            print("Multiple CAL-*.ms files in", absrawdir, '. Can not continue.')
            sys.exit(1)
        if len(rawlogfilelist) == 0:
            print("Can't find CAL-*.log file in", absrawdir, '. Can not continue.')
            sys.exit(1)
        elif len(rawlogfilelist) > 1:
            print("Multiple CAL-*.log files in", absrawdir, '. Can not continue.')
            sys.exit(1)
        if not os.path.exists(rawdatadir):
            print("Can't find css data sub dir in", absrawdir, '. Can not continue.')
            sys.exit(1)

        rawmsfn = rawmsfilelist[0]
        rawlogfn = rawlogfilelist[0]

        msfile_parts = rawmsfn.split(os.sep)

        chosen = ''
        while (not (chosen in ['c', 'q', 'C', 'Q'])):
            print('')
            loccode = msfile_parts[8].split('-')[1][-2:]
            seismometer = msfile_parts[5]
            seisloc = seismometer + ' (loc=' + loccode + ')'
            print(' {:<5}{:<10} {:<14} {:<6} ({:<20})'.format(msfile_parts[4], msfile_parts[7], seisloc,  msfile_parts[6], msfile_parts[8]))
            print('')
            chosen = input('Type "c" to continue or "q" to quit:')
        if chosen in ['q', 'Q']:
            print('Processing cancelled by user.')
            sys.exit(0)

        if msfile_parts[6] == 'rbhf':
            msfile_parts[6] = 'sp'
        elif msfile_parts[6] == 'rblf':
            msfile_parts[6] = 'lp'


        # construct processing dir path. MUST NOT EXIST
        station = msfile_parts[4]
        prcdir_path = os.path.join(prcdir_root, station, 
            'dfatest_' + msfile_parts[7] + '.' + msfile_parts[6] + '.' + msfile_parts[5] + '-' + msfile_parts[8].split('-')[1][-2:])
        # print(prcdir_path)
        if True or (not (os.path.exists(prcdir_path))):
            if not (os.path.exists(prcdir_path)):
                os.mkdir(prcdir_path)
                os.chmod(prcdir_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
                os.symlink(rawdatadir, os.path.join(prcdir_path, 'data'))
                for fn in copyfilelist:
                    shutil.copy(fn, prcdir_path)

                copyfilelist = [rawcssfilename] + [rawmsfn, rawlogfn]
            # print(copyfilelist)

            #copy files and create data dir symlink

            # create tmp.wfdisc file ONLY FOR COMPARISON WITH OLD MATLAB processing pipieline
            calsig_chan = None
            with open(prcdir_path + '/tmp.wfdisc', 'wt') as tmpfl:
                with open(rawcssfilename, 'r') as cssfl:
                    for line in cssfl:
                        line = cssfl.readline()
                        parts = line.split()
                        if (parts[1].startswith('ccs')) or (parts[1].startswith('ccf')):
                            calsig_chan = parts[1][:3]
                            tmpfl.write(line)
            # create tmp.wfdisc file ONLY FOR COMPARISON WITH OLD MATLAB processing pipieline


        else:
            print("Calibration processing directory already exists:", prcdir_path, '. Can not continue.')
            sys.exit(1)

        if not calsig_chan:
            print("Calibration channel not found in file:", rawcssfilename,  '\nCan not continue.')
            sys.exit(1)


        # parse qcal log file for settling and trailing times (in secs)
        logs = glob.glob(os.path.join(prcdir_path, 'CAL-*.log'))
        if len(logs) == 0:
            print("Can't find CAL-*.log file in", prcdir_path, '. Can not continue.')
            sys.exit(1)
        elif len(logs) > 1:
            print("Multiple CAL-*.log files in", prcdir_path, '. Can not continue.')
            sys.exit(1)

        prclogfilepath = logs[0]
        with open(prclogfilepath, 'r') as logfl:
            loglines = logfl.readlines()

        settling_lines = [line.strip() for line in loglines if line.find('settling time =') > -1]
        if len(settling_lines) != 1:
            print('multiple settling lines in log')
            sys.exit(1)
        settle_val = settling_lines[0].split()[3]
        trailing_lines = [line.strip() for line in loglines if line.find('trailer time =') > -1]
        if len(trailing_lines) != 1:
            print('multiple trailing lines in log')
            sys.exit(1)
        trail_val = trailing_lines[0].split()[3]
        print('Settling value:',settle_val)
        print('Trailing value:',trail_val)
        # convert to INT, check for TypeError s


        prcmsfilepath = os.path.join(prcdir_path, rawmsfn)
        stream = read(prcmsfilepath)
        # for tr in stream:
        #     print('10 values starting at 89607 of ORIG:', tr.stats.channel)
        #     print(tr.data[800:810])


        # trim traces....
        trimmed_stream = process.ms_trim(stream, int(settle_val), int(trail_val))

        freq_nyq = trimmed_stream[0].stats.sampling_rate / 2.0

        # DEBUG
        # with open(os.path.join(prcdir_path, 'py-freqs.txt'), 'w') as ofl:
        #     freqs.tofile(ofl, sep="\n")

        taper_size = 0.1
        taper = signal.tukey(trimmed_stream[0].data.size, alpha=(taper_size * 2))

        rb_stream = trimmed_stream.select(channel=calsig_chan)
        if len(rb_stream) == 0:
            print('Calibration data not found in miniseed file. Can not continue.')
            sys.exit(1)

        trimmed_stream.remove(rb_stream[0])
        sampling_rate = rb_stream[0].stats.sampling_rate
        sampling_rate_str = str(int(sampling_rate))


        ######################
        # process rb cal data
        fn = 'O-' + sampling_rate_str

        # Apply taper and transform
        rb_tapered = np.multiply(rb_stream[0].data.astype(np.float32), taper)
        rb_len = rb_stream[0].data.size
        rb_fft = np.fft.rfft(rb_tapered)

        # DEBUG
        with open(os.path.join(prcdir_path, 'py-'+fn+'-FFT.txt'), 'w') as ofl:
            rb_fft.tofile(ofl, sep="\n")
            ofl.write('\n')


        # flip traces that need it
        waveforms = {
            'floats' : {},
            'normed' : {},
            'normed-meaned' : {},
            'response' : {}
        }
        response = {}
        for tr in trimmed_stream:
            flip = False
            fn = ''


            if tr.stats.channel[-1:] in ['2', 'E']:
                fn = 'E-' + sampling_rate_str
                # fn_legacy = 'E-'
                flip = seismometer == 'sts1'

                if flip:
                    tr.data = np.multiply(tr.data, -1)

                # DEBUG
                # save 'new' MS format data
                tr.write(os.path.join(prcdir_path, fn+'.ms'), 'MSEED')

                # save 'legacy' raw FLOATs for cross.f
                waveforms['floats'][fn] = tr.data.astype(np.float32)
                with open(os.path.join(prcdir_path, 'py-'+fn+'-out.float'), 'w+b') as ofl:
                    ofl.write(waveforms['floats'][fn])

                # DEBUG
                with open(os.path.join(prcdir_path, 'py-'+fn+'-out.float-T'), 'w') as ofl:
                    waveforms['floats'][fn].tofile(ofl, sep="\n")
                    ofl.write('\n')

                stddev = waveforms['floats'][fn].std()
                waveforms['normed'][fn] = np.divide(waveforms['floats'][fn], stddev)

                mean = waveforms['normed'][fn].mean()
                waveforms['normed-meaned'][fn] = np.subtract(waveforms['normed'][fn], mean)

                print(tr.stats.channel,stddev,mean)

                with open(os.path.join(prcdir_path, 'py-'+fn+'-out_norm_demn.txt'), 'w') as ofl:
                    waveforms['normed-meaned'][fn].tofile(ofl, sep="\n")
                    ofl.write('\n')

                
                resp_fn = proc_caldata.resp_select_file(station, tr.stats.channel, sensresp_dir, nomiresp_dir)
                response['E'] = ida_config_io.resp_read_pzfile(resp_fn, 'acc')

                # DEBUG
                print('freq_resp (PAZ):', response['E'])

                freq_resp, freqs = ida_config_io.resp_freq_resp_from_pz(tr.data.size, response['E'], tr.stats.sampling_rate)

                # DEBUG
                with open(os.path.join(prcdir_path, 'py-freqs.txt'), 'w') as ofl:
                    freqs.tofile(ofl, sep="\n")
                    ofl.write('\n')
                # [print(fr) for fr in freq_resp[:5]]

                waveforms['response'][fn] = ida_config_io.resp_normalize(freq_resp, freqs, 0.05)
                with open(os.path.join(prcdir_path, 'py-'+fn+'-resp.txt'), 'w') as ofl:
                    waveforms['response'][fn].tofile(ofl, sep="\n")
                    ofl.write('\n')

                rb_fft_w_resp = np.multiply(rb_fft, waveforms['response'][fn])
                with open(os.path.join(prcdir_path, 'py-'+fn+'-rb-with-resp.txt'), 'w') as ofl:
                    rb_fft_w_resp.tofile(ofl, sep="\n")
                    ofl.write('\n')

                rb_ifft = np.fft.irfft(rb_fft_w_resp, rb_len)
                with open(os.path.join(prcdir_path, 'py-'+fn+'-rb-ifft.txt'), 'w') as ofl:
                    rb_fft_w_resp.tofile(ofl, sep="\n")
                    ofl.write('\n')

                rb_ifft_detaper = np.divide(rb_ifft, taper)
                with open(os.path.join(prcdir_path, 'py-'+fn+'-rb-ifft-final.txt'), 'w') as ofl:
                    rb_ifft_detaper.tofile(ofl, sep="\n")
                    ofl.write('\n')

                # remove tapered protions of time series
                taper_bin_size = floor(rb_len * taper_size)
                with open(os.path.join(prcdir_path, 'py-'+fn+'-cross-input.txt'), 'w') as ofl:
                    for ndx in range(taper_bin_size-1, rb_len-taper_bin_size):
                        ofl.write('{} {}\n'.format(rb_ifft_detaper[ndx], waveforms['normed-meaned'][fn][ndx]))
                    # rb_ifft_detaper[taper_bin_size-1:rb_len-taper_bin_size].tofile(ofl, sep="\n")
                    # ofl.write('\n')

                cross_correlate(sampling_rate, rb_ifft_detaper[taper_bin_size-1:rb_len-taper_bin_size], waveforms['normed-meaned'][fn][taper_bin_size-1:rb_len-taper_bin_size])

                # lets make SNR plot
                stddev = rb_ifft_detaper[taper_bin_size-1: rb_len-taper_bin_size].std()
                print('rb_ifft STDDEV:', stddev)
                rb_ifft_detaper.__itruediv__(stddev)
                print('Start plotting....')
                plt.plot(rb_ifft_detaper[taper_bin_size-1: rb_len-taper_bin_size], 'b', linewidth=0.5)
                snrarr = np.subtract(waveforms['normed-meaned'][fn][taper_bin_size-1: rb_len-taper_bin_size], rb_ifft_detaper[taper_bin_size-1: rb_len-taper_bin_size])
                plt.plot(snrarr, 'r', linewidth=0.5)
                plt.title('SNR = {:<.1f}'.format(1.0/snrarr.std()))
                plt.show()


            elif tr.stats.channel[-1:] in ['1', 'N']:
                fn = 'N-' + sampling_rate_str
                flip = seismometer == 'sts1'
                resp_fn = proc_caldata.resp_select_file(station, tr.stats.channel, sensresp_dir, nomiresp_dir)
                response['N'] = ida_config_io.resp_read_pzfile(resp_fn)
            elif tr.stats.channel[-1:] in ['Z']:
                fn = 'Z-' + sampling_rate_str
                resp_fn = proc_caldata.resp_select_file(station, tr.stats.channel, sensresp_dir, nomiresp_dir)
                response['Z'] = ida_config_io.resp_read_pzfile(resp_fn)
            else:
                print('Unexpected CHANNEL: ', tr.stats.channel)
                print('Exiting...')
                sys.exit(1)
      


        trimmed_stream.write(os.path.join(prcdir_path, 'trimmed.ms'), 'MSEED')

        # trimmed_stream.plot(outfile=os.path.join(prcdir_path, 'trimmed.png'))


        # lets go on to respnse processing...
        # os.chdir(prcdir_path)
        # print('cur dir:', os.getcwd()) # just checking


        # calc response using input rb data
        # need to construct freq array
        




    else:
        print(len(sys.argv))