#!/usr/bin/env python
#----------------------------------------------------------------------------
# shabench - Copyright (c) 2025, Thierry Lelegard
# BSD 2-Clause License, see LICENSE file.
# A Python module to analyze results files and produce a table.
# The main analyzes results files and produce an analysis in RESULTS.txt.
# With option --pprint, print the data structure instead of creating the file.
#----------------------------------------------------------------------------

import re, os, sys, pprint

#
# List of CPU cores and corresponding result files.
#
RESULTS = [
    {'cpu': 'i7-8565U',     'core': 'Whiskey Lake', 'frequency': 4.20, 'file': 'intel-i7-8565U-linux-vm.txt'},
    {'cpu': 'i7-13700H',    'core': 'Raptor Lake',  'frequency': 5.00, 'file': 'intel-i7-13700H-linux-vm.txt'},
    {'cpu': 'Xeon G6242R',  'core': 'Cascade Lake', 'frequency': 3.10, 'file': 'intel-xeon-gold-6242r-linux.txt'},
    {'cpu': 'Xeon G6348',   'core': 'Ice Lake',     'frequency': 2.60, 'file': 'intel-xeon-gold-6348-linux.txt'},
    {'cpu': 'Xeon M9460',   'core': 'Sapphire Rpd', 'frequency': 3.50, 'file': 'intel-xeon-max-9460-linux.txt'},
    {'cpu': 'EPYC 7543P',   'core': 'Milan',        'frequency': 3.70, 'file': 'amd-epyc-7543p-linux.txt'},
    {'cpu': 'EPYC 9534',    'core': 'Genoa',        'frequency': 3.70, 'file': 'amd-epyc-9534-linux.txt'},
    {'cpu': 'Rasp. Pi 3',   'core': 'Cortex A53',   'frequency': 1.20, 'file': 'arm-rpi3-cortex-a53-linux.txt'},
    {'cpu': 'Rasp. Pi 4',   'core': 'Cortex A72',   'frequency': 1.80, 'file': 'arm-rpi4-cortex-a72-linux.txt'},
    {'cpu': 'Ampere Altra', 'core': 'Neoverse N1',  'frequency': 3.00, 'file': 'arm-ampere-neoverse-n1-30-linux.txt'},
    {'cpu': 'Ampere Altra', 'core': 'Neoverse N1',  'frequency': 3.30, 'file': 'arm-ampere-neoverse-n1-33-linux.txt'},
    {'cpu': 'Graviton 3',   'core': 'Neoverse V1',  'frequency': 2.60, 'file': 'arm-graviton3-neoverse-v1-linux-vm.txt'},
    {'cpu': 'Nvidia Grace', 'core': 'Neoverse V2',  'frequency': 3.30, 'file': 'arm-grace-neoverse-v2-linux.txt'},
    {'cpu': 'Apple M1',     'core': 'M1',           'frequency': 3.20, 'file': 'arm-apple-m1-macos.txt'},
    {'cpu': 'Apple M2',     'core': 'M2',           'frequency': 3.49, 'file': 'arm-apple-m2-macos.txt'},
    {'cpu': 'Apple M3',     'core': 'M3',           'frequency': 4.05, 'file': 'arm-apple-m3-macos.txt'},
    {'cpu': 'Apple M4',     'core': 'M4',           'frequency': 4.40, 'file': 'arm-apple-m4-macos.txt'}
]

#
# Column headers.
#
HEADERS = {'cpu': 'CPU', 'core': 'CPU core', 'freq': 'Frequency', 'openssl': 'OpenSSL'}
SEPARATOR = '   '
GIGA = 1000000000.0

##
# Load and analyze a "results" structure.
#
# A "results" structure is a list of dictionaries. Each dictionary describes one test.
# In a test dictionary, the two mandatory fields are 'frequency' (in GHz) and 'file'
# (containing the output of shabench).
#
# @param [in,out] results List of results. Each result is updated with data from the file.
# @param [in] input_dir Base directory for input file names. All file names are updated.
# @return A list of algorithm names.
#
def load_results(results, input_dir='.'):
    algos = []
    count = 0

    # Load all files.
    while count < len(results):
        res = results[count]
        if not os.path.isabs(res['file']):
            res['file'] = os.path.abspath(input_dir + os.path.sep + res['file'])
        if not os.path.exists(res['file']):
            del results[count]
            continue
        res['freq'] = '%.2f GHz' % (res['frequency'])
        if not 'openssl' in res:
            res['openssl'] = ''
        res['data'] = {}
        res['index'] = count
        count += 1
        with open(res['file'], 'r') as input:
            algo = None
            for line in input:
                line = [field.strip() for field in line.split(':')]
                if len(line) >= 2:
                    if line[0] == 'algo':
                        algo = line[1]
                        if algo != 'SHA1' and algo.startswith('SHA') and not algo.startswith('SHA3-'):
                            algo = 'SHA2-' + algo[3:]
                        if algo not in algos:
                            algos += [algo]
                        res['data'][algo] = {
                            'bitrate':  {'value': 0,   'string': '', 'rank': 0},
                            'bitcycle': {'value': 0.0, 'string': '', 'rank': 0},
                        }
                    elif line[0] == 'openssl' and not res['openssl']:
                        match = re.search(r'([0-9\.]+[a-zA-Z]*)', line[1])
                        if match is not None:
                            res['openssl'] = match.group(1)
                    elif line[0] == 'hash-bitrate' and algo is not None:
                        data = res['data'][algo]
                        bitcycle = float(line[1]) / (res['frequency'] * GIGA)
                        data['bitrate']['value'] = int(line[1])
                        data['bitrate']['string'] = '%.3f' % (float(line[1]) / GIGA) 
                        data['bitcycle']['value'] = bitcycle
                        if bitcycle >= 10.0:
                            data['bitcycle']['string'] = '%.1f' % bitcycle
                        elif bitcycle >= 1.0:
                            data['bitcycle']['string'] = '%.2f' % bitcycle
                        else:
                            data['bitcycle']['string'] = '%.3f' % bitcycle

    # Build rankings.
    for algo in algos:
        for value in ['bitrate', 'bitcycle']:
            dlist = [(res['index'], res['data'][algo][value]['value']) for res in results]
            dlist.sort(key=lambda x: x[1], reverse=True)
            for rank in range(len(dlist)):
                res = next(r for r in results if r['index'] == dlist[rank][0])
                res['data'][algo][value]['rank'] = rank + 1
    for res in results:
        res['width'] = 0
        res['ranks'] = {'bitrate': {'min': 1000, 'max': 0}, 'bitcycle': {'min': 1000, 'max': 0}}
        for algo in algos:
            for value in ['bitrate', 'bitcycle']:
                data = res['data'][algo][value]
                res['ranks'][value]['min'] = min(res['ranks'][value]['min'], data['rank'])
                res['ranks'][value]['max'] = max(res['ranks'][value]['max'], data['rank'])
        for algo in algos:
            for value in ['bitrate', 'bitcycle']:
                data = res['data'][algo][value]
                space = ' '
                if res['ranks'][value]['min'] < 10 and res['ranks'][value]['max'] >= 10 and data['rank'] < 10:
                    space = '  '
                data['string'] += '%s(%d)' % (space, data['rank'])
                res['width'] = max(res['width'], len(data['string']))

    # End of analysis, return the list of algos.
    return algos

##
# Generate a text table of results.
#
# @param [in] results Table results.
# @param [in] algos List of algorithms to display.
# @param [in] headers List of headers, by key from result.
# @param [in] value_name Key of result to display, typically 'bitrate' or 'bitcycle'.
# @param [in] file Output file handler.
# @param [in] colsep Separator between columns.
#
def display_one_table(results, algos, headers, value_name, file, colsep=SEPARATOR):
    # Max width of first column.
    w0 = max(max([len(s) for s in headers.values()]), max([len(s) for s in algos]))
    # Max line of each column, depending on headers.
    for res in results:
        res['_width'] = max(res['width'], max([len(res[k]) for k in headers.keys()]))
    # Output headers lines.
    for k in headers.keys():
        line = headers[k].ljust(w0)
        for res in results:
            line += colsep + res[k].rjust(res['_width'])
        print(line.rstrip(), file=file)
    line = w0 * '-'
    for res in results:
        line += colsep + (res['_width'] * '-')
    print(line.rstrip(), file=file)
    # Output one line per operation.
    for algo in algos:
            line = algo.ljust(w0)
            for res in results:
                if algo in res['data']:
                    line += colsep + res['data'][algo][value_name]['string'].rjust(res['_width'])
                else:
                    line += colsep + res['_width'] * ' '
            print(line.rstrip(), file=file)

##
# Generate the final text file.
#
# @param [in] results Table results.
# @param [in] algos List of algorithms to display.
# @param [in] headers List of headers, by key from result.
# @param [in] file Output file handler.
# @param [in] colsep Separator between columns.
#
def display_tables(results, algos, headers, file, colsep=SEPARATOR):
    print('HASH BITRATE (Gb/s)', file=file)
    print('', file=file)
    display_one_table(results, algos, headers, 'bitrate', file, colsep)
    print('', file=file)
    print('HASHED BITS PER PROCESSOR CYCLE', file=file)
    print('', file=file)
    display_one_table(results, algos, headers, 'bitcycle', file, colsep)

#
# Main code.
#
if __name__ == '__main__':
    dir = os.path.dirname(os.path.abspath(__file__))
    algos = load_results(RESULTS, dir + '/results')
    if '--pprint' in sys.argv:
        pprint.pprint(RESULTS, width=132)
    else:
        with open(dir + '/RESULTS.txt', 'w') as output:
            display_tables(RESULTS, algos, HEADERS, output)
