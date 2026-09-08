param([switch]$SelfTest)

@'
import pathlib,re,json,hashlib,subprocess,datetime,sys
if sys.flags.optimize:
    print('{"status":"BLOCKED","check":"optimized-interpreter"}')
    sys.exit(1)
root=pathlib.Path('.')
pins={
    'scripts/inspect-vm105-pnpm-package.py':'fcddc77c890b289e28c609fa30b3b41f6c060a73c5c4ea3ab69b468a130df424',
    'docs/evidence/vm105-selector-store-trace.md':'a7ab0f1d371c7283a6b5e8441b05c4312b6fff86f2b7e2fddd154ced0a863ae2',
    'docs/superpowers/plans/2026-09-08-vm105-candidate-cutover.md':'a51d5342e59ee981d4fa8a90ed077dc7f73cc22c637fd4fd7f43336bd802f5f3',
}
def verify_inputs(blobs):
    if set(blobs)!=set(pins) or any(hashlib.sha256(blobs[p]).hexdigest()!=digest for p,digest in pins.items()):
        raise ValueError('input-pin-mismatch')
blobs={p:(root/p).read_bytes() for p in pins}
try:
    verify_inputs(blobs)
except ValueError:
    print('{"status":"BLOCKED","check":"input-pin-mismatch"}')
    sys.exit(1)
inspector,ledger,plan=(blobs[p].decode('utf-8') for p in pins)
def one(pattern,text):
    hits=re.findall(pattern,text)
    assert len(hits)==1,(pattern,len(hits))
    return hits[0]
packages=[{'name':'dsh','logical':one(r'Root logical package: (\S+)\.',ledger),'canonical':one(r'Root canonical package: (\S+)\.',ledger),'files':{'package.json':one(r'Root manifest SHA-256: ([a-f0-9]{64})',ledger),'config/agent-presets/standard/agent.cordis.yml':one(r'file SHA-256 `([a-f0-9]{64})`',ledger)}}]
for name,body in re.findall(r'### (dsh-[\w-]+)\s*\n(.*?)(?=\n### |\n## |\Z)',ledger,re.S):
    files=dict(re.findall(r'- ([\w./-]+) SHA-256: `([a-f0-9]{64})`',body))
    packages.append({'name':name,'logical':one(r'- Logical: `([^`]+)`',body),'canonical':one(r'- Canonical: `([^`]+)`',body),'files':files})
assert len(packages)==20
for line in ledger.splitlines():
    if re.match(r'- dsh-[\w-]+: logical ',line):
        name=one(r'^- (dsh-[\w-]+):',line)
        packages.append({'name':name,'logical':one(r'logical `([^`]+)`',line),'canonical':one(r'canonical `([^`]+)`',line),'files':{'package.json':one(r'manifest SHA-256 `([a-f0-9]{64})`',line),'lib/index.js':one(r'lib/index.js SHA-256 `([a-f0-9]{64})`',line)}})
for name in ['dsh-api-gateway','dsh-api-remotes']:
    body=one(r'(- '+name+r' logical:.*?lib/index.js SHA-256: `[^`]+`)',ledger.replace('\r','')) if False else re.search(r'- '+name+r' logical:.*?lib/index.js SHA-256: `[^`]+`',ledger,re.S).group(0)
    packages.append({'name':name,'logical':one(r'logical: `([^`]+)`',body),'canonical':one(r'- canonical: `([^`]+)`',body),'files':{'package.json':one(r'manifest SHA-256 `([a-f0-9]{64})`',body),'lib/index.js':one(r'lib/index.js SHA-256: `([a-f0-9]{64})`',body)}})
web=next(p for p in packages if p['name']=='dsh-web-app')['canonical']
for name,entry in [('dsh-host-apiproxy','lib/index.js'),('dsh-client-ui-settings-models','lib/client.js')]:
    line=one(r'(^- `'+name+r'` canonical root:.*$)',plan) if False else next(x for x in plan.splitlines() if x.startswith('- `'+name+'` canonical root:'))
    packages.append({'name':name,'logical':web.rsplit('/',1)[0]+'/'+name,'canonical':one(r'canonical root: `([^`]+)`',line),'files':{'package.json':one(r'Manifest SHA256 `([a-f0-9]{64})`',line),entry:one(r'`'+re.escape(entry)+r'` SHA256 `([a-f0-9]{64})`',line)}})
assert len(packages)==28 and sum(len(p['files']) for p in packages)==56,(len(packages),sum(len(p['files']) for p in packages))
assert all(p['files'] and len(p['files'])==2 for p in packages)
assert len({p['canonical'] for p in packages})==28
byparent={p['canonical'].rsplit('/',1)[0]:p['name'] for p in packages if p['name'] in ['dsh','dsh-base','dsh-web-app']}
for p in packages:
    p['parent']=None if p['name']=='dsh' else byparent[p['logical'].rsplit('/',1)[0]]
    assert p['canonical'].startswith('/opt/deepseek-harness/node_modules/.pnpm/')
    assert 'dsh-base/lib/index.js' not in p['canonical']+'/'+next(iter(p['files']))
remote=inspector.split('def inspect(')[0]+'\nPACKAGES='+repr(packages)+'\n'+r'''
import datetime
links=Inspection()
link_states=[]
results=[]
manifests={}
current='initial'
try:
    for package in PACKAGES:
        current=package['name']
        logical=package['logical']; canonical=package['canonical']
        parent=links.open(posixpath.dirname(logical)); name=posixpath.basename(logical)
        def state(parent=parent,name=name,logical=logical,canonical=canonical):
            st=os.stat(name,dir_fd=parent,follow_symlinks=False)
            require(stat.S_ISLNK(st.st_mode) and (st.st_uid,st.st_gid)==(0,0),'untrusted package link')
            target=os.readlink(name,dir_fd=parent)
            require(posixpath.normpath(posixpath.join(posixpath.dirname(logical),target))==canonical,'canonical mapping mismatch')
            return snapshot(st),target
        before=state(); link_states.append((state,before))
        declaration=None
        if package['parent']:
            declaration=manifests[package['parent']].get('dependencies',{}).get('@deepseek-ai/'+current)
            require(declaration=='^0.1.1-rc.2','parent dependency declaration mismatch')
        check=Inspection()
        file_results=[]
        try:
            for rel,expected in package['files'].items():
                require(rel in ('package.json','cordis.patch.yml','lib/index.js','lib/client.js','config/agent-presets/standard/agent.cordis.yml'),'file outside allowlist')
                require(not(current=='dsh-base' and rel=='lib/index.js'),'rejected source excluded')
                source,meta=check.read(canonical+'/'+rel)
                require(meta['sha256']==expected,'source pin mismatch')
                if rel=='package.json':
                    manifest=json.loads(source)
                    require(manifest.get('name')=='@deepseek-ai/'+current and manifest.get('version')=='0.1.1-rc.2','package identity mismatch')
                    manifests[current]=manifest
                file_results.append({'relative_path':rel,'sha256':expected,'digest_match':True})
            check.verify()
            require(state()==before,'logical link drift')
        finally:
            check.close()
        results.append({'name':current,'version':'0.1.1-rc.2','logical':logical,'canonical':canonical,'mapping_match':True,'declared_parent':package['parent'],'dependency_declaration':declaration,'files':file_results,'status':'PASS'})
    links.verify()
    for state,before in link_states:
        require(state()==before,'logical link drift')
    print(json.dumps({'status':'PASS','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'package_count':len(results),'file_count':sum(len(p['files']) for p in results),'packages':results}))
except Exception as error:
    print(json.dumps({'status':'BLOCKED','package':current,'check':str(error) if isinstance(error,RuntimeError) else type(error).__name__,'verified_package_count':len(results),'packages':results}))
    sys.exit(1)
finally:
    links.close()
'''
# Local-only parser and Python syntax checks precede the one remote attempt.
compile(remote,'bounded-source-revalidation','exec')
print(json.dumps({'local_allowlist_packages':len(packages),'local_allowlist_files':sum(len(p['files']) for p in packages)}),flush=True)
def checked_run(input_blobs,runner):
    verify_inputs(input_blobs)
    run=runner()
    if run.returncode!=0:
        raise ValueError('ssh-nonzero')
    try:
        result=json.loads(run.stdout)
        assert result['status']=='PASS' and result['package_count']==28 and result['file_count']==56
        assert len(result['packages'])==28
        datetime.datetime.fromisoformat(result['observed_at_utc'])
        for expected,actual in zip(packages,result['packages'],strict=True):
            assert actual['name']==expected['name'] and actual['version']=='0.1.1-rc.2'
            assert actual['logical']==expected['logical'] and actual['canonical']==expected['canonical']
            assert actual['declared_parent']==expected['parent'] and actual['mapping_match'] is True and actual['status']=='PASS'
            assert actual['dependency_declaration']==('^0.1.1-rc.2' if expected['parent'] else None)
            assert len(actual['files'])==2
            assert {f['relative_path']:f['sha256'] for f in actual['files']}==expected['files']
            assert all(f['digest_match'] is True and set(f)=={'relative_path','sha256','digest_match'} for f in actual['files'])
            assert set(actual)=={'name','version','logical','canonical','mapping_match','declared_parent','dependency_declaration','files','status'}
        assert set(result)=={'status','observed_at_utc','package_count','file_count','packages'}
    except Exception:
        raise ValueError('remote-schema-or-status-failure') from None
    result['remote_exit_code']=run.returncode
    return result

if len(sys.argv)>1 and sys.argv[1].lower()=='true':
    from types import SimpleNamespace
    cases=[('ssh-nonzero',blobs,SimpleNamespace(returncode=9,stdout='{"status":"PASS"}')),
           ('remote-schema-or-status-failure',blobs,SimpleNamespace(returncode=0,stdout='{')),
           ('remote-schema-or-status-failure',blobs,SimpleNamespace(returncode=0,stdout='{"status":"PASS"}')),
           ('input-pin-mismatch',dict(blobs,**{next(iter(pins)):b'drift'}),None)]
    for reason,inputs,reply in cases:
        def fake_run():
            assert reply is not None,'input drift reached SSH'
            return reply
        try:
            checked_run(inputs,fake_run)
        except ValueError as error:
            assert str(error)==reason
        else:
            raise AssertionError('unsafe result accepted')
    # Exercise the process exit boundary with the same checked_run and mocked SSH.
    script=(root/'scripts/Test-VM105SourcePins.ps1').read_text(encoding='utf-8')
    body=script.split("@'\n",1)[1].rsplit("\n'@ | python",1)[0]
    definitions=body.split("if len(sys.argv)>1",1)[0]
    for reason,inputs,reply in cases:
        suffix='\nfrom types import SimpleNamespace\n'
        suffix+='test_inputs='+repr(inputs)+'\n'
        suffix+='reply='+('None' if reply is None else 'SimpleNamespace(returncode='+repr(reply.returncode)+',stdout='+repr(reply.stdout)+')')+'\n'
        suffix+='try:\n    checked_run(test_inputs,lambda:reply)\nexcept Exception:\n    sys.exit(1)\nsys.exit(0)\n'
        child=subprocess.run([sys.executable,'-I','-'],input=definitions+suffix,capture_output=True,text=True,timeout=10)
        assert child.returncode==1,'rejection did not return nonzero'
    print('{"status":"SELF_TEST_PASS","rejections":4,"nonzero_exit_checks":4,"remote_attempts":0}')
    sys.exit(0)

try:
    out=root/'docs/evidence/vm105-v1-source-revalidation-2026-09-09.json'
    if out.exists() or out.is_symlink():
        raise ValueError('receipt-destination-exists')
    result=checked_run(blobs,lambda:subprocess.run(['ssh','-i','C:/Users/chatc/.ssh/codex-prox01-vms-ed25519','-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','dsh@192.168.1.139','/usr/bin/python3.12 -I -'],input=remote,text=True,capture_output=True,timeout=120))
    result.update({'scope':'VM105 explicit installed public-source pins only; no installed JavaScript execution','source_version':'0.1.1-rc.2','expected_packages':28,'expected_files':56,'method':'Single strict SSH attempt; exact preflight-pinned input bytes; in-memory pinned Inspection definitions; exact ledger allowlist; nofollow root:root trusted canonical ancestors; held descriptors and path metadata rechecked before/after; double SHA-256 reads; logical symlinks rechecked; manifest identity and parent dependency declaration verified. No directory crawl or VM write.','inspector_sha256':pins['scripts/inspect-vm105-pnpm-package.py'],'ledger_sha256':pins['docs/evidence/vm105-selector-store-trace.md'],'cutover_plan_sha256':pins['docs/superpowers/plans/2026-09-08-vm105-candidate-cutover.md'],'not_proven':['runtime readiness','cutover execution or acceptance','credential readiness or authentication provenance','usable provider route or inference acceptance'],'owner_readiness':'MISSING; source verification grants no cutover authority'})
    with out.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ['status','package_count','file_count','remote_exit_code']}))
    print(str(out.resolve()))
except Exception as error:
    print(json.dumps({'status':'BLOCKED','check':str(error) if type(error) is ValueError else type(error).__name__}))
    sys.exit(1)
'@ | python -I - $SelfTest.IsPresent.ToString()
exit $LASTEXITCODE
