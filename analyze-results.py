#!/usr/bin/env python
#----------------------------------------------------------------------------
# shabench - Copyright (c) 2025, Thierry Lelegard
# BSD 2-Clause License, see LICENSE file.
# Analyze results files and produce an analysis in RESULTS.txt.
# With option --pprint, print the data structure instead of creating the file.
#----------------------------------------------------------------------------

import os, sys, pprint, analyze

# List of CPU cores and corresponding result files.
results = [
    {'cpu': 'i7-8565U',    'frequency': 4.20, 'file': 'intel-i7-8565U-linux-vm.txt'},
    {'cpu': 'i7-13700H',   'frequency': 5.00, 'file': 'intel-i7-13700H-linux-vm.txt'},
    {'cpu': 'Xeon G6348',  'frequency': 2.60, 'file': 'intel-xeon-gold-6348-linux.txt'},
    {'cpu': 'Xeon M9460',  'frequency': 3.50, 'file': 'intel-xeon-max-9460-linux.txt'},
    {'cpu': 'EPYC 7543P',  'frequency': 3.70, 'file': 'amd-epyc-7543p-linux.txt'},
    {'cpu': 'EPYC 9534',   'frequency': 3.70, 'file': 'amd-epyc-9534-linux.txt'},
    {'cpu': 'Cortex A53',  'frequency': 1.20, 'file': 'arm-rpi3-cortex-a53-linux.txt'},
    {'cpu': 'Cortex A72',  'frequency': 1.80, 'file': 'arm-rpi4-cortex-a72-linux.txt'},
    {'cpu': 'Neoverse N1', 'frequency': 3.00, 'file': 'arm-ampere-neoverse-n1-linux.txt'},
    {'cpu': 'Neoverse V1', 'frequency': 2.60, 'file': 'arm-graviton3-neoverse-v1-linux-vm.txt'},
    {'cpu': 'Neoverse V2', 'frequency': 3.30, 'file': 'arm-grace-neoverse-v2-linux.txt'},
    {'cpu': 'Apple M1',    'frequency': 3.20, 'file': 'arm-apple-m1-macos.txt'},
    {'cpu': 'Apple M3',    'frequency': 4.00, 'file': 'arm-apple-m3-macos.txt'},
    {'cpu': 'Apple M4',    'frequency': 4.40, 'file': 'arm-apple-m4-macos.txt'}
]

# Column headers.
headers = {'cpu': 'CPU core', 'freq': 'Frequency', 'openssl': 'OpenSSL'}

# Main code.
if __name__ == '__main__':
    dir = os.path.dirname(os.path.abspath(__file__))
    algos = analyze.load_results(results, dir + '/results')
    if '--pprint' in sys.argv:
        pprint.pprint(results, width=132)
    else:
        with open(dir + '/RESULTS.txt', 'w') as output:
            analyze.display_tables(results, algos, headers, output)
