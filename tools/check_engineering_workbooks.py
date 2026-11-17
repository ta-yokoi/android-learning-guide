#!/usr/bin/env python3
"""Run the published host models; never accesses Android, devices or peripherals."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from engineering_workbooks import android,embedded,source_for,output_for

def run(command):
    result=subprocess.run(command,capture_output=True,text=True,timeout=20)
    if result.returncode:raise RuntimeError(result.stdout+'\n'+result.stderr)
    return result.stdout.strip()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subject',choices=['all','android','embedded'],default='all')
    parser.add_argument('--sanitize',action='store_true',help='Use UndefinedBehaviorSanitizer for C examples')
    args=parser.parse_args();items=[]
    if args.subject in ('all','android'):items += [('android',k,w) for k,w in android.WORKBOOKS.items()]
    if args.subject in ('all','embedded'):
        if not shutil.which('cc'):parser.error('cc is required for development-time C11 checks')
        items += [('embedded',k,w) for k,w in embedded.WORKBOOKS.items()]
    def check(item):
        subject,key,w=item
        with tempfile.TemporaryDirectory(prefix='engineering-'+key+'-') as temp:
            folder=Path(temp)
            if subject=='android':
                src=folder/'Main.py';src.write_text(source_for(w));actual=run([sys.executable,'-I',str(src)])
            else:
                src=folder/'main.c';src.write_text(source_for(w));exe=folder/'experiment'
                flags=['-std=c11','-Wall','-Wextra','-Werror','-pedantic','-O2']
                if args.sanitize:flags+=['-fsanitize=undefined','-fno-sanitize-recover=all']
                run(['cc',*flags,str(src),'-o',str(exe)]);actual=run([str(exe)])
            if actual!=output_for(w):raise AssertionError((key,actual,output_for(w)))
        return key
    with ThreadPoolExecutor(max_workers=3) as pool:verified=list(pool.map(check,items))
    print(f'PASS {len(verified)} standalone models: assertions and published outputs match.')
    print('Host-only checks; Android APIs, real hardware and target toolchains are not verified.')

if __name__=='__main__':main()
