#!/usr/bin/env python3
"""Fixed, one-shot VM105 containment smoke launcher; no action without --apply."""
import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys


HOST = 'dsh@192.168.1.139'
IDENTITY = 'C:/Users/chatc/.ssh/codex-prox01-vms-ed25519'
SSH = 'C:/Windows/System32/OpenSSH/ssh.exe'
ROOT = '/var/tmp/omniroute-dsh-containment-smoke-20260913'
UNIT = 'omniroute-dsh-containment-smoke-20260913.service'
SERVICE = 'deepseek-harness.service'
SERVICE_FRAGMENT = '/etc/systemd/system/deepseek-harness.service'

REMOTE_SCRIPT = r'''#!/bin/bash
set -euo pipefail
ROOT=/var/tmp/omniroute-dsh-containment-smoke-20260913
UNIT=omniroute-dsh-containment-smoke-20260913.service
SERVICE=deepseek-harness.service
FRAGMENT=/etc/systemd/system/deepseek-harness.service
WORK=/srv/dsh/workspaces
OUTSIDE="$WORK/.omniroute-dsh-containment-outside-20260913"
owned=0
fail() { printf '%s\n' "$1" >&2; exit 1; }
cleanup() {
  code=$?
  if [ "$owned" = 1 ]; then
    sudo -n systemctl kill --kill-who=all --signal=SIGKILL "$UNIT" >/dev/null 2>&1 || true
    sudo -n systemctl stop "$UNIT" >/dev/null 2>&1 || true
  fi
  if [ -n "${service_pin:-}" ]; then
    cleanup_pin="$(systemctl show "$SERVICE" -p Id -p FragmentPath -p User -p Group -p ActiveState -p MainPID -p InvocationID | sha256sum | awk '{print $1}')"
    if [ "$service_pin" != "$cleanup_pin" ]; then printf '%s\n' ORIGINAL_SERVICE_DRIFT >&2; [ "$code" = 0 ] && code=1; fi
  fi
  exit "$code"
}
trap cleanup EXIT INT TERM
[ ! -e "$ROOT" ] || fail ROOT_ALREADY_EXISTS
[ ! -e "$OUTSIDE" ] && [ ! -L "$OUTSIDE" ] || fail OUTSIDE_ALREADY_EXISTS
[ "$(sudo -n systemctl show "$UNIT" -p LoadState --value 2>/dev/null || true)" = not-found ] || fail UNIT_ALREADY_EXISTS
[ "$(systemctl show "$SERVICE" -p Id --value)" = "$SERVICE" ] || fail SERVICE_ID
[ "$(systemctl show "$SERVICE" -p FragmentPath --value)" = "$FRAGMENT" ] || fail SERVICE_FRAGMENT
[ "$(systemctl show "$SERVICE" -p User --value)" = dsh ] || fail SERVICE_USER
[ "$(systemctl show "$SERVICE" -p Group --value)" = dsh ] || fail SERVICE_GROUP
[ "$(systemctl show "$SERVICE" -p ActiveState --value)" = active ] || fail SERVICE_INACTIVE
service_pin="$(systemctl show "$SERVICE" -p Id -p FragmentPath -p User -p Group -p ActiveState -p MainPID -p InvocationID | sha256sum | awk '{print $1}')"
umask 077
mkdir "$ROOT"
cat >"$ROOT/smoke.sh" <<'SMOKE'
#!/bin/bash
set -euo pipefail
ROOT=/var/tmp/omniroute-dsh-containment-smoke-20260913
OUTSIDE=/srv/dsh/workspaces/.omniroute-dsh-containment-outside-20260913
fail() { printf '%s\n' "$1" >&2; exit 1; }
touch "$ROOT/inside-write" || fail INSIDE_WRITE_ALLOWED
[ -f "$ROOT/inside-write" ] || fail INSIDE_WRITE_ALLOWED
printf 'INSIDE_WRITE_ALLOWED\n' >> "$ROOT/assertions"
if : >"$OUTSIDE"; then rm -f -- "$OUTSIDE"; fail OUTSIDE_WRITE_DENIED; fi
printf 'OUTSIDE_WRITE_DENIED\n' >> "$ROOT/assertions"
if test -r /home/dsh || test -x /home/dsh; then fail HOME_HIDDEN; fi
printf 'HOME_HIDDEN\n' >> "$ROOT/assertions"
/opt/node-v24.19.0-linux-x64/bin/node -e 'const n=require("net");let done=false;const ok=e=>{if(done)return;done=true;if(["EAFNOSUPPORT","EPERM","EACCES"].includes(e&&e.code))process.exit(0);process.exit(1)};try{const s=n.createConnection({host:"127.0.0.1",port:9});s.on("error",ok);setTimeout(()=>ok(),500)}catch(e){ok(e)}' || fail NETWORK_DENIED
printf 'NETWORK_DENIED\n' >> "$ROOT/assertions"
( sleep 120 ) &
child=$!
start="$(awk '{print $22}' "/proc/$child/stat")"
printf '%s %s\n' "$child" "$start" > "$ROOT/child.pin"
printf READY > "$ROOT/status"
while :; do sleep 1; done
SMOKE
chmod 700 "$ROOT/smoke.sh"
sudo -n systemd-run --wait --unit="$UNIT" \
  --property=User=dsh --property=Group=dsh --property=UMask=0077 \
  --property=Environment= --property=PassEnvironment= \
  --property=WorkingDirectory="$ROOT" --property=ProtectSystem=strict \
  --property=Type=exec \
  --property=ReadWritePaths="$ROOT" --property=ProtectHome=yes --property=PrivateDevices=yes \
  --property=PrivateNetwork=yes --property=RestrictAddressFamilies=AF_UNIX \
  --property=NoNewPrivileges=yes --property=CapabilityBoundingSet= \
  --property=RestrictSUIDSGID=yes --property=RestrictNamespaces=yes --property=PrivateMounts=yes \
  --property=ProtectControlGroups=yes --property=ProtectKernelTunables=yes \
  --property=LockPersonality=yes --property=SystemCallArchitectures=native \
  --property=KillMode=control-group --property=Delegate=no --property=TasksMax=16 \
  --property=RuntimeMaxSec=30s --property=TimeoutStartSec=10s --property=TimeoutStopSec=5s \
  -- /bin/bash "$ROOT/smoke.sh" >/dev/null &
runner=$!
for _ in $(seq 1 10); do [ "$(cat "$ROOT/status" 2>/dev/null || true)" = READY ] && break; sleep 1; done
[ "$(cat "$ROOT/status" 2>/dev/null || true)" = READY ] || fail READY_TIMEOUT
sudo -n systemctl show "$UNIT" -p ActiveState -p SubState -p ControlGroup -p InvocationID >"$ROOT/unit-before.txt"
unit_invocation="$(sudo -n systemctl show "$UNIT" -p InvocationID --value)"
[ -n "$unit_invocation" ] || fail UNIT_INVOCATION
owned=1
check_property() { [ "$(sudo -n systemctl show "$UNIT" -p "$1" --value)" = "$2" ] || fail "UNIT_PROPERTY_$1"; }
for pair in 'Type=exec' 'ProtectSystem=strict' 'ProtectHome=yes' 'PrivateDevices=yes' 'PrivateNetwork=yes' 'RestrictAddressFamilies=AF_UNIX' 'NoNewPrivileges=yes' 'RestrictSUIDSGID=yes' 'RestrictNamespaces=yes' 'PrivateMounts=yes' 'ProtectControlGroups=yes' 'ProtectKernelTunables=yes' 'LockPersonality=yes' 'KillMode=control-group' 'Delegate=no' 'TasksMax=16' "ReadWritePaths=$ROOT"; do
  check_property "${pair%%=*}" "${pair#*=}"
done
check_property CapabilityBoundingSet ''
cgroup="$(sudo -n systemctl show "$UNIT" -p ControlGroup --value)"
[ -n "$cgroup" ] || fail UNIT_PROPERTY_ControlGroup
read -r child child_start <"$ROOT/child.pin"
case "$child:$child_start" in *[!0-9:]*|:) fail CHILD_PIN;; esac
sudo -n systemctl stop "$UNIT"
set +e
wait "$runner"
runner_rc=$?
set -e
unit_result="$(sudo -n systemctl show "$UNIT" -p Result --value)"
exec_main_code="$(sudo -n systemctl show "$UNIT" -p ExecMainCode --value)"
exec_main_status="$(sudo -n systemctl show "$UNIT" -p ExecMainStatus --value)"
printf '%s %s %s %s\n' "$runner_rc" "$unit_result" "$exec_main_code" "$exec_main_status" >"$ROOT/stop-result"
[ "$runner_rc" = 0 ] && [ "$unit_result" = success ] || fail UNIT_STOP_RESULT
if [ -r "/proc/$child/stat" ] && [ "$(awk '{print $22}' "/proc/$child/stat")" = "$child_start" ]; then fail DESCENDANT_REAPED; fi
if [ -e "/sys/fs/cgroup$cgroup/cgroup.procs" ]; then
  [ -r "/sys/fs/cgroup$cgroup/cgroup.procs" ] || fail CGROUP_NOT_READABLE
  [ -z "$(cat "/sys/fs/cgroup$cgroup/cgroup.procs")" ] || fail CGROUP_NOT_EMPTY
fi
printf 'DESCENDANT_REAPED\n' >> "$ROOT/assertions"
owned=0
post_pin="$(systemctl show "$SERVICE" -p Id -p FragmentPath -p User -p Group -p ActiveState -p MainPID -p InvocationID | sha256sum | awk '{print $1}')"
[ "$service_pin" = "$post_pin" ] || fail ORIGINAL_SERVICE_DRIFT
[ "$(sort "$ROOT/assertions" | tr '\n' ' ')" = 'DESCENDANT_REAPED HOME_HIDDEN INSIDE_WRITE_ALLOWED NETWORK_DENIED OUTSIDE_WRITE_DENIED ' ] || fail ASSERTION_SET
printf '{"status":"CONTAINMENT_SMOKE_PASS","root":"%s","unit":"%s","service_pin_sha256":"%s"}\n' "$ROOT" "$UNIT" "$service_pin"
trap - EXIT INT TERM
'''


def contract():
    return {'status': 'CONTRACT_ONLY', 'root': ROOT, 'unit': UNIT,
            'remote_sha256': hashlib.sha256(REMOTE_SCRIPT.encode()).hexdigest()}


def ssh_argv():
    return [SSH, '-T', '-i', IDENTITY, '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes',
            '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10', HOST,
            '/bin/bash -o pipefail -c "/usr/bin/base64 -d | /bin/bash"']


def valid_receipt(raw):
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return False
    return (isinstance(value, dict) and set(value) == {'status', 'root', 'unit', 'service_pin_sha256'}
            and value['status'] == 'CONTAINMENT_SMOKE_PASS' and value['root'] == ROOT and value['unit'] == UNIT
            and isinstance(value['service_pin_sha256'], str)
            and re.fullmatch(r'[0-9a-f]{64}', value['service_pin_sha256']) is not None)


def run():
    raw = base64.b64encode(REMOTE_SCRIPT.encode())
    return subprocess.run(ssh_argv(), input=raw, capture_output=True, timeout=70)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    if not args.apply:
        print(json.dumps(contract(), sort_keys=True))
        return 0
    result = run()
    if result.returncode or len(result.stdout) > 1024 or result.stderr or not valid_receipt(result.stdout):
        return 1
    sys.stdout.buffer.write(result.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
