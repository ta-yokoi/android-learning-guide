#!/usr/bin/env python3
"""Compile/run the guide and workbook examples; optional ECJ for a JRE-only workspace."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import subprocess
import tempfile
from generate_gof_slides import sources
from gof_book_labs import LABS,java_for

def run(command):
    result=subprocess.run(command,capture_output=True,text=True,timeout=45)
    if result.returncode:
        raise RuntimeError(f'{command[0]} exited {result.returncode}\n{result.stdout}\n{result.stderr}')
    return result.stdout.strip()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ecj',type=Path,help='Existing Eclipse compiler jar; otherwise use javac --release 17')
    parser.add_argument('--patterns',nargs='+',help='Optional pattern IDs to verify')
    args=parser.parse_args()
    if not shutil.which('java'):parser.error('java is required for development-time checks')
    if args.ecj:
        if not args.ecj.is_file():parser.error('ECJ jar does not exist')
        compiler=['java','-jar',str(args.ecj.resolve()),'-17','-proc:none','-warn:none']
    else:
        if not shutil.which('javac'):parser.error('Install a JDK or provide an existing compiler jar with --ecj')
        compiler=['javac','--release','17','-proc:none']
    all_sources=sources()
    if args.patterns:
        unknown=set(args.patterns)-all_sources.keys()
        if unknown:parser.error('Unknown patterns: '+', '.join(sorted(unknown)))
        all_sources={key:value for key,value in all_sources.items() if key in args.patterns}

    def verify(item):
        key,source=item;lab=LABS[key]
        programs=[('before',source['before'],None),('after',source['code'],source['output']),('lab',java_for(source['code'],lab),lab['output'])]
        for kind,code,expected in programs:
            with tempfile.TemporaryDirectory(prefix='gof-'+key+'-'+kind+'-') as folder:
                path=Path(folder)/'Main.java';path.write_text(code,encoding='utf-8')
                try:
                    run(compiler+['-encoding','UTF-8',str(path)])
                    actual=run(['java','-cp',folder,'Main'])
                    if expected is not None and actual!=expected.strip():
                        raise AssertionError(f'Output mismatch\nEXPECTED:\n{expected}\nACTUAL:\n{actual}')
                except Exception as error:
                    raise RuntimeError(key+' / '+kind+': '+str(error)) from error
        return key

    with ThreadPoolExecutor(max_workers=3) as pool:
        verified=list(pool.map(verify,all_sources.items()))
    print(f'PASS {len(verified)*3} Java programs; {len(verified)*2} published outputs match.')
    print('Source target: Java 17. Runtime is the java command in this environment.')

if __name__=='__main__':main()
