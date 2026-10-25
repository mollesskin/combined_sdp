#!/usr/bin/env python3
"""Download official archived native compilers and verify upstream SHA256."""
import datetime,hashlib,json,pathlib,platform,subprocess,urllib.request,ssl
import certifi
TLS=ssl.create_default_context(cafile=certifi.where())
BASE=pathlib.Path(__file__).resolve().parent

def main():
    folder=BASE/'toolchain'; folder.mkdir(exist_ok=True)
    log=BASE/'setup'/'compilers.jsonl'
    arch='macosx-amd64' if platform.system()=='Darwin' else 'linux-amd64'
    root=f'https://raw.githubusercontent.com/ethereum/solc-bin/gh-pages/{arch}/'
    def record(data):
        with log.open('a') as f: f.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**data})+'\n')
    try:
        raw=urllib.request.urlopen(root+'list.json',timeout=30,context=TLS).read()
        (BASE/'setup'/'solc-list.json').write_bytes(raw); listing=json.loads(raw)
    except Exception as e:
        record(dict(status='index_download_error',url=root+'list.json',error=str(e))); return
    for version in sorted({r['solc'] for r in json.loads((BASE/'manifest.json').read_text())['contracts']}):
        try:
            name=listing['releases'][version]; meta=next(x for x in listing['builds'] if x['path']==name)
            data=urllib.request.urlopen(root+name,timeout=60,context=TLS).read(); actual=hashlib.sha256(data).hexdigest()
            if actual!=meta['sha256'].removeprefix('0x'): raise RuntimeError('SHA256 mismatch')
            p=folder/('solc-'+version); p.write_bytes(data); p.chmod(0o755)
            registry=folder/'solcx'; registry.mkdir(exist_ok=True)
            link=registry/('solc-v'+version)
            if link.is_symlink(): link.unlink()
            if link.exists(): raise RuntimeError('Refusing to replace compiler registration')
            link.symlink_to(pathlib.Path('..')/p.name)
            proc=subprocess.run([str(p),'--version'],capture_output=True,text=True,timeout=30)
            record(dict(status='downloaded',version=version,url=root+name,sha256=actual,exit_code=proc.returncode,stdout=proc.stdout,stderr=proc.stderr))
        except Exception as e: record(dict(status='compiler_setup_error',version=version,error=str(e)))
if __name__=='__main__': main()
