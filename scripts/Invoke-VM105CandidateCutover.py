#!/usr/bin/env python3
"""VM105 cutover preparation only. No service mutation entry is implemented."""
import argparse
import base64
import hashlib
import json
import pathlib
import re
import shlex
import socket
import subprocess
import sys
import time

SMOKE_SHA = 'bcbfe2c6ee27f7895dc8feef26ae134ef574ab7d337902c11098cbee753ddc77'
GRAPH_SHA = 'f41ff7a8ed958f0baf262f043d9cee6e19fd56a97d2513a6770cc8d505b2d73b'
BASE_SHA = '286e05565c12cdaae886a3907500932b07e239277afe60da2f251777967761d3'
DROP = (b'[Service]\nEnvironment=DSH_HOME=/home/dsh/.dsh-profiles/vm105-provider-v1\nExecStart=\n'
        b'ExecStart=/opt/node-v24.19.0-linux-x64/bin/node --no-global-search-paths '
        b'/opt/deepseek-harness/node_modules/@deepseek-ai/dsh/lib/bin.js '
        b'web --host 127.0.0.1 --port 3080 --no-open\n')


class Blocked(Exception):
    pass


def require(ok, code):
    if not ok:
        raise Blocked(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inputs(root):
    paths = {'smoke': (root / 'scripts/Test-VM105CandidateSmoke.py', SMOKE_SHA),
             'graph': (root / 'docs/evidence/vm105-post-smoke-evidence-2026-09-09.json', GRAPH_SHA),
             'base': (root / 'docs/evidence/vm105-cutover-base-contract-2026-09-09.json', BASE_SHA)}
    bundle = {}
    for key, (path, expected) in paths.items():
        with path.open('rb') as stream:
            raw = stream.read(2097153)
        require(len(raw) <= 2097152 and sha(raw) == expected, 'INPUT_PIN')
        bundle[key] = base64.b64encode(raw).decode('ascii')
    raw = json.dumps(bundle, separators=(',', ':')).encode()
    require(len(raw) <= 4194304, 'BOOTSTRAP_SIZE')
    return raw


# This read-only program is passed in -c. Only the exact bounded bundle uses stdin.
# It imports the frozen verifier under a non-main name and calls verification functions;
# no consumed CLI mode or service action is dispatched.
REMOTE = r'''
import base64,hashlib,json,os,select,signal,sys,time,types
def need(ok,code):
 if not ok: raise ValueError(code)
def digest(raw): return hashlib.sha256(raw).hexdigest()
end=time.monotonic()+30
def take(n):
 out=bytearray()
 while len(out)<n:
  remaining=end-time.monotonic()
  need(remaining>0 and select.select([0],[],[],remaining)[0],'BOOTSTRAP_TIMEOUT')
  part=os.read(0,n-len(out));need(part,'BOOTSTRAP_EOF');out.extend(part)
 return bytes(out)
result={'status':'CUTOVER_PREFLIGHT_INCOMPLETE','mutation_entry':'UNIMPLEMENTED'}
trust=None
try:
 count=int.from_bytes(take(4),'big');need(0<count<=4194304,'BOOTSTRAP_SIZE')
 raw=take(count);need(digest(raw)==BUNDLE_SHA,'BOOTSTRAP_PIN')
 bundle=json.loads(raw);need(type(bundle) is dict and set(bundle)=={'smoke','graph','base'},'BOOTSTRAP_SCHEMA')
 decoded={}
 for key,pin in PINS.items():
  data=base64.b64decode(bundle[key],validate=True)
  need(len(data)<=2097152 and digest(data)==pin,'INPUT_PIN');decoded[key]=data
 smoke=types.ModuleType('vm105_cutover_preflight_verifier')
 exec(compile(decoded['smoke'],'<frozen-verifier>','exec'),smoke.__dict__)
 graph=json.loads(decoded['graph']);base=json.loads(decoded['base'])
 need(graph['ssh_exit']==0 and graph['result']['status']=='POST_SMOKE_EVIDENCE_PASS','GRAPH_RECEIPT')
 need(base['ssh_exit']==0 and base['status']=='BASE_CONTRACT_SOURCE_AND_METADATA_PASS','BASE_RECEIPT')
 before=smoke.pilot_baseline()
 identity_keys=['InvocationID','MainPID','ExecMainStartTimestampMonotonic','NRestarts']
 initial_identity=smoke.show(smoke.PILOT,identity_keys)
 # This fresh preparation purpose is explicitly read-only. The verifier retains its
 # original source/manifest/edge/time/private-inventory/FD-restoration bounds.
 evidence=smoke.preflight_diagnostic(post_smoke=True)
 need(evidence['status']=='POST_SMOKE_EVIDENCE_PASS','FRESH_GRAPH_VERIFICATION')
 need(evidence['closure_records']==graph['result']['closure_records'],'GRAPH_DRIFT')
 need(evidence['inventory']==graph['result']['inventory'],'INVENTORY_DRIFT')
 need(evidence['root_bytes_equal'] is True and evidence['root_sha256']==graph['result']['root_sha256']
      and evidence['original_input_sha256']==graph['result']['original_input_sha256'],'CANDIDATE_PIN_DRIFT')
 trust=smoke.Trusted()
 unit=smoke.PILOT;fragment='/etc/systemd/system/'+unit
 source=trust.read(fragment)
 need(source==base['source'].encode() and digest(source)=='5019702fa48ea6067de59b5071297f80450b90bd759a813236b71db7e4bf6ec0','BASE_SOURCE_DRIFT')
 smoke.reject_envfile_directives(source,sockets=True)
 excluded={'MainPID','NRestarts','ExecMainStartTimestamp','ActiveState','InvocationID'}
 expected={k:v for k,v in base['effective_properties'].items() if k not in excluded}
 properties=smoke.show(unit,list(expected)+['EnvironmentFiles','Sockets'])
 need(all(properties[k]==v for k,v in expected.items()),'BASE_EFFECTIVE_DRIFT')
 need(properties['EnvironmentFiles'] in {'',smoke.ENV_SOURCE_PROOF}
      and properties['Sockets'] in {'',smoke.SOCKET_SOURCE_PROOF},'ACTIVATION_SOURCE')
 need(smoke.show('deepseek-harness.socket',['LoadState'])=={'LoadState':'not-found'},'SOCKET_EXISTS')
 directory=fragment+'.d'
 try:
  directory_fd=trust.open(directory)
 except FileNotFoundError:
  directory_fd=None
 if directory_fd is not None:
  need(os.fstat(directory_fd).st_mode & 0o777==0o755 and not os.listdir(directory_fd),'DROPIN_DESTINATION')
 need(not os.path.lexists(directory+'/90-vm105-provider-profile.conf'),'DROPIN_DESTINATION')
 # Effective ExecStart must be the single source-pinned base wrapper command.
 exec_value=smoke.show(unit,['ExecStart'])['ExecStart']
 prefix='{ path=/usr/local/bin/dsh ; argv[]=/usr/local/bin/dsh web --host 127.0.0.1 --port 3080 ; ignore_errors=no ; '
 need(exec_value.startswith(prefix) and exec_value.endswith(' }') and exec_value.count('{')==exec_value.count('}')==1,'BASE_EXECSTART')
 pid=before[0]['MainPID'];actual=smoke.environment(pid)
 names={'HOME','DSH_HOME','PATH','USER','LOGNAME','SHELL','LANG','INVOCATION_ID','JOURNAL_STREAM','SYSTEMD_EXEC_PID',
        'PWD','MEMORY_PRESSURE_WATCH','MEMORY_PRESSURE_WRITE'}
 need(set(actual)<=names and actual.get('HOME')=='/home/dsh' and actual.get('DSH_HOME')==smoke.OLD
      and actual.get('PATH')==before[3],'PILOT_ENVIRONMENT')
 pressure=smoke.show(unit,['ControlGroup','MemoryPressureWatch','MemoryPressureThresholdUSec'])
 need(pressure=={'ControlGroup':'/system.slice/deepseek-harness.service','MemoryPressureWatch':'auto',
                 'MemoryPressureThresholdUSec':'200ms'},'PILOT_MEMORY_PRESSURE')
 need(actual.get('PWD')==base['effective_properties']['WorkingDirectory']
      and actual.get('MEMORY_PRESSURE_WATCH')=='/sys/fs/cgroup/system.slice/deepseek-harness.service/memory.pressure'
      and type(actual.get('MEMORY_PRESSURE_WRITE')) is str,'PILOT_MEMORY_PRESSURE')
 need(base64.b64decode(actual['MEMORY_PRESSURE_WRITE'],validate=True)==b'some 200000 2000000\0','PILOT_MEMORY_PRESSURE')
 firewall=smoke.command(['/usr/sbin/ufw','status','numbered'],5)
 need(firewall.startswith('Status: active\n') and not __import__('re').search(r'\b3080\b',firewall),'FIREWALL_POLICY')
 rows=[row for row in smoke.listeners(pid) if row[0].endswith((':0C08',':0C09'))]
 need(len(rows)==1 and rows[0][0]=='0100007F:0C08' and rows[0][1] in smoke.socket_inodes(pid),'PILOT_LISTENER')
 need(smoke.pilot_baseline()==before and smoke.show(unit,identity_keys)==initial_identity,'PILOT_CHANGED')
 need(smoke.show(unit,list(expected)+['EnvironmentFiles','Sockets'])==properties,'BASE_EFFECTIVE_DRIFT')
 trust.verify()
 result.update(status='CUTOVER_PREFLIGHT_PASS',closure_count=len(evidence['closure_records']),
  inventory_count=len(evidence['inventory']),root_bytes_equal=True,fd_restoration=evidence['fd_restoration'],
  base_source_equal=True,base_effective_equal=True,pilot_identity_unchanged=True,
  dropin_destination_absent=True,socket_absent=True,ufw_active=True,
  environment_file_proof=properties['EnvironmentFiles'] or 'EMITTED_EMPTY',
  socket_source_proof=properties['Sockets'] or 'EMITTED_EMPTY')
except Exception as error:
 safe={'BOOTSTRAP_TIMEOUT','BOOTSTRAP_EOF','BOOTSTRAP_SIZE','BOOTSTRAP_PIN','BOOTSTRAP_SCHEMA','INPUT_PIN',
 'GRAPH_RECEIPT','BASE_RECEIPT','FRESH_GRAPH_VERIFICATION','GRAPH_DRIFT','INVENTORY_DRIFT','CANDIDATE_PIN_DRIFT',
 'BASE_SOURCE_DRIFT','BASE_EFFECTIVE_DRIFT','ACTIVATION_SOURCE','SOCKET_EXISTS','DROPIN_DESTINATION',
 'BASE_EXECSTART','PILOT_ENVIRONMENT','PILOT_MEMORY_PRESSURE','FIREWALL_POLICY','PILOT_LISTENER','PILOT_CHANGED'}
 code=error.args[0] if len(error.args)==1 else None
 result['error_code']=code if isinstance(code,str) and code in safe else 'VERIFICATION_INCOMPLETE'
finally:
 if trust is not None:
  try: trust.close()
  except Exception: result.update(status='CUTOVER_PREFLIGHT_INCOMPLETE',error_code='FD_CLOSE_FAILED')
print(json.dumps(result,sort_keys=True))
sys.exit(0 if result['status']=='CUTOVER_PREFLIGHT_PASS' else 1)
'''

HTTP = r'''
import urllib.request
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**k): return None
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
with opener.open('http://127.0.0.1:3080/',timeout=4) as response:
 assert response.status==200 and len(response.read(65537))<=65536
'''

TUNNEL = r'''
$ErrorActionPreference='Stop'
$t=Get-ScheduledTask -TaskName 'DeepSeek Harness VM105 SSH Tunnel'
if($t.State -ne 'Running' -or @($t.Actions).Count -ne 1){throw 'task'}
if($t.Actions[0].Execute -ine 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -or $t.Actions[0].Arguments -cne '-NoProfile -NonInteractive -WindowStyle Hidden -File C:\Users\chatc\Projects\DeepSeekHarnessRuntime\Start-VM105PilotTunnel.ps1'){throw 'action'}
$hasher=[System.Security.Cryptography.SHA256]::Create()
try{$scriptHash=[BitConverter]::ToString($hasher.ComputeHash([System.IO.File]::ReadAllBytes('C:\Users\chatc\Projects\DeepSeekHarnessRuntime\Start-VM105PilotTunnel.ps1'))).Replace('-','')}finally{$hasher.Dispose()}
if($scriptHash -cne '59E1E77B9C9C308E8DF89E2E8E2494B417FFA0BE255DF6CCF228B1EBF4FFF571'){throw 'script'}
$l=@(Get-NetTCPConnection -State Listen | Where-Object LocalPort -eq 3080)
if($l.Count -ne 1 -or $l[0].LocalAddress -ne '127.0.0.1'){throw 'listener'}
$p=Get-CimInstance Win32_Process -Filter ('ProcessId='+$l[0].OwningProcess)
$tail='-N -i C:/Users/chatc/.ssh/codex-prox01-vms-ed25519 -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o ExitOnForwardFailure=yes -o ConnectTimeout=10 -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -L 127.0.0.1:3080:127.0.0.1:3080 dsh@192.168.1.139'
if($p.ExecutablePath -ine 'C:\Windows\System32\OpenSSH\ssh.exe' -or ($p.CommandLine.TrimEnd([char]' ') -ireplace '^"?C:\\Windows\\System32\\OpenSSH\\ssh.exe"?\s+','') -cne $tail){throw 'process'}
@{pid=[int]$p.ProcessId;creation=$p.CreationDate.ToUniversalTime().ToString('o')}|ConvertTo-Json -Compress
'''


def external(previous=None):
    start = time.monotonic()
    proc = subprocess.run(['C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe', '-NoProfile', '-NonInteractive',
                           '-Command', TUNNEL], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
    require(proc.returncode == 0 and len(proc.stdout) <= 4096, 'TUNNEL_IDENTITY')
    identity = json.loads(proc.stdout)
    require(type(identity) is dict and set(identity) == {'pid', 'creation'} and type(identity['pid']) is int
            and identity['pid'] > 1 and type(identity['creation']) is str
            and re.fullmatch(r'[0-9T:Z.+-]{20,40}', identity['creation']), 'TUNNEL_IDENTITY')
    require(previous is None or identity == previous, 'TUNNEL_CHANGED')
    health = subprocess.run([sys.executable, '-I', '-c', HTTP], stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    require(health.returncode == 0, 'TUNNEL_HTTP')
    try:
        connected = socket.create_connection(('192.168.1.139', 3080), timeout=5)
    except (ConnectionRefusedError, TimeoutError, socket.timeout):
        pass
    else:
        connected.close()
        raise Blocked('LAN_ACCESSIBLE')
    require(time.monotonic() - start <= 20, 'EXTERNAL_TIMEOUT')
    return identity


def preflight():
    require(sys.platform == 'win32' and socket.gethostname().lower() == 'bell-pc2', 'LOCAL_IDENTITY')
    raw = inputs(pathlib.Path(__file__).resolve().parent.parent)
    prefix = 'BUNDLE_SHA=' + repr(sha(raw)) + '\nPINS=' + repr({'smoke': SMOKE_SHA, 'graph': GRAPH_SHA, 'base': BASE_SHA}) + '\n'
    code = 'import base64;exec(base64.b64decode(' + repr(base64.b64encode((prefix + REMOTE).encode()).decode()) + '))'
    command = '/usr/bin/sudo -n /usr/bin/python3.12 -I -c ' + shlex.quote(code)
    args = ['C:/Windows/System32/OpenSSH/ssh.exe', '-T', '-i', 'C:/Users/chatc/.ssh/codex-prox01-vms-ed25519',
            '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10',
            'dsh@192.168.1.139', command]
    require(len(subprocess.list2cmdline(args)) < 30000, 'SSH_COMMAND_SIZE')
    before = external()
    proc = subprocess.run(args, input=len(raw).to_bytes(4, 'big') + raw, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=150)
    require(len(proc.stdout) <= 16384, 'SSH_OR_REMOTE_FAILURE')
    result = json.loads(proc.stdout)
    if proc.returncode != 0:
        require(type(result) is dict and set(result) == {'status', 'mutation_entry', 'error_code'}
                and result['status'] == 'CUTOVER_PREFLIGHT_INCOMPLETE' and result['mutation_entry'] == 'UNIMPLEMENTED'
                and type(result['error_code']) is str and re.fullmatch('[A-Z_]{1,64}', result['error_code']), 'REMOTE_RECEIPT')
        result['ssh_exit'] = proc.returncode
        return result
    require(type(result) is dict and result.get('status') == 'CUTOVER_PREFLIGHT_PASS'
            and result.get('mutation_entry') == 'UNIMPLEMENTED', 'REMOTE_RECEIPT')
    external(before)
    result.update(parent_access_before_after=True, candidate_cutover='NOT EXECUTABLE',
                  proposed_dropin_sha256=sha(DROP), ssh_exit=proc.returncode)
    return result


def self_test():
    import ast
    from unittest.mock import patch
    # The shipped remote program has no path to consumed apply modes or unit controls.
    tree = ast.parse(REMOTE)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            require(node.func.attr not in {'apply', 'apply_v2', 'unlink', 'mkdir', 'rmdir', 'rename', 'write'}, 'SELF_TEST_MUTATION')
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            require(node.value not in {'start', 'stop', 'restart', 'daemon-reload'}, 'SELF_TEST_MUTATION')
    # Execute the exact shipped listener predicate against host-namespace fixtures.
    listener_lines = REMOTE[REMOTE.index(' rows=[row for row in smoke.listeners(pid)'):REMOTE.index(" need(smoke.pilot_baseline()==before")]
    from types import SimpleNamespace
    for rows, allowed in (([('00000000:0016', 'ssh'), ('0100007F:0C08', 'web')], True),
                          ([('00000000:0016', 'ssh'), ('00000000:0C08', 'web')], False),
                          ([('0100007F:0C08', 'web'), ('0100007F:0C09', 'extra')], False),
                          ([('0100007F:0C08', 'other-owner')], False)):
        fixture = {'pid': '123', 'smoke': SimpleNamespace(listeners=lambda _: rows, socket_inodes=lambda _: {'web'}),
                   'need': require}
        try:
            exec(compile('\n'.join(line[1:] for line in listener_lines.splitlines()), '<listener-fixture>', 'exec'), fixture)
        except Blocked:
            require(not allowed, 'SELF_TEST_NAMESPACE_LISTENER')
        else:
            require(allowed, 'SELF_TEST_NAMESPACE_LISTENER')
    environment_lines = REMOTE[REMOTE.index(' names={'):REMOTE.index(' firewall=')]
    import types
    env_good = {'HOME': '/home/dsh', 'DSH_HOME': '/home/dsh/.dsh', 'PATH': '/usr/bin', 'PWD': '/srv/dsh/workspaces',
                'MEMORY_PRESSURE_WATCH': '/sys/fs/cgroup/system.slice/deepseek-harness.service/memory.pressure',
                'MEMORY_PRESSURE_WRITE': base64.b64encode(b'some 200000 2000000\0').decode()}
    for change in ({}, {'PWD': '/wrong'}, {'MEMORY_PRESSURE_WATCH': '/sys/fs/cgroup/other/memory.pressure'},
                   {'MEMORY_PRESSURE_WRITE': base64.b64encode(b'some 200001 2000000\0').decode()}, {'UNKNOWN': 'x'}):
        pressure = {'ControlGroup': '/system.slice/deepseek-harness.service', 'MemoryPressureWatch': 'auto',
                    'MemoryPressureThresholdUSec': '200ms'}
        fixture = {'actual': env_good | change, 'before': (None, None, None, '/usr/bin'), 'unit': 'deepseek-harness.service',
                   'base': {'effective_properties': {'WorkingDirectory': '/srv/dsh/workspaces'}},
                   'smoke': types.SimpleNamespace(OLD='/home/dsh/.dsh', show=lambda *a: pressure), 'need': require, 'base64': base64}
        try:
            exec(compile('\n'.join(line[1:] for line in environment_lines.splitlines()), '<environment-fixture>', 'exec'), fixture)
        except Blocked:
            require(bool(change), 'SELF_TEST_MEMORY_PRESSURE')
        else:
            require(not change, 'SELF_TEST_MEMORY_PRESSURE')
    with patch.object(subprocess, 'run', side_effect=AssertionError('must not execute')):
        require(sha(DROP) == '498ffcd058b856e054e8b144292d1831b0a3f4c4004bb0ae6d94a6e21ee0ea0a', 'SELF_TEST_DROP_HASH')
    from types import SimpleNamespace
    identity = {'pid': 123, 'creation': '2026-09-08T20:00:00.0000000Z'}
    for variant in ('pass', 'changed', 'lan', 'task'):
        tunnel = SimpleNamespace(returncode=1 if variant == 'task' else 0, stdout=json.dumps(identity).encode())
        health = SimpleNamespace(returncode=0)
        connection = SimpleNamespace(close=lambda: None)
        with patch.object(subprocess, 'run', side_effect=[tunnel, health]), \
             patch.object(socket, 'create_connection', side_effect=None if variant == 'lan' else ConnectionRefusedError(),
                          return_value=connection):
            try:
                observed = external({'pid': 124, 'creation': identity['creation']} if variant == 'changed' else None)
            except Blocked as error:
                require(error.args == ({'changed': 'TUNNEL_CHANGED', 'lan': 'LAN_ACCESSIBLE', 'task': 'TUNNEL_IDENTITY'}[variant],),
                        'SELF_TEST_EXTERNAL_GUARD')
            else:
                require(variant == 'pass' and observed == identity, 'SELF_TEST_EXTERNAL_ACCEPTANCE')
    with patch.object(pathlib.Path, 'open') as opened:
        opened.return_value.__enter__.return_value.read.return_value = b'wrong pinned input'
        try:
            inputs(pathlib.Path('.'))
        except Blocked as error:
            require(error.args == ('INPUT_PIN',), 'SELF_TEST_INPUT_PIN')
        else:
            raise Blocked('SELF_TEST_INPUT_PIN_ACCEPTED')
    require("$p.CommandLine.TrimEnd([char]' ') -ireplace" in TUNNEL, 'SELF_TEST_COMMAND_TRAILING_SPACE')
    require('Get-FileHash' not in TUNNEL and '[System.Security.Cryptography.SHA256]::Create()' in TUNNEL
            and '[System.IO.File]::ReadAllBytes(' in TUNNEL and 'finally{$hasher.Dispose()}' in TUNNEL
            and 'Import-Module' not in TUNNEL and 'PSModulePath' not in TUNNEL, 'SELF_TEST_NATIVE_HASH')
    compile(REMOTE, '<remote>', 'exec')
    compile(HTTP, '<http>', 'exec')
    return {'status': 'SELF_TEST_PASS', 'mutation_entry': 'UNIMPLEMENTED'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--self-test', action='store_true')
    modes.add_argument('--preflight', action='store_true')
    args = parser.parse_args()  # --apply is deliberately unsupported.
    try:
        result = self_test() if args.self_test else preflight() if args.preflight else {
            'status': 'CONTRACT_ONLY', 'mutation_entry': 'UNIMPLEMENTED',
            'preflight_requires': '--preflight', 'proposed_dropin_sha256': sha(DROP)}
    except Exception as error:
        allowed = {'INPUT_PIN', 'BOOTSTRAP_SIZE', 'TUNNEL_IDENTITY', 'TUNNEL_CHANGED', 'TUNNEL_HTTP', 'LAN_ACCESSIBLE',
                   'EXTERNAL_TIMEOUT', 'LOCAL_IDENTITY', 'SSH_COMMAND_SIZE', 'SSH_OR_REMOTE_FAILURE', 'REMOTE_RECEIPT'}
        code = error.args[0] if len(error.args) == 1 else None
        result = {'status': 'CUTOVER_PREFLIGHT_INCOMPLETE', 'mutation_entry': 'UNIMPLEMENTED',
                  'error_code': code if isinstance(code, str) and code in allowed else 'VERIFICATION_INCOMPLETE'}
    print(json.dumps(result, sort_keys=True))
    sys.exit(0 if result['status'] in {'CONTRACT_ONLY', 'SELF_TEST_PASS', 'CUTOVER_PREFLIGHT_PASS'} else 1)
