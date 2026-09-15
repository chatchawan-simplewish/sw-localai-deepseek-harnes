"""Sealed, inert R10 action gate; transport is injected only by a reviewed owner."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERATION = "phase13-r10-action-20260915"
ATTEMPT_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-sudoers-narrowing-phase13-r10-attempt-20260915.json"
TERMINAL_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-sudoers-narrowing-phase13-r10-20260915.json"
PARENT_PLANNER_PATH = REPOSITORY_ROOT / "scripts/Invoke-VM105ReconstructionSudoersNarrowing.py"
R9_SOURCE_PATH = REPOSITORY_ROOT / "scripts/Capture-VM105ReconstructionCaptureSudoPolicy.py"
R9_RECEIPT_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r9-20260915.json"
ACTION_SOURCE_PATH = Path(__file__).resolve()
ACTION_TEST_PATH = REPOSITORY_ROOT / "scripts/tests/test_vm105_reconstruction_sudoers_narrowing_action.py"
ACTION_CONTRACT_PATH = REPOSITORY_ROOT / "docs/contracts/vm105-reconstruction-sudoers-narrowing-r10-action-contract-20260915.md"
ACTION_REVIEW_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-reconstruction-sudoers-narrowing-r10-payload-action-review-20260915.md"
BINDING_PATHS = (PARENT_PLANNER_PATH, ACTION_CONTRACT_PATH, ACTION_SOURCE_PATH, ACTION_TEST_PATH,
                 ACTION_REVIEW_PATH, R9_SOURCE_PATH, R9_RECEIPT_PATH)
TARGET_PATH = "/etc/sudoers.d/90-cloud-init-users"
ROLLBACK_ROOT = "/var/tmp/omniroute-dsh-sudoers-r10-"
VISUDO_PATH = "/usr/sbin/visudo"
CANDIDATE_PATH_RULE = "/etc/sudoers.d/.90-cloud-init-users.r10-*"
STEPS = ("validate-current-policy", "create-root-rollback", "validate-candidate-with-visudo",
         "atomic-replace", "exact-query-attestation", "semantic-attestation-or-rollback")

# Root-only bootstrap. It accepts one sealed JSON frame, never prints policy/payload/stderr,
# and returns only its canonical terminal frame. Candidate commands come solely from that frame.
REMOTE_BOOTSTRAP = r'''import base64,hashlib,json,os,pwd,re,stat,subprocess,sys,tempfile
def cb(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
def signed(v): v=dict(v);v['receiptSha256']=hashlib.sha256(cb(v)).hexdigest();return v
def out(v): sys.stdout.buffer.write(cb(signed(v))+b'\n')
def fail(reason, rollback=False, status='BLOCKED', rollback_status=None):
 state=rollback_status or ('NOT_NEEDED' if not rollback else 'RESTORED');created=bool(rollback_path) if state!='NOT_NEEDED' else False
 out({'generation':d['generation'],'bindingSha256':d['bindingSha256'],'status':status,'reason':reason,'targetPath':d['targetPath'],'rollbackCreated':created,'rollbackPath':rollback_path if created else '','rollbackSize':rollback_size if created else 0,'rollbackSha256':rollback_sha if created else '','candidateValidationCode':validation,'captureExactAllowed':False,'reconstructionExactAllowed':False,'fullPolicyState':'UNSUPPORTED','rollbackStatus':state,'targetExecuted':False,'rawOutputStored':False,'retryAuthorized':False})
rollback_path='';rollback_size=0;rollback_sha='';validation=-1;replaced=False;was_replaced=False;restored=False
try:
 d=json.loads(sys.stdin.buffer.read(65536)); assert os.geteuid()==0
 assert set(d)=={'generation','bindingSha256','targetPath','rollbackRoot','visudoPath','capturePolicyCommand','reconstructionPolicyCommand','captureQuery','reconstructionQuery','semanticQuery'}
 target=d['targetPath']; assert target=='/etc/sudoers.d/90-cloud-init-users' and d['visudoPath']=='/usr/sbin/visudo'
 def safe(path):
  before=os.lstat(path);assert stat.S_ISREG(before.st_mode) and before.st_uid==0
  fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW);after=os.fstat(fd);assert stat.S_ISREG(after.st_mode) and (before.st_dev,before.st_ino)==(after.st_dev,after.st_ino) and after.st_uid==0
  raw=os.read(fd,1048577);os.close(fd);assert len(raw)<=1048576;return raw
 root=safe('/etc/sudoers');old=safe(target)
 def broad(raw, allow):
  text=raw.decode('ascii'); assert '\\\n' not in text and not re.search(r'(?im)^\\s*(?:[A-Za-z]+_Alias|[@#]include(?:dir)?)\\b',text)
  hits=[x for x in text.splitlines() if re.search(r'\\bdsh\\b',x)]
  return allow and len(hits)==1 and re.fullmatch(r'\\s*dsh\\s+ALL\\s*=\\s*\\(\\s*ALL\\s*\\)\\s+NOPASSWD\\s*:\\s*ALL\\s*',hits[0])
 assert not re.search(r'\\bdsh\\b',root.decode('ascii')) and broad(old,True)
 fd,rollback_path=tempfile.mkstemp(prefix=d['rollbackRoot'].rsplit('/',1)[-1],dir='/var/tmp');os.fchmod(fd,0o600);os.write(fd,old);os.close(fd);rollback_size=len(old);rollback_sha=hashlib.sha256(old).hexdigest()
 fd,candidate=tempfile.mkstemp(prefix='.90-cloud-init-users.r10-',dir=os.path.dirname(target));os.fchmod(fd,0o440);os.write(fd,('dsh ALL=(root) NOPASSWD: '+d['capturePolicyCommand']+', '+d['reconstructionPolicyCommand']+'\\n').encode('ascii'));os.close(fd)
 def restore():
  saved=safe(rollback_path);assert len(saved)==rollback_size and hashlib.sha256(saved).hexdigest()==rollback_sha
  fd,tmp=tempfile.mkstemp(prefix='.90-cloud-init-users.r10-rollback-',dir=os.path.dirname(target));os.write(fd,saved);os.fchmod(fd,0o440);os.close(fd);os.replace(tmp,target);assert safe(target)==saved
 validation=subprocess.run([d['visudoPath'],'-cf',candidate],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
 assert validation==0;os.replace(candidate,target);replaced=True;was_replaced=True
 pw=pwd.getpwnam('dsh')
 def q(command):
  def drop():
   os.setgroups([]);os.setgid(pw.pw_gid);os.setuid(pw.pw_uid)
   if os.geteuid()!=pw.pw_uid or os.getegid()!=pw.pw_gid: raise RuntimeError()
  return subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=30,preexec_fn=drop)
 cap=q(d['captureQuery']);rec=q(d['reconstructionQuery']);full=q(d['semanticQuery'])
 cap=cap.returncode==0;rec=rec.returncode==0
 def semantic(raw):
  frame=json.loads(raw);assert cb(frame)+b'\n'==raw and set(frame)=={'sudoVersion','policy'} and frame['sudoVersion']=='1.9.15p5'
  policy=frame['policy'];assert isinstance(policy,str) and policy.count('Sudoers entry: '+target+'\n')==1
  entry=target+'\n    RunAsUsers: root\n    Options: !authenticate\n    Commands:\n\\t'+d['capturePolicyCommand']+'\n\\t'+d['reconstructionPolicyCommand']+'\n'
  parts=policy.split('Sudoers entry: ')
  return len(parts)==2 and parts[1]==entry
 exact=full.returncode==0 and len(full.stdout)<=262144 and semantic(full.stdout)
 if not (cap and rec and exact):
  restore();replaced=False;restored=True;fail('POST_REPLACEMENT_ATTESTATION_REJECTED',True,'BLOCKED','RESTORED');raise SystemExit
 out({'generation':d['generation'],'bindingSha256':d['bindingSha256'],'status':'PASS','reason':'NONE','targetPath':target,'rollbackCreated':True,'rollbackPath':rollback_path,'rollbackSize':rollback_size,'rollbackSha256':rollback_sha,'candidateValidationCode':validation,'captureExactAllowed':True,'reconstructionExactAllowed':True,'fullPolicyState':'EXACT','rollbackStatus':'RETAINED','targetExecuted':False,'rawOutputStored':False,'retryAuthorized':False})
except SystemExit: pass
except Exception:
 try:
  if replaced:
   restore();replaced=False;restored=True
  fail('BOOTSTRAP_REJECTED',was_replaced,'BLOCKED','RESTORED' if restored else None)
 except Exception: fail('ROLLBACK_UNCERTAIN',was_replaced,'UNKNOWN','FAILED')
'''
REMOTE_BOOTSTRAP_SHA256 = hashlib.sha256(REMOTE_BOOTSTRAP.encode("ascii")).hexdigest()

class ActionBlocked(RuntimeError): pass
def canonical_bytes(value): return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
def canonical_line(value): return canonical_bytes(value) + b"\n"
def _sha(raw): return hashlib.sha256(raw).hexdigest()
def _publish_exclusive(path, raw):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_BINARY",0),0o600)
    try:
        view=memoryview(raw)
        while view:
            count=os.write(fd,view)
            if not count: raise OSError("short evidence write")
            view=view[count:]
        os.fsync(fd)
    finally: os.close(fd)
class EvidenceWriter:
    def __init__(self, attempt=ATTEMPT_PATH, terminal=TERMINAL_PATH): self.paths={attempt,terminal}
    def __call__(self,path,raw):
        if path not in self.paths or not isinstance(raw,bytes): raise OSError("evidence path rejected")
        _publish_exclusive(path,raw)
def _stable(path, expected, limit=1048576):
    try:
        before=os.lstat(path)
        if not stat.S_ISREG(before.st_mode): raise OSError()
        fd=os.open(path,os.O_RDONLY|getattr(os,"O_BINARY",0)|getattr(os,"O_NOFOLLOW",0)); raw=os.read(fd,limit+1);os.close(fd)
        after=os.lstat(path)
        if len(raw)>limit or _sha(raw)!=expected or (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns): raise OSError()
        return raw
    except OSError: raise ActionBlocked("SEALED_INPUT_REJECTED") from None
def _absent(path,lstat):
    try: lstat(path)
    except FileNotFoundError: return
    except OSError: raise ActionBlocked("EVIDENCE_STATE_UNKNOWN") from None
    raise ActionBlocked("EVIDENCE_ALREADY_EXISTS")
def _r9(read_file):
    raw=read_file(R9_SOURCE_PATH, _sha(R9_SOURCE_PATH.read_bytes()))
    ns={"__name__":"r9","__file__":str(R9_SOURCE_PATH)};exec(compile(raw,str(R9_SOURCE_PATH),"exec"),ns)
    parent,details=ns["_reviewed_context"](); recon=parent["_reconstruction_command_details"]()
    return parent,details,recon,ns,raw
def _validate_r9(manifest, read_file):
    expected=manifest["files"][R9_RECEIPT_PATH.relative_to(REPOSITORY_ROOT).as_posix()]
    raw=read_file(R9_RECEIPT_PATH,expected)
    try:
        value=json.loads(raw); unsigned=dict(value); receipt=unsigned.pop("receiptSha256")
        required={"generation":"phase13-r9-20260915","status":"PASS","reason":"NONE","captureExactCommandAllowed":True,"reconstructionExactCommandAllowed":True,"fullPolicyState":"BROAD","targetExecuted":False,"rawOutputStored":False,"retryAuthorized":False,"policySources":["/etc/sudoers",TARGET_PATH]}
        hashes=("loadedSourceSha256","captureTargetArgvSha256","reconstructionTargetArgvSha256","captureBootstrapSha256","reconstructionBootstrapSha256")
        if canonical_line(value)!=raw or receipt!=_sha(canonical_bytes(unsigned)) or any(value.get(k)!=v for k,v in required.items()) or any(not isinstance(value.get(k),str) or len(value[k])!=64 for k in hashes): raise ValueError()
    except (ValueError,TypeError,UnicodeDecodeError,json.JSONDecodeError): raise ActionBlocked("R9_PROVENANCE_REJECTED") from None
def _validate_review(manifest, read_file):
    path=ACTION_REVIEW_PATH.relative_to(REPOSITORY_ROOT).as_posix();raw=read_file(ACTION_REVIEW_PATH,manifest["files"][path])
    try:
        value=json.loads(raw);pins={p:sha for p,sha in manifest["files"].items() if p!=path}
        if set(value)!={"generation","status","pins"} or canonical_line(value)!=raw or value["generation"]!=GENERATION or value["status"]!="PASS" or value["pins"]!=pins: raise ValueError()
    except (ValueError,TypeError,UnicodeDecodeError,json.JSONDecodeError): raise ActionBlocked("REVIEW_PROVENANCE_REJECTED") from None
def action_manifest(files):
    parent,details,recon,_,_raw= _r9(_stable)
    return {"generation":GENERATION,"files":{p.relative_to(REPOSITORY_ROOT).as_posix():files[p] if p in files else files[p.relative_to(REPOSITORY_ROOT).as_posix()] for p in BINDING_PATHS},"freshLeaves":[p.relative_to(REPOSITORY_ROOT).as_posix() for p in (ATTEMPT_PATH,TERMINAL_PATH)],"targetPath":TARGET_PATH,"rollbackRoot":ROLLBACK_ROOT,"visudoPath":VISUDO_PATH,"candidatePathRule":CANDIDATE_PATH_RULE,"sshPrefixSha256":_sha(canonical_bytes(list(parent["SSH_COMMAND_PREFIX"]))),"capture":[details["captureTargetArgc"],details["captureTargetArgvSha256"],details["captureBootstrapSha256"]],"reconstruction":[details["reconstructionTargetArgc"],details["reconstructionTargetArgvSha256"],details["reconstructionBootstrapSha256"]],"semanticBootstrapSha256":details["semanticBootstrapSha256"],"remoteBootstrapSha256":REMOTE_BOOTSTRAP_SHA256,"steps":list(STEPS)}
def prepare_action(manifest,*,read_file=_stable,lstat=os.lstat):
    _absent(ATTEMPT_PATH,lstat);_absent(TERMINAL_PATH,lstat)
    if not isinstance(manifest,dict) or set(manifest)!={"generation","files","freshLeaves","targetPath","rollbackRoot","visudoPath","candidatePathRule","sshPrefixSha256","capture","reconstruction","semanticBootstrapSha256","remoteBootstrapSha256","steps"}: raise ActionBlocked("ACTION_MANIFEST_REJECTED")
    for path in BINDING_PATHS:
        key=path.relative_to(REPOSITORY_ROOT).as_posix(); expected=manifest["files"].get(key) if isinstance(manifest["files"],dict) else None
        if not isinstance(expected,str) or len(expected)!=64 or _sha(read_file(path,expected))!=expected: raise ActionBlocked("SEALED_INPUT_REJECTED")
    _validate_r9(manifest,read_file)
    _validate_review(manifest,read_file)
    expected=action_manifest(dict(manifest["files"]))
    if manifest!=expected: raise ActionBlocked("ACTION_MANIFEST_REJECTED")
    parent,details,recon,_ns,r9_raw=_r9(read_file)
    return {"authorized":False,"bindingSha256":_sha(canonical_bytes(manifest)),"r9Raw":r9_raw,"r9Sha256":_sha(r9_raw),"r9Context":(parent,details,recon)}
def result(binding,status,target_path=TARGET_PATH):
    asset=status=="PASS";values={"generation":GENERATION,"bindingSha256":binding,"status":status,"reason":"NONE" if status=="PASS" else "REMOTE_REJECTED","targetPath":target_path,"rollbackCreated":asset,"rollbackPath":"/var/tmp/omniroute-dsh-sudoers-r10-safe" if asset else "","rollbackSize":1 if asset else 0,"rollbackSha256":"0"*64 if asset else "","candidateValidationCode":0 if status=="PASS" else -1,"captureExactAllowed":status=="PASS","reconstructionExactAllowed":status=="PASS","fullPolicyState":"EXACT" if status=="PASS" else "UNSUPPORTED","rollbackStatus":"RETAINED" if status=="PASS" else "NOT_NEEDED","targetExecuted":False,"rawOutputStored":False,"retryAuthorized":False};values["receiptSha256"]=_sha(canonical_bytes(values));return values
def _remote_command():
    encoded=base64.b64encode(REMOTE_BOOTSTRAP.encode("ascii")).decode("ascii")
    return "/usr/bin/sudo -n /usr/bin/python3.12 -I -c 'import base64;exec(base64.b64decode(\""+encoded+"\"))'"
def _valid(raw,binding):
    try:
        value=json.loads(raw); unsigned=dict(value); receipt=unsigned.pop("receiptSha256")
        allowed={"generation","bindingSha256","status","reason","targetPath","rollbackCreated","rollbackPath","rollbackSize","rollbackSha256","candidateValidationCode","captureExactAllowed","reconstructionExactAllowed","fullPolicyState","rollbackStatus","targetExecuted","rawOutputStored","retryAuthorized","receiptSha256"}
        reasons={"NONE","BOOTSTRAP_REJECTED","POST_REPLACEMENT_ATTESTATION_REJECTED","ROLLBACK_UNCERTAIN","REMOTE_REJECTED"}
        asset_path=isinstance(value.get("rollbackPath"),str) and re.fullmatch(r"/var/tmp/omniroute-dsh-sudoers-r10-[A-Za-z0-9._-]+",value["rollbackPath"]) and isinstance(value.get("rollbackSha256"),str) and re.fullmatch(r"[0-9a-f]{64}",value["rollbackSha256"])
        typed=(value.get("generation")==GENERATION and isinstance(value.get("candidateValidationCode"),int) and not isinstance(value.get("candidateValidationCode"),bool) and isinstance(value.get("rollbackCreated"),bool) and isinstance(value.get("rollbackSize"),int) and not isinstance(value.get("rollbackSize"),bool) and value["rollbackSize"]>=0 and isinstance(value.get("captureExactAllowed"),bool) and isinstance(value.get("reconstructionExactAllowed"),bool))
        pre=(value.get("status")=="BLOCKED" and value.get("reason") in {"BOOTSTRAP_REJECTED","REMOTE_REJECTED"} and value.get("rollbackStatus")=="NOT_NEEDED" and value.get("rollbackCreated") is False and value.get("rollbackPath")=="" and value.get("rollbackSize")==0 and value.get("rollbackSha256")=="" and value.get("captureExactAllowed") is False and value.get("reconstructionExactAllowed") is False and value.get("fullPolicyState")=="UNSUPPORTED")
        restored=(value.get("status")=="BLOCKED" and value.get("reason")=="POST_REPLACEMENT_ATTESTATION_REJECTED" and value.get("rollbackStatus")=="RESTORED" and value.get("rollbackCreated") is True and asset_path and value.get("rollbackSize")>0 and value.get("candidateValidationCode")==0 and value.get("captureExactAllowed") is False and value.get("reconstructionExactAllowed") is False and value.get("fullPolicyState")=="UNSUPPORTED")
        failed=(value.get("status")=="UNKNOWN" and value.get("reason")=="ROLLBACK_UNCERTAIN" and value.get("rollbackStatus")=="FAILED" and value.get("rollbackCreated") is True and asset_path and value.get("rollbackSize")>0 and value.get("candidateValidationCode")==0 and value.get("captureExactAllowed") is False and value.get("reconstructionExactAllowed") is False and value.get("fullPolicyState")=="UNSUPPORTED")
        passed=(value.get("status")=="PASS" and value.get("reason")=="NONE" and value.get("rollbackStatus")=="RETAINED" and value.get("rollbackCreated") is True and asset_path and value.get("rollbackSize")>0 and value.get("candidateValidationCode")==0 and value.get("fullPolicyState")=="EXACT" and value.get("captureExactAllowed") and value.get("reconstructionExactAllowed"))
        combos=passed or pre or restored or failed
        if set(value)!=allowed or not typed or not combos or value.get("reason") not in reasons or canonical_line(value)!=raw or receipt!=_sha(canonical_bytes(unsigned)) or value.get("bindingSha256")!=binding or value.get("targetPath")!=TARGET_PATH or value.get("status") not in {"PASS","BLOCKED","UNKNOWN"} or any(value.get(k) is not False for k in ("targetExecuted","rawOutputStored","retryAuthorized")): raise ValueError()
        return value
    except (ValueError,TypeError,UnicodeDecodeError,json.JSONDecodeError): raise ActionBlocked("REMOTE_RECEIPT_REJECTED") from None
def _attempt(binding):
    value={"generation":GENERATION,"bindingSha256":binding,"status":"ATTEMPTED","reason":"NONE","targetExecuted":False,"rawOutputStored":False,"retryAuthorized":False}
    value["receiptSha256"]=_sha(canonical_bytes(value));return canonical_line(value)
def _local_unknown(binding, reason):
    value=result(binding,"UNKNOWN");value["reason"]=reason;unsigned=dict(value);unsigned.pop("receiptSha256");value["receiptSha256"]=_sha(canonical_bytes(unsigned));return value
def _valid_local_terminal(value,binding):
    allowed={"generation","bindingSha256","status","reason","targetPath","rollbackCreated","rollbackPath","rollbackSize","rollbackSha256","candidateValidationCode","captureExactAllowed","reconstructionExactAllowed","fullPolicyState","rollbackStatus","targetExecuted","rawOutputStored","retryAuthorized","receiptSha256"}
    unsigned=dict(value);receipt=unsigned.pop("receiptSha256",None)
    if set(value)!=allowed or value.get("status")!="UNKNOWN" or value.get("reason")!="ATTEMPT_PUBLICATION_FAILED" or value.get("bindingSha256")!=binding or receipt!=_sha(canonical_bytes(unsigned)) or any(value.get(k) is not False for k in ("targetExecuted","rawOutputStored","retryAuthorized")): raise ActionBlocked("LOCAL_TERMINAL_REJECTED")
    return canonical_line(value)
def run_action(authority_sha256,manifest,*,transport=None,read_file=_stable,lstat=os.lstat,publish=None,prepared=None):
    prepared=prepared or prepare_action(manifest,read_file=read_file,lstat=lstat); binding=prepared["bindingSha256"]
    if not isinstance(authority_sha256,str) or authority_sha256!=binding or transport is None: raise ActionBlocked("SUDOERS_NARROWING_NOT_AUTHORIZED")
    publish=publish or EvidenceWriter()
    if not callable(publish): raise ActionBlocked("SUDOERS_NARROWING_NOT_AUTHORIZED")
    try: publish(ATTEMPT_PATH,_attempt(binding))
    except Exception:
        try: publish(TERMINAL_PATH,_valid_local_terminal(_local_unknown(binding,"ATTEMPT_PUBLICATION_FAILED"),binding))
        except Exception: raise ActionBlocked("TERMINAL_PUBLICATION_FAILED") from None
        raise ActionBlocked("ATTEMPT_PUBLICATION_FAILED") from None
    try:
        if _sha(read_file(R9_SOURCE_PATH,prepared["r9Sha256"]))!=prepared["r9Sha256"]: raise ActionBlocked("R9_TOCTOU_REJECTED")
        parent,details,recon=prepared["r9Context"]; prefix=list(parent["SSH_COMMAND_PREFIX"])
        def remote_argv(command):
            if not isinstance(command,list) or command[:-1]!=prefix or not isinstance(command[-1],str): raise ActionBlocked("R9_PROVENANCE_REJECTED")
            return shlex.split(command[-1])
        payload={"generation":GENERATION,"bindingSha256":binding,"targetPath":TARGET_PATH,"rollbackRoot":ROLLBACK_ROOT,"visudoPath":VISUDO_PATH,"capturePolicyCommand":details["capturePolicyCommand"],"reconstructionPolicyCommand":details["reconstructionPolicyCommand"],"captureQuery":remote_argv(details["captureExactQueryCommand"]),"reconstructionQuery":remote_argv(details["reconstructionExactQueryCommand"]),"semanticQuery":remote_argv(details["sudoFullQueryCommand"])}; code,out,err=transport(prefix+[_remote_command()], canonical_line(payload)); value=_valid(out,binding) if code==0 and not err else result(binding,"UNKNOWN")
    except Exception: value=result(binding,"UNKNOWN")
    try: publish(TERMINAL_PATH,canonical_line(value))
    except Exception: raise ActionBlocked("TERMINAL_PUBLICATION_FAILED") from None
    return value
def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv);return 2
if __name__=="__main__": raise SystemExit(main())
