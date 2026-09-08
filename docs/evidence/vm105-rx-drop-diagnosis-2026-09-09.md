# VM105 RX-drop diagnosis - 2026-09-09

Status: **WARN remains unresolved**. No acceptance or roadmap count increment.

Project: DeepSeek Harness. Verified Git remote: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git.
Worktree: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap`.

## Before and after

Historical evidence remains unchanged in `vm105-deployment-2026-08-23-redacted.md`, revalidation section dated 2026-09-08: RX drops `234093 -> 234129`, `+36/45s`, WARN.

Fresh identity at 2026-09-09 00:16:35 Asia/Bangkok (2026-09-08 17:16:35 UTC): hostname `deepseek-harness-01`, `eth0` UP at `192.168.1.139/24`, MAC `bc:24:11:5c:49:52`, kernel `6.8.0-139-generic`. Driver symlink resolved to `/sys/bus/virtio/drivers/virtio_net`.

A single four-sample window with three 15-second sleeps lasted 46 seconds including reads. Values were read sequentially, not atomically; diagnostic SSH itself contributed traffic.

| Bangkok timestamp, 2026-09-09 | UTC, 2026-09-08 | rx_packets | rx_bytes | rx_dropped | tx_packets |
| --- | --- | ---: | ---: | ---: | ---: |
| 00:17:14 | 17:17:14 | 246842 | 18743357 | 7119 | 7353 |
| 00:17:30 | 17:17:30 | 246898 | 18751439 | 7130 | 7405 |
| 00:17:45 | 17:17:45 | 247663 | 18809830 | 7141 | 7466 |
| 00:18:00 | 17:18:00 | 247718 | 18816741 | 7153 | 7501 |

Fresh delta: **+34 rx_dropped / 46s**, approximately 0.74/s. `rx_packets +876`, `rx_bytes +73384`. The lower absolute drop total than historical evidence means those totals are not a continuous counter series; reset/reboot/interface history was not investigated and is not inferred.

All four samples reported zero for `rx_errors`, `rx_missed_errors`, `rx_fifo_errors`, `rx_frame_errors`, `rx_crc_errors`, `rx_length_errors`, `rx_over_errors`, `tx_errors`, `tx_dropped`, and `multicast`.

All four `ethtool -S eth0` samples reported zero for `rx_queue_0_drops`, all RX XDP counters, TX XDP counters and `tx_queue_0_tx_timeouts`. Queue RX packet observations were 246857, 246906, 247675, 247730. Queue RX bytes were 18744197, 18751859, 18810490, 18817401. `rx_queue_0_kicks` remained 4. The later `ip -s -s link` reads agreed on drop totals 7119, 7130, 7141, 7153; link stayed UP/LOWER_UP, MTU 1500, fq_codel, qlen 1000. Its TX `transns` counter stayed 2; no new transition observed.

`/proc/net/softnet_stat` had eight CPU rows on every sample. Columns 2 (dropped), 3 (time_squeeze), 11 (flow_limit_count), 12 (backlog length), 14 and 15 (queue lengths) were zero in every row. Only CPU 1's processed counter changed: hex `0003c325`, `0003c357`, `0003c654`, `0003c68b`. Other processed counters stayed `0000056a`, `000004c8`, `000000f5`, `00000058`, `00000022`, `00000018`, `000001d9` for CPUs 0, 2-7 respectively. Column meanings are checked against [Linux v6.8 net-procfs.c](https://github.com/torvalds/linux/blob/v6.8/net/core/net-procfs.c#L146-L173); the guest Ubuntu patch set was not source-audited.

Metadata at 00:16:55 Bangkok: `ethtool -i` reported virtio_net 1.0.0, bus `0000:00:12.0`, statistics supported. `ethtool -g` reported RX ring 1024/max 1024 and TX ring 256/max 256; `ethtool -l` reported one combined channel/max one. No settings changed.

## Interpretation and limits

Direct evidence reproduces the guest RX-drop counter increase with no corresponding reported virtio queue drops, NIC receive errors/missed errors, or softnet drops/time squeeze. This narrows the symptom to the guest aggregate receive-drop accounting rather than proving ring exhaustion or softnet backlog overflow. Virtual-driver zero counters do not independently prove the physical host/network has no faults.

Linux documents `rx_dropped` as received but unprocessed packets, including resource or unsupported-protocol cases; that counter alone cannot identify the cause. See [Linux v6.8 interface statistics](https://www.kernel.org/doc/html/v6.8/networking/statistics.html). Unsupported traffic is a hypothesis only. Actual discarded protocol, kernel drop location, application impact and root cause remain **NOT PROVEN**. No loss percentage or harness-service acceptance is inferred from aggregate counters.

Next narrowed check, not executed at this collection time: obtain counts grouped only by kernel drop reason and interface for eth0, without packet bodies or addresses, to distinguish an unhandled protocol from another guest stack discard. First assess availability/privileges and obtain separate scope for tracing; this read-only sysfs/proc/net/link/ethtool lane did not authorize installing or attaching tracing. Avoid buffer/sysctl changes without that attribution. Later separately reviewed tracing is recorded in `vm105-drop-reasons-first-attempt-2026-09-09.json` and `vm105-drop-reasons-observed-2026-09-09.json`; cause and application impact remain NOT PROVEN.

Independent review: `rx_evidence_review` accepted this historical collection and the later receipts as WARN-scoped evidence on 2026-09-09 Asia/Bangkok. No NET-02 verdict upgrade or roadmap count change.

## Collection commands and execution caveat

Connection used existing key, BatchMode, IdentitiesOnly, strict known-host verification, timeout 10 seconds, user `dsh`, and only VM105. No password/credential files were read.

```powershell
ssh -i C:/Users/chatc/.ssh/codex-prox01-vms-ed25519 -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=10 dsh@192.168.1.139
```

The following secret-free shell body reproduces the collected fields on that verified guest (one bounded window; not an instruction to repeat automatically):

```sh
set -eu
[ "$(hostname)" = deepseek-harness-01 ]
[ "$(cat /sys/class/net/eth0/address)" = bc:24:11:5c:49:52 ]
ip -4 -o address show dev eth0 | grep -q '192.168.1.139/24'
date -Is
uname -r
readlink -f /sys/class/net/eth0/device/driver
ethtool -i eth0
ethtool -g eth0
ethtool -l eth0
for sample in 0 1 2 3; do
  if [ "$sample" != 0 ]; then sleep 15; fi
  printf 'SAMPLE=%s\n' "$sample"
  date -Is
  for counter in rx_packets rx_bytes rx_dropped rx_errors rx_missed_errors rx_fifo_errors rx_frame_errors rx_crc_errors rx_length_errors rx_over_errors tx_packets tx_errors tx_dropped multicast; do
    printf '%s=' "$counter"
    cat "/sys/class/net/eth0/statistics/$counter"
  done
  cat /proc/net/softnet_stat
  ethtool -S eth0
  ip -s -s link show dev eth0
done
```

Actual execution used a PowerShell here-string piped to `ssh ... sh -s`. The first attempt returned driver/ring/channel metadata then failed parsing before any sample (`expecting done`). Adding a final newline allowed all four samples and link reads to complete; an extra PowerShell carriage return afterward produced `sh: 18: \r: not found` and exit 1. Therefore the overall shell run was **not a clean exit**, but the timestamped four-sample outputs above were directly returned. No additional observation window was run. For future automation normalize all transmitted line endings, including the transport-added newline, before execution.

Only this evidence file was added. Original evidence, source code, active pilot, tunnel, service, firewall, interfaces, sysctls, VM/host settings and other VMs were untouched by this lane. No root logs, environment/profile contents, packet capture, inference/load test, install, Proxmox action, or credential inspection occurred. Application health belongs to the parent's separate verification lane.
