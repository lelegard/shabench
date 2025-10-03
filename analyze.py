#!/usr/bin/env python
#----------------------------------------------------------------------------
# shabench - Copyright (c) 2025, Thierry Lelegard
# BSD 2-Clause License, see LICENSE file.
# A Python module to analyze results files and produce a table.
#----------------------------------------------------------------------------

import re, os, sys

GIGA = 1000000000.0
SEPARATOR = '   '

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
