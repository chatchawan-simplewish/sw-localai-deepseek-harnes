#requires -Version 7.5
[CmdletBinding()]
param(
    [ValidateSet('Preflight','Postflight','Rollback')][string]$Stage = 'Preflight',
    [string]$RuleId,
    [string]$PacketPath = (Join-Path $PSScriptRoot '../docs/evidence/phase-03-firewall-packet.json'),
    [string]$ResultsPath = (Join-Path $PSScriptRoot '../docs/evidence/phase-03-firewall-results.json'),
    [switch]$SelfTest
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$routeNames = [ordered]@{
    'OR-AUTO' = 'OpenRouter Auto'; 'OR-PARETO-CODE' = 'OpenRouter Pareto Code'; 'VM1201-QWEN' = 'VM1201 Qwen'
    'BELL-WORKER' = 'Bell-PC2 local worker'; 'TYPHOON-TEXT' = 'Typhoon Thai text'; 'TYPHOON-OCR' = 'Typhoon OCR'
    'CODEX-LUNA' = 'Codex Luna'; 'CODEX-TERRA' = 'Codex Terra'; 'CODEX-SOL' = 'Codex Sol'
}

function Require([bool]$Condition, [string]$Category) { if (-not $Condition) { throw $Category } }
function Text-Required($Value) {
    Require ($Value -is [string] -and -not [string]::IsNullOrWhiteSpace($Value) -and $Value -notmatch '^(?i:unknown|unresolved|tbd|todo|not proven|n/?a|null|blocked)$') 'missing-or-unresolved-field'
}
function Timestamp($Value) {
    Text-Required $Value
    $parsed = [DateTimeOffset]::MinValue
    Require ($Value -match '^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$' -and [DateTimeOffset]::TryParse($Value, [ref]$parsed)) 'invalid-timestamp'
    Require ($parsed -le [DateTimeOffset]::UtcNow.AddMinutes(5)) 'future-timestamp'
}
function Evidence($Value) { Require ($Value -is [System.Collections.IDictionary]) 'missing-evidence'; Timestamp $Value.capturedAt; Text-Required $Value.provenance; Text-Required $Value.observation }
function Address($Value) {
    Text-Required $Value
    $ip = $null
    Require ($Value -notmatch '[/\s]' -and [Net.IPAddress]::TryParse($Value, [ref]$ip)) 'invalid-address'
    Require ($ip.ToString() -ceq $Value -and $Value -notin @('0.0.0.0','::','255.255.255.255') -and -not [Net.IPAddress]::IsLoopback($ip)) 'non-host-address'
    $bytes = $ip.GetAddressBytes()
    Require (($bytes.Length -eq 4 -and $bytes[0] -gt 0 -and $bytes[0] -lt 224) -or ($bytes.Length -eq 16 -and $bytes[0] -ne 255 -and -not $ip.IsIPv4MappedToIPv6)) 'non-unicast-address'
}
function Tuple($Value) {
    Address $Value.source; Address $Value.destination
    Require ($Value.protocol -cin @('tcp','udp')) 'invalid-protocol'
    Require (($Value.port -is [long] -or $Value.port -is [int]) -and $Value.port -ge 1 -and $Value.port -le 65535) 'invalid-port'
    Require (-not ($Value.protocol -ceq 'tcp' -and $Value.port -eq 3080)) 'forbidden-3080'
}
function Same-Tuple($A, $B) { foreach ($field in @('source','destination','protocol','port')) { Require ($A[$field] -ceq $B[$field]) 'inventory-tuple-mismatch' } }
function Normalize($Value) {
    if ($Value -is [System.Collections.IDictionary]) {
        $ordered = [ordered]@{}; foreach ($key in @($Value.Keys | Sort-Object)) { $ordered[$key] = Normalize $Value[$key] }; return $ordered
    }
    if ($Value -is [array]) { $array = @($Value | ForEach-Object { Normalize $_ }); return ,$array }
    return $Value
}
function Json($Value) { ConvertTo-Json -InputObject (Normalize $Value) -Depth 60 -Compress }
function Same($A, $B, [string]$Category) { Require ((Json $A) -ceq (Json $B)) $Category }
function State($Rule) { return @{id=$Rule.id;source=$Rule.source;destination=$Rule.destination;protocol=$Rule.protocol;port=$Rule.port;direction=$Rule.direction;action='allow'} }
function Same-Rules($Actual, $Expected) {
    Require ($Actual -is [array] -and $Expected -is [array]) 'missing-rule-state'
    Same @($Actual | Sort-Object { $_.id }) @($Expected | Sort-Object { $_.id }) 'rule-state-drift'
}
function Identity($Value) {
    foreach ($field in @('hostname','machineIdentity','sshHostKeyIdentity')) { Text-Required $Value[$field] }
    Address $Value.address
}
function Check-Packet($Packet) {
    Require ($Packet.schemaVersion -eq 1) 'unsupported-schema'
    Timestamp $Packet.capturedAt
    Require ($Packet.vm105.hostname -ceq 'deepseek-harness-01') 'wrong-vm105-hostname'
    Address $Packet.vm105.address; Timestamp $Packet.vm105.capturedAt
    foreach ($field in @('correlatedMachineIdentity','sshHostKeyIdentity','provenance')) { Text-Required $Packet.vm105[$field] }
    foreach ($field in @('listener','service','tunnel','directPort','firewall','management')) { Evidence $Packet.baseline[$field] }
    Require ($Packet.baseline.listener.observation -ceq '127.0.0.1:3080' -and $Packet.baseline.service.observation -ceq 'active' -and $Packet.baseline.directPort.observation -ceq 'denied') 'isolation-baseline-mismatch'
    Require ($Packet.routes -is [array] -and $Packet.routes.Count -eq 9 -and $Packet.rules -is [array]) 'invalid-route-or-rule-collection'
    $ids = @{}; $blocked = $false
    foreach ($route in $Packet.routes) {
        Require ($route.id -is [string] -and $routeNames.Contains($route.id) -and -not $ids.ContainsKey($route.id)) 'duplicate-or-unknown-route'
        $ids[$route.id] = $true
        Require ($route.name -ceq $routeNames[$route.id]) 'route-name-mismatch'
        Timestamp $route.capturedAt; Text-Required $route.provenance
        Require ($route.decision -cin @('BLOCKED','NO_FIREWALL_CHANGE','READY_FOR_SINGLE_RULE')) 'invalid-route-decision'
        $matching = @($Packet.rules | Where-Object { $_.route -ceq $route.id })
        if ($route.decision -ceq 'BLOCKED') {
            Text-Required $route.reason
            Require ($route.releaseEligible -is [bool] -and -not $route.releaseEligible) 'blocked-route-release-claim'
            foreach ($field in @('source','destination','protocol','port','ruleId','commands','proposedPermission','targetIdentity','rules','permissions')) { Require (-not $route.Contains($field)) 'blocked-route-mutable-target' }
            foreach ($field in @('approvedRuleIds','releasableRuleIds')) { if ($route.Contains($field)) { Require ($route[$field] -is [array] -and $route[$field].Count -eq 0) 'blocked-route-rule-release-claim' } }
            if ($route.Contains('releaseStatus')) { Require ($route.releaseStatus -cin @('BLOCKED','NOT PROVEN')) 'blocked-route-status-claim' }
            Require ($matching.Count -eq 0) 'blocked-route-permission'
            $blocked = $true; continue
        }
        Tuple $route; Require ($route.source -ceq $Packet.vm105.address) 'vm105-source-mismatch'
        if ($route.decision -ceq 'NO_FIREWALL_CHANGE') {
            Require ($matching.Count -eq 0) 'no-change-route-permission'
            Evidence $route.existingPathProof; Tuple $route.existingPathProof; Same-Tuple $route $route.existingPathProof
            Require ($route.existingPathProof.exitCode -is [long] -or $route.existingPathProof.exitCode -is [int]) 'missing-path-exit'
            Require ($route.existingPathProof.exitCode -eq 0) 'existing-path-not-proven'
        } else { Require ($matching.Count -eq 1) 'route-permission-count' }
    }
    $ruleIds = @{}; $tuples = @{}; $hostBaselines = @{}
    foreach ($rule in $Packet.rules) {
        Require ($rule.id -cmatch '^phase03-[a-z0-9-]+$' -and -not $ruleIds.ContainsKey($rule.id)) 'invalid-or-duplicate-rule-id'; $ruleIds[$rule.id] = $true
        Require ($rule.route -in $ids.Keys) 'unknown-rule-route'
        Tuple $rule; $route = @($Packet.routes | Where-Object { $_.id -ceq $rule.route })[0]; Same-Tuple $rule $route
        $tupleKey = '{0}|{1}|{2}|{3}' -f $rule.source,$rule.destination,$rule.protocol,$rule.port
        Require (-not $tuples.ContainsKey($tupleKey)) 'duplicate-permission'; $tuples[$tupleKey] = $true
        foreach ($field in @('purpose','resourceOwner','intendedService')) { Text-Required $rule[$field] }
        Require ($rule.platform -ceq 'ufw' -and $rule.direction -ceq 'in' -and $rule.protocol -ceq 'tcp') 'unsupported-firewall-platform-direction-or-probe'
        Identity $rule.targetIdentity; Require ($rule.targetIdentity.address -ceq $rule.destination) 'target-identity-mismatch'
        Evidence $rule.baseline; Text-Required $rule.baseline.policy
        Require ($rule.baseline.rules -is [array]) 'missing-baseline-rules'
        $baselineIds = @{}
        foreach ($existing in $rule.baseline.rules) {
            Text-Required $existing.id
            Require (-not $baselineIds.ContainsKey($existing.id) -and $existing.id -cne $rule.id) 'baseline-rule-identity-collision'; $baselineIds[$existing.id] = $true
            $sameTuple = $true
            foreach ($field in @('source','destination','protocol','port','direction')) { if ($existing[$field] -cne $rule[$field]) { $sameTuple = $false } }
            Require (-not $sameTuple) 'baseline-rule-tuple-collision'
        }
        $target = $rule.targetIdentity.address
        if ($hostBaselines.ContainsKey($target)) { Same $hostBaselines[$target] $rule.baseline 'inconsistent-host-baseline' } else { $hostBaselines[$target] = $rule.baseline }
        Evidence $rule.listenerEvidence
        Require ($rule.listenerEvidence.address -ceq $rule.destination -and $rule.listenerEvidence.port -eq $rule.port -and $rule.listenerEvidence.service -ceq $rule.intendedService) 'listener-service-mismatch'
        Evidence $rule.sourceEvidence; Require ($rule.sourceEvidence.actualSource -ceq $rule.source) 'destination-observed-source-mismatch'
        Evidence $rule.negativeSourceEvidence; Address $rule.negativeSourceEvidence.actualSource
        Require ($rule.negativeSourceEvidence.actualSource -cne $rule.source -and $rule.negativeSourceEvidence.preexistingAuthorized -is [bool] -and -not $rule.negativeSourceEvidence.preexistingAuthorized) 'negative-source-authorized-or-unproven'
        $commandIds = @{}
        foreach ($name in @('add','inverse','allowedProbe','rejectedProbe','ruleState','postflight','rollback')) {
            $command = $rule.commands[$name]
            foreach ($field in @('id','command','expectedOutput')) { Text-Required $command[$field] }
            Require (-not $commandIds.ContainsKey($command.id)) 'duplicate-command-id'; $commandIds[$command.id] = $true
            Require ($command.expectedExitCode -is [int] -or $command.expectedExitCode -is [long]) 'missing-command-exit'
            Require ($command.expectedOutput -cnotin @('PASS','OK','SUCCESS')) 'self-reported-status-not-receipt'
        }
        $suffix = "allow in proto $($rule.protocol) from $($rule.source) to $($rule.destination) port $($rule.port) comment '$($rule.id)'"
        Require ($rule.commands.add.command -ceq "sudo -n ufw $suffix") 'noncanonical-add-command'
        Require ($rule.commands.inverse.command -ceq "sudo -n ufw --force delete $suffix") 'noncanonical-inverse-command'
        Require ($rule.commands.add.expectedExitCode -eq 0 -and $rule.commands.inverse.expectedExitCode -eq 0 -and $rule.commands.allowedProbe.expectedExitCode -eq 0 -and $rule.commands.rejectedProbe.expectedExitCode -ne 0) 'invalid-command-expectation'
        foreach ($name in @('allowedProbe','rejectedProbe')) {
            Require ($rule.commands[$name].command -ceq "nc -nvz -w 5 $($rule.destination) $($rule.port) 2>&1") 'noncanonical-probe-command'
            Evidence $rule.preChangeProbes[$name]
            $probeSource = if ($name -ceq 'allowedProbe') { $rule.source } else { $rule.negativeSourceEvidence.actualSource }
            Require ($rule.commands[$name].source -ceq $probeSource -and $rule.preChangeProbes[$name].source -ceq $probeSource) 'probe-source-mismatch'
            Same $rule.preChangeProbes[$name].command $rule.commands[$name].command 'prechange-command-mismatch'
            Require ($rule.preChangeProbes[$name].exitCode -is [long] -or $rule.preChangeProbes[$name].exitCode -is [int]) 'missing-prechange-exit'
            Text-Required $rule.preChangeProbes[$name].output
            if ($name -ceq 'rejectedProbe') { Require ($rule.preChangeProbes[$name].exitCode -ne 0) 'negative-source-connected-before-change' }
        }
    }
    if ($blocked) {
        Require ($Packet.releaseEligible -is [bool] -and -not $Packet.releaseEligible) 'blocked-packet-release-claim'
        foreach ($field in @('approvedRuleIds','releasableRuleIds')) { Require ($Packet[$field] -is [array] -and $Packet[$field].Count -eq 0) 'blocked-packet-rule-release-claim' }
        Require ($Packet.fw01Verdict -cin @('BLOCKED','NOT PROVEN')) 'blocked-packet-fw01-claim'
        if ($Packet.Contains('releaseStatus')) { Require ($Packet.releaseStatus -cin @('BLOCKED','NOT PROVEN')) 'blocked-packet-status-claim' }
        Require ($Packet.rules.Count -eq 0) 'blocked-packet-permission'
    }
}
function Check-Execution($Actual, $Expected, [string]$Since) {
    Evidence $Actual
    Require ([DateTimeOffset]$Actual.capturedAt -ge [DateTimeOffset]$Since) 'receipt-before-packet'
    foreach ($field in @('id','command')) { Same $Actual[$field] $Expected[$field] 'executed-command-mismatch' }
    Same $Actual.exitCode $Expected.expectedExitCode 'command-exit-mismatch'; Same $Actual.output $Expected.expectedOutput 'command-output-mismatch'
    if ($Expected.Contains('source')) { Same $Actual.source $Expected.source 'actual-probe-source-mismatch' }
}
function Check-Results($Packet, $Results, [string]$Digest, [string]$SelectedStage, [string]$SelectedId) {
    Require (@($Packet.routes | Where-Object { $_.decision -ceq 'BLOCKED' }).Count -eq 0) 'blocked-packet-has-no-releasable-receipts'
    Require ($Results.packetSha256 -cmatch '^[A-Fa-f0-9]{64}$' -and $Results.packetSha256 -ieq $Digest) 'packet-digest-mismatch'
    Require ($SelectedId -in @($Packet.rules.id) -and $Results.records -is [array]) 'missing-selected-rule-or-records'
    $active = @{}; $seen = @{}; $found = $false; $lastTime = [DateTimeOffset]$Packet.capturedAt
    foreach ($record in $Results.records) {
        Require ($record.stage -cin @('Postflight','Rollback') -and $record.ruleId -in @($Packet.rules.id)) 'invalid-receipt-stage-or-rule'
        $key = $record.stage + ':' + $record.ruleId; Require (-not $seen.ContainsKey($key)) 'duplicate-stage-receipt'; $seen[$key] = $true
        Timestamp $record.capturedAt; Text-Required $record.provenance
        Require ([DateTimeOffset]$record.capturedAt -ge $lastTime) 'receipt-time-order'; $lastTime = [DateTimeOffset]$record.capturedAt
        $rule = @($Packet.rules | Where-Object { $_.id -ceq $record.ruleId })[0]
        Same $record.identity $rule.targetIdentity 'current-target-identity-mismatch'
        Same $record.vm105Identity $Packet.vm105 'current-vm105-identity-mismatch'
        $prior = @($rule.baseline.rules)
        foreach ($activeRule in $active.Values) { if ($activeRule.targetIdentity.address -ceq $rule.targetIdentity.address -and $activeRule.id -cne $rule.id) { $prior += State $activeRule } }
        $added = @($prior) + @(State $rule)
        Same $record.beforePolicy $rule.baseline.policy 'before-policy-drift'; Same $record.afterPolicy $rule.baseline.policy 'after-policy-drift'
        if ($record.stage -ceq 'Postflight') {
            Require (-not $active.ContainsKey($rule.id)) 'rule-already-active'
            Same-Rules $record.beforeRules $prior; Same-Rules $record.afterRules $added
            foreach ($name in @('add','allowedProbe','rejectedProbe','ruleState','postflight')) { Check-Execution $record.executions[$name] $rule.commands[$name] $Packet.capturedAt }
            $active[$rule.id] = $rule
        } else {
            Same-Rules $record.beforeRules $added; Same-Rules $record.afterRules $prior
            foreach ($name in @('inverse','rollback')) { Check-Execution $record.executions[$name] $rule.commands[$name] $Packet.capturedAt }
            $active.Remove($rule.id)
        }
        $stateCommand = if ($record.stage -ceq 'Postflight') { 'ruleState' } else { 'rollback' }
        $observedState = $record.executions[$stateCommand].output | ConvertFrom-Json -AsHashtable -DateKind String
        Same-Rules $observedState.rules $record.afterRules
        Same $observedState.policy $record.afterPolicy 'rule-state-output-policy-mismatch'
        foreach ($name in @('listener','service','tunnel','directPort','firewall','management')) {
            Evidence $record.management[$name]
            Require ([DateTimeOffset]$record.management[$name].capturedAt -ge [DateTimeOffset]$Packet.capturedAt) 'management-receipt-before-packet'
            Same $record.management[$name].observation $Packet.baseline[$name].observation 'management-baseline-drift'
        }
        if ($record.ruleId -ceq $SelectedId -and $record.stage -ceq $SelectedStage) { $found = $true }
    }
    Require $found 'missing-selected-receipt'
    Require (($SelectedStage -ceq 'Postflight' -and $active.ContainsKey($SelectedId)) -or ($SelectedStage -ceq 'Rollback' -and -not $active.ContainsKey($SelectedId))) 'selected-stage-no-longer-current'
}

function Run-SelfTest {
    $time = '2026-01-01T00:00:00Z'
    function E([string]$Observation) { return @{capturedAt=$time;provenance='synthetic in-memory command';observation=$Observation} }
    $packet = @{schemaVersion=1;capturedAt=$time;vm105=@{hostname='deepseek-harness-01';address='192.0.2.10';correlatedMachineIdentity='synthetic-machine';sshHostKeyIdentity='SHA256:synthetic';capturedAt=$time;provenance='synthetic verified SSH'};baseline=@{};routes=@();rules=@()}
    foreach ($name in @('listener','service','tunnel','directPort','firewall','management')) { $packet.baseline[$name] = E 'synthetic observation' }
    $packet.baseline.listener.observation='127.0.0.1:3080'; $packet.baseline.service.observation='active'; $packet.baseline.directPort.observation='denied'
    foreach ($id in $routeNames.Keys) {
        $proof = E 'TCP connect exit 0'; $proof += @{source='192.0.2.10';destination='192.0.2.20';protocol='tcp';port=443;exitCode=0}
        $packet.routes += @{id=$id;name=$routeNames[$id];decision='NO_FIREWALL_CHANGE';capturedAt=$time;provenance='synthetic inventory';source='192.0.2.10';destination='192.0.2.20';protocol='tcp';port=443;existingPathProof=$proof}
    }
    Check-Packet $packet
    $packet.routes[0].decision='READY_FOR_SINGLE_RULE'
    $rule = @{id='phase03-synthetic';route='OR-AUTO';source='192.0.2.10';destination='192.0.2.20';protocol='tcp';port=443;purpose='synthetic transport';resourceOwner='synthetic owner';intendedService='synthetic service';platform='ufw';direction='in';targetIdentity=@{hostname='synthetic-destination';address='192.0.2.20';machineIdentity='synthetic-machine';sshHostKeyIdentity='SHA256:synthetic'};baseline=(E 'synthetic firewall dump');listenerEvidence=(E 'synthetic listener');sourceEvidence=(E 'synthetic destination-observed source');negativeSourceEvidence=(E 'synthetic unauthorized source');commands=@{};preChangeProbes=@{}}
    $rule.baseline += @{policy='deny incoming, allow outgoing';rules=@(@{id='baseline-ssh';source='192.0.2.30';destination='192.0.2.20';protocol='tcp';port=22;direction='in';action='allow'})}
    $rule.listenerEvidence += @{address=$rule.destination;port=$rule.port;service=$rule.intendedService}; $rule.sourceEvidence.actualSource=$rule.source
    $rule.negativeSourceEvidence += @{actualSource='192.0.2.99';preexistingAuthorized=$false}
    foreach ($name in @('add','inverse','allowedProbe','rejectedProbe','ruleState','postflight','rollback')) { $rule.commands[$name]=@{id="synthetic-$name";command="synthetic-$name-command";expectedExitCode=0;expectedOutput="synthetic-$name-observation"} }
    $rule.commands.add.command="sudo -n ufw allow in proto tcp from 192.0.2.10 to 192.0.2.20 port 443 comment 'phase03-synthetic'"
    $rule.commands.inverse.command="sudo -n ufw --force delete allow in proto tcp from 192.0.2.10 to 192.0.2.20 port 443 comment 'phase03-synthetic'"
    $rule.commands.allowedProbe.source=$rule.source; $rule.commands.rejectedProbe.source='192.0.2.99'; $rule.commands.rejectedProbe.expectedExitCode=1
    foreach ($name in @('allowedProbe','rejectedProbe')) { $rule.commands[$name].command='nc -nvz -w 5 192.0.2.20 443 2>&1' }
    $rule.commands.ruleState.expectedOutput=Json @{policy=$rule.baseline.policy;rules=(@($rule.baseline.rules)+@(State $rule))}
    $rule.commands.rollback.expectedOutput=Json @{policy=$rule.baseline.policy;rules=$rule.baseline.rules}
    foreach ($name in @('allowedProbe','rejectedProbe')) { $rule.preChangeProbes[$name]=E 'synthetic prechange probe'; $rule.preChangeProbes[$name] += @{source=$rule.commands[$name].source;command=$rule.commands[$name].command;exitCode=1;output='synthetic prechange denial'} }
    $packet.rules=@($rule); Check-Packet $packet
    $record=@{ruleId=$rule.id;stage='Postflight';capturedAt=$time;provenance='synthetic command receipts';identity=$rule.targetIdentity;vm105Identity=$packet.vm105;beforeRules=$rule.baseline.rules;afterRules=(@($rule.baseline.rules)+@(State $rule));beforePolicy=$rule.baseline.policy;afterPolicy=$rule.baseline.policy;executions=@{};management=$packet.baseline}
    foreach ($name in @('add','allowedProbe','rejectedProbe','ruleState','postflight')) {
        $command=$rule.commands[$name]; $record.executions[$name]=E 'synthetic command execution'
        $record.executions[$name] += @{id=$command.id;command=$command.command;exitCode=$command.expectedExitCode;output=$command.expectedOutput}
        if ($command.ContainsKey('source')) { $record.executions[$name].source=$command.source }
    }
    $digest='A'*64; $results=@{packetSha256=$digest;records=@($record)}
    Check-Results $packet $results $digest 'Postflight' $rule.id
    $rollback = Json $record | ConvertFrom-Json -AsHashtable -DateKind String
    $rollback.stage='Rollback'; $rollback.beforeRules=$record.afterRules; $rollback.afterRules=$record.beforeRules; $rollback.executions=@{}
    foreach ($name in @('inverse','rollback')) {
        $command=$rule.commands[$name]; $rollback.executions[$name]=E 'synthetic rollback execution'
        $rollback.executions[$name] += @{id=$command.id;command=$command.command;exitCode=$command.expectedExitCode;output=$command.expectedOutput}
    }
    Check-Results $packet @{packetSha256=$digest;records=@($record,$rollback)} $digest 'Rollback' $rule.id
    $cases = @(
        @{name='broad-source';change={param($p,$r) $p.rules[0].source='0.0.0.0/0'}},
        @{name='inverse-mismatch';change={param($p,$r) $p.rules[0].commands.inverse.command='sudo -n ufw delete 1'}},
        @{name='missing-rejected-receipt';change={param($p,$r) $r.records[0].executions.Remove('rejectedProbe')}},
        @{name='digest-altered';change={param($p,$r) $r.packetSha256='B'*64}},
        @{name='before-drift';change={param($p,$r) $r.records[0].beforeRules[0].port=2222}},
        @{name='after-drift';change={param($p,$r) $r.records[0].afterRules[0].port=2222}},
        @{name='3080';change={param($p,$r) $p.rules[0].port=3080}},
        @{name='baseline-collision';change={param($p,$r) $p.rules[0].baseline.rules[0].id=$p.rules[0].id}},
        @{name='wrong-probe-source';change={param($p,$r) $r.records[0].executions.allowedProbe.source='192.0.2.99'}},
        @{name='missing-provenance';change={param($p,$r) $p.baseline.listener.provenance=''}},
        @{name='unproven-no-change';change={param($p,$r) $p.routes[1].Remove('existingPathProof')}},
        @{name='zero-network-source';change={param($p,$r) $p.rules[0].source='0.1.2.3'}},
        @{name='fabricated-probe';change={param($p,$r) $p.rules[0].commands.allowedProbe.command='echo connected'}},
        @{name='negative-source-already-connected';change={param($p,$r) $p.rules[0].preChangeProbes.rejectedProbe.exitCode=0}},
        @{name='baseline-tuple-collision';change={param($p,$r) $p.rules[0].baseline.rules[0]=State $p.rules[0]; $p.rules[0].baseline.rules[0].id='preexisting-same-tuple'}}
    )
    foreach ($case in $cases) {
        $p=Json $packet | ConvertFrom-Json -AsHashtable -DateKind String; $r=Json $results | ConvertFrom-Json -AsHashtable -DateKind String
        Check-Packet $p; Check-Results $p $r $digest 'Postflight' $rule.id
        & $case.change $p $r
        $rejected=$false; try { Check-Packet $p; Check-Results $p $r $digest 'Postflight' $rule.id } catch { $rejected=$true }
        Require $rejected 'negative-selftest-accepted'
    }
    $p=Json $packet | ConvertFrom-Json -AsHashtable -DateKind String; $p.rules=@()
    $p.releaseEligible=$false; $p.approvedRuleIds=@(); $p.releasableRuleIds=@(); $p.fw01Verdict='BLOCKED'; $p.releaseStatus='BLOCKED'
    foreach ($route in $p.routes) {
        $route.decision='BLOCKED'; $route.reason='Synthetic missing service proof'; $route.releaseEligible=$false
        foreach ($field in @('source','destination','protocol','port','ruleId','existingPathProof')) { $route.Remove($field) }
    }
    Check-Packet $p
    $mixed=Json $p | ConvertFrom-Json -AsHashtable -DateKind String
    $mixed.routes[1]=Json $packet.routes[1] | ConvertFrom-Json -AsHashtable -DateKind String
    Check-Packet $mixed
    $blockedCases = @(
        @{name='empty-blocker';change={param($b) $b.routes[0].reason=''}},
        @{name='blocked-permission';change={param($b) $b.rules=@($rule)}},
        @{name='blocked-source';change={param($b) $b.routes[0].source='192.0.2.10'}},
        @{name='blocked-destination';change={param($b) $b.routes[0].destination='192.0.2.20'}},
        @{name='blocked-protocol';change={param($b) $b.routes[0].protocol='tcp'}},
        @{name='blocked-port';change={param($b) $b.routes[0].port=443}},
        @{name='blocked-rule-id';change={param($b) $b.routes[0].ruleId='phase03-synthetic'}},
        @{name='blocked-commands';change={param($b) $b.routes[0].commands=@{add='synthetic forbidden command'}}},
        @{name='blocked-proposed-permission';change={param($b) $b.routes[0].proposedPermission=@{port=443}}},
        @{name='blocked-target-identity';change={param($b) $b.routes[0].targetIdentity=@{address='192.0.2.20'}}},
        @{name='blocked-route-release';change={param($b) $b.routes[0].releaseEligible=$true}},
        @{name='blocked-route-approved';change={param($b) $b.routes[0].approvedRuleIds=@('phase03-synthetic')}},
        @{name='blocked-route-releasable';change={param($b) $b.routes[0].releasableRuleIds=@('phase03-synthetic')}},
        @{name='blocked-route-status';change={param($b) $b.routes[0].releaseStatus='APPROVED'}},
        @{name='blocked-route-permissions';change={param($b) $b.routes[0].permissions=@($rule)}},
        @{name='missing-route-release';change={param($b) $b.routes[0].Remove('releaseEligible')}},
        @{name='blocked-packet-release';change={param($b) $b.releaseEligible=$true}},
        @{name='blocked-approved-ids';change={param($b) $b.approvedRuleIds=@('phase03-synthetic')}},
        @{name='blocked-releasable-ids';change={param($b) $b.releasableRuleIds=@('phase03-synthetic')}},
        @{name='blocked-pass-verdict';change={param($b) $b.fw01Verdict='PASS'}},
        @{name='blocked-approved-status';change={param($b) $b.releaseStatus='APPROVED'}},
        @{name='blocked-pass-status';change={param($b) $b.releaseStatus='PASS'}}
    )
    foreach ($case in $blockedCases) {
        $b=Json $p | ConvertFrom-Json -AsHashtable -DateKind String; Check-Packet $b
        & $case.change $b
        $rejected=$false; try { Check-Packet $b } catch { $rejected=$true }; Require $rejected 'unsafe-blocked-selftest-accepted'
    }
    Write-Output ('SelfTest PASS (valid blocked, mixed, no-change, rule, postflight and rollback structures; {0} rejection cases)' -f ($cases.Count+$blockedCases.Count))
}

try {
    if ($SelfTest) { Run-SelfTest; exit 0 }
    $bytes = [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $PacketPath))
    $packet = [Text.Encoding]::UTF8.GetString($bytes).TrimStart([char]0xFEFF) | ConvertFrom-Json -AsHashtable -DateKind String
    Check-Packet $packet
    if ($Stage -ne 'Preflight') {
        Text-Required $RuleId
        $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
        $results = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $ResultsPath)) | ConvertFrom-Json -AsHashtable -DateKind String
        Check-Results $packet $results $digest $Stage $RuleId
    }
    if ($Stage -eq 'Preflight') {
        Write-Output 'Preflight PASS (structural validation only; no mutation release; independent review and controller acceptance remain required)'
    } else { Write-Output "$Stage PASS (receipt consistency only; no mutation release)" }
    exit 0
} catch {
    # Never echo parser exceptions, packet values, commands, or receipts.
    $category = if ($_.Exception.Message -cmatch '^[a-z][a-z0-9-]{2,80}$') { $_.Exception.Message } else { 'invalid-packet-or-receipt' }
    Write-Output "${Stage}:$category"; exit 1
}
