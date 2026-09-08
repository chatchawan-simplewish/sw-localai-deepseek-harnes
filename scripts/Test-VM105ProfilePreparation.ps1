[CmdletBinding()]
param(
    [string]$EvidencePath = 'docs/evidence/vm105-profile-pointer-preparation.json',
    [ValidateSet('Selector','Candidate','Closeout')]
    [string]$Stage = 'Selector',
    [switch]$SelfTest
)
function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

function Assert-ExactKeys {
    param([object]$Value, [string[]]$Expected, [string]$Label)
    Assert-True ($null -ne $Value -and $Value -isnot [string] -and $Value -isnot [Collections.IEnumerable]) "$Label object"
    $actual = @($Value.psobject.Properties.Name | Sort-Object)
    $wanted = @($Expected | Sort-Object)
    Assert-True (($actual -join "`n") -ceq ($wanted -join "`n")) "$Label keys differ"
}

function Assert-String { param([object]$Value,[string]$Label,[switch]$AllowEmpty) Assert-True ($Value -is [string] -and ($AllowEmpty -or -not [string]::IsNullOrWhiteSpace($Value)) -and $Value -notmatch '[\x00-\x08\x0b\x0c\x0e-\x1f]') "$Label string" }
function Assert-Bool { param([object]$Value,[string]$Label) Assert-True ($Value -is [bool]) "$Label bool" }
function Assert-Int { param([object]$Value,[string]$Label,[int64]$Min=([int64]::MinValue),[int64]$Max=([int64]::MaxValue)) Assert-True ($Value -is [byte] -or $Value -is [int16] -or $Value -is [int32] -or $Value -is [int64]) "$Label integer"; Assert-True ([int64]$Value -ge $Min -and [int64]$Value -le $Max) "$Label range" }
function Assert-Array { param([object]$Value,[string]$Label) Assert-True ($null -ne $Value -and $Value -is [Collections.IEnumerable] -and $Value -isnot [string] -and $Value -isnot [Collections.IDictionary]) "$Label array" }
function Assert-IsoTime { param([object]$Value,[string]$Label,[switch]$AllowNull) if($AllowNull -and $null-eq$Value){return}; Assert-String $Value $Label; $parsed=[DateTimeOffset]::MinValue; Assert-True ([DateTimeOffset]::TryParseExact($Value,'o',[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::None,[ref]$parsed)) "$Label timestamp" }
function Assert-Digest { param([object]$Value,[string]$Label,[switch]$AllowNull) if($AllowNull -and $null-eq$Value){return}; Assert-True ($Value -is [string] -and $Value -cmatch '^[A-F0-9]{64}$') "$Label digest" }
function Assert-StringArray { param([object]$Value,[string]$Label,[switch]$RequireAny) Assert-Array $Value $Label; if($RequireAny){Assert-True (@($Value).Count-gt0) "$Label empty"}; foreach($item in @($Value)){Assert-String $item "$Label item"} }
function Assert-Blockers { param([object]$Value,[bool]$Required,[string]$Label) Assert-StringArray $Value $Label; Assert-True ((@($Value).Count-gt0)-eq$Required) "$Label count" }

function Assert-Throws {
    param([scriptblock]$Action, [string]$Pattern)
    try { & $Action; throw 'Expected rejection was not raised' }
    catch { Assert-True ($_.Exception.Message -match $Pattern) "Wrong rejection category"; $script:NegativeTestCount++ }
}

function Copy-SyntheticRecord {
    param([object]$Value)
    if($null-eq$Value -or $Value-is[string] -or $Value-is[ValueType]){return $Value}
    if($Value-is[Collections.IDictionary]){$copy=[ordered]@{};foreach($key in $Value.Keys){$copy[$key]=Copy-SyntheticRecord $Value[$key]};return $copy}
    if($Value-is[Collections.IEnumerable]){$items=[Collections.Generic.List[object]]::new();foreach($item in $Value){$items.Add((Copy-SyntheticRecord $item))};return ,$items.ToArray()}
    $copy=[ordered]@{};foreach($property in $Value.psobject.Properties){$copy[$property.Name]=Copy-SyntheticRecord $property.Value};return [pscustomobject]$copy
}

function Get-UpperSha256 {
    param([byte[]]$Bytes)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes))
}

function Assert-StrictPosixPath {
    param([string]$Path,[string]$Root,[switch]$AllowRoot)
    Assert-True (-not [string]::IsNullOrWhiteSpace($Path)) 'posix-path-empty'
    Assert-True ($Path[0] -ceq '/') 'posix-path-relative'
    Assert-True ($Path -notmatch '\\|//|(^|/)\.\.?(/|$)|[\x00-\x1f]') 'posix-path-shape'
    Assert-True ($Root -match '^/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+$') 'posix-root-shape'
    $inside = $Path.StartsWith("$Root/",[StringComparison]::Ordinal)
    Assert-True ($inside -or ($AllowRoot -and $Path -ceq $Root)) 'posix-path-root'
}

function Assert-StrictPosixRelativePath {
    param([string]$Path)
    Assert-True (-not [string]::IsNullOrWhiteSpace($Path)) 'relative-path-empty'
    Assert-True ($Path[0] -cne '/') 'relative-path-rooted'
    Assert-True ($Path -notmatch '\\|//|(^|/)\.\.?(/|$)|[\x00-\x1f;&|`$<>]') 'relative-path-shape'
}

function ConvertTo-CanonicalNode {
    param([object]$Value)
    if ($null -eq $Value) { return $null }
    if ($Value -is [string] -or $Value -is [ValueType]) { return $Value }
    if ($Value -is [Collections.IDictionary]) {
        $ordered=[ordered]@{}; foreach($key in @($Value.Keys | Sort-Object)){ $ordered[[string]$key]=ConvertTo-CanonicalNode $Value[$key] }; return $ordered
    }
    if ($Value -is [Collections.IEnumerable]) { $items=[Collections.Generic.List[object]]::new();foreach($item in $Value){$items.Add((ConvertTo-CanonicalNode $item))};return ,$items.ToArray() }
    $object=[ordered]@{}; foreach($property in @($Value.psobject.Properties.Name | Sort-Object)){ $object[$property]=ConvertTo-CanonicalNode $Value.$property }; return $object
}

function Get-CanonicalStageDigest {
    param([object]$Stage,[string[]]$OmitTopLevelKeys)
    $copy=[ordered]@{}
    foreach($property in @($Stage.psobject.Properties.Name | Sort-Object)){
        if($OmitTopLevelKeys -ccontains $property){continue}
        $copy[$property]=ConvertTo-CanonicalNode $Stage.$property
    }
    return Get-UpperSha256 ([Text.Encoding]::UTF8.GetBytes(($copy | ConvertTo-Json -Depth 100 -Compress)))
}

function Assert-InstalledSourceRef {
    param([object]$Ref, [string]$PackageRoot)
    Assert-True ($Ref.sourceClass -ceq 'installed-source') 'proof-source-class'
    Assert-ExactKeys $Ref @('sourceClass','path','sha256','lineStart','lineEnd','claim') 'installedSourceRef'
    Assert-String $Ref.path 'installed-source-path'; Assert-Digest $Ref.sha256 'installed-source'
    Assert-Int $Ref.lineStart 'installed-source-lineStart' 1; Assert-Int $Ref.lineEnd 'installed-source-lineEnd' $Ref.lineStart
    if($Ref.path -ceq '/usr/local/bin/dsh'){Assert-StrictPosixPath $Ref.path '/usr/local/bin' }
    else { Assert-StrictPosixPath $Ref.path $PackageRoot -AllowRoot }
    Assert-True (($Ref.path -ceq '/usr/local/bin/dsh') -or $Ref.path.StartsWith("$PackageRoot/", [StringComparison]::Ordinal)) 'installed-source-root'
    Assert-String $Ref.claim 'installed-source-claim'
}

function Assert-SanitizedUnitRef {
    param([object]$Ref,[string]$SelectorKey)
    $allowed = @('User','Group','ExecStart','WorkingDirectory','UMask','FragmentPath','DropInPaths','ActiveState','SubState','Result','NRestarts')
    if($SelectorKey -match '^[A-Z][A-Z0-9_]{1,63}$'){$allowed += $SelectorKey}
    Assert-ExactKeys $Ref @('sourceClass','observationId','capturedAt','propertyAllowlist','observations','claim') 'sanitizedUnitRef'
    Assert-True ($Ref.sourceClass -ceq 'sanitized-unit') 'proof-source-class'
    Assert-String $Ref.observationId 'unit-observation-id'; Assert-IsoTime $Ref.capturedAt 'unit-capturedAt'
    Assert-Array $Ref.propertyAllowlist 'unit-property-allowlist'; Assert-Array $Ref.observations 'unit-observations'
    Assert-True (@($Ref.propertyAllowlist).Count -gt 0) 'unit-property-allowlist-empty'
    Assert-True (@($Ref.propertyAllowlist | Select-Object -Unique).Count -eq @($Ref.propertyAllowlist).Count) 'unit-property-allowlist-duplicate'
    foreach($name in @($Ref.propertyAllowlist)){Assert-True ($allowed -ccontains [string]$name) 'unit-property-allowlist'}
    $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($item in @($Ref.observations)) {
        Assert-ExactKeys $item @('name','value') 'sanitizedUnitObservation'
        Assert-True ($Ref.propertyAllowlist -ccontains [string]$item.name) 'unit-property-allowlist'
        Assert-True ($seen.Add([string]$item.name)) 'unit-property-duplicate'
        Assert-String $item.name 'unit-property-name'; Assert-String $item.value 'unit-property-value' -AllowEmpty
        Assert-True ($item.value -notmatch "`r|`n") 'unit-property-value-shape'
        if($item.name -ceq 'User' -or $item.name -ceq 'Group'){Assert-True ($item.value -ceq 'dsh') 'unit-identity'}
        if($item.name -ceq 'ActiveState'){Assert-True ($item.value -ceq 'active') 'unit-active'}
        if($item.name -ceq 'SubState'){Assert-True ($item.value -ceq 'running') 'unit-running'}
        if($item.name -ceq 'NRestarts'){Assert-True ($item.value -cmatch '^\d+$') 'unit-restarts'}
        if($item.name -ceq $SelectorKey){Assert-True ($item.value -ceq 'ABSENT' -or $item.value -cmatch '^/[A-Za-z0-9._/-]+$') 'unit-selector-value'}
    }
    Assert-True ($seen.Count -eq @($Ref.propertyAllowlist).Count) 'unit-property-incomplete'
    Assert-String $Ref.claim 'unit-claim'
}

function Assert-PrivilegeReceiptRef {
    param([object]$Ref)
    Assert-ExactKeys $Ref @('sourceClass','operationId','capturedAt','queryUser','sudoPath','targetExecutable','targetArgv','noninteractive','result','exitCode','rawOutputStored','claim') 'privilegeReceiptRef'
    Assert-True ($Ref.sourceClass -ceq 'privilege-receipt') 'proof-source-class'
    Assert-String $Ref.operationId 'privilege-operation'; Assert-IsoTime $Ref.capturedAt 'privilege-capturedAt'
    Assert-String $Ref.queryUser 'privilege-user'; Assert-String $Ref.sudoPath 'privilege-sudo'; Assert-String $Ref.targetExecutable 'privilege-executable'; Assert-StringArray $Ref.targetArgv 'privilege-argv'
    Assert-Bool $Ref.noninteractive 'privilege-noninteractive'; Assert-String $Ref.result 'privilege-result'; Assert-Int $Ref.exitCode 'privilege-exitCode'; Assert-Bool $Ref.rawOutputStored 'privilege-raw-output'
    Assert-True (($Ref.queryUser -ceq 'dsh') -and $Ref.noninteractive -and -not $Ref.rawOutputStored) 'privilege-receipt-safety'
    Assert-True ($Ref.sudoPath -ceq '/usr/bin/sudo') 'privilege-receipt-sudo'
    Assert-True (@('ALLOWED','DENIED') -ccontains [string]$Ref.result) 'privilege-receipt-result'
    Assert-True (($Ref.exitCode -eq 0) -eq ($Ref.result -ceq 'ALLOWED')) 'privilege-receipt-exit'
    Assert-String $Ref.claim 'privilege-receipt-claim'
}

function Assert-PrivilegeSeam {
    param([object[]]$Receipts,[string]$FutureFile)
    $expected=[ordered]@{
        'future-install'=@('/usr/bin/install','-o','root','-g','root','-m','0644','/dev/stdin',$FutureFile)
        'future-remove'=@('/usr/bin/rm','-f','--',$FutureFile)
        'future-stop'=@('/usr/bin/systemctl','stop','deepseek-harness.service')
        'future-start'=@('/usr/bin/systemctl','start','deepseek-harness.service')
        'future-reload'=@('/usr/bin/systemctl','daemon-reload')
        'future-status'=@('/usr/bin/systemctl','show','deepseek-harness.service')
    }
    Assert-True ($Receipts.Count -eq 6) 'privilege-receipt-count'
    Assert-True (@($Receipts.operationId | Select-Object -Unique).Count -eq 6) 'privilege-receipt-duplicate'
    foreach($receipt in $Receipts){
        Assert-PrivilegeReceiptRef $receipt
        Assert-True ($expected.Contains([string]$receipt.operationId)) 'privilege-receipt-id'
        $spec=$expected[[string]$receipt.operationId]
        Assert-True ($receipt.targetExecutable -ceq $spec[0]) 'privilege-receipt-executable'
        Assert-True ((@($receipt.targetArgv) -join "`0") -ceq (@($spec[1..($spec.Count-1)]) -join "`0")) 'privilege-receipt-argv'
    }
}

function Assert-Review {
    param([object]$Review,[string]$Digest,[string[]]$AllowedStatus)
    Assert-ExactKeys $Review @('status','reviewedAt','reviewer','reviewedDigest','findings') 'review'
    Assert-String $Review.status 'review-status'; Assert-True ($AllowedStatus -ccontains $Review.status) 'review-status-value'; Assert-Array $Review.findings 'review-findings'
    foreach($finding in @($Review.findings)){Assert-String $finding 'review-finding'}
    if($Review.status-ceq'PENDING'){Assert-True ($null-eq$Review.reviewedAt -and $null-eq$Review.reviewer -and $null-eq$Review.reviewedDigest -and @($Review.findings).Count-eq0) 'review-pending-fields'}
    else {Assert-IsoTime $Review.reviewedAt 'reviewedAt';Assert-String $Review.reviewer 'reviewer';Assert-Digest $Review.reviewedDigest 'reviewedDigest';Assert-True ($Review.reviewedDigest-ceq$Digest) 'review-digest';if($Review.status-ceq'ACCEPTED'){Assert-True ($Review.reviewer-notmatch'(?i)pending|implementer') 'reviewer-pending';Assert-True (@($Review.findings).Count-eq0) 'accepted-review-findings'}else{Assert-True (@($Review.findings).Count-gt0) 'rejected-review-findings'}}
}

function Assert-Target {
    param([object]$Target)
    Assert-ExactKeys $Target @('hostname','address','sshHostKeyIdentity','service','serviceUser','serviceGroup','candidateRoot','listenerHost','listenerPort','futureDropInDirectory','futureDropInFile') 'target'
    foreach($name in @('hostname','address','sshHostKeyIdentity','service','serviceUser','serviceGroup','candidateRoot','listenerHost','futureDropInDirectory','futureDropInFile')){Assert-String $Target.$name "target-$name"}
    Assert-Int $Target.listenerPort 'target-listenerPort' 1 65535
    Assert-True ($Target.hostname-ceq'deepseek-harness-01' -and $Target.address-ceq'192.168.1.139' -and $Target.service-ceq'deepseek-harness.service' -and $Target.serviceUser-ceq'dsh' -and $Target.serviceGroup-ceq'dsh' -and $Target.candidateRoot-ceq'/home/dsh/.dsh-profiles/vm105-provider-v1' -and $Target.listenerHost-ceq'127.0.0.1' -and $Target.listenerPort-eq3080 -and $Target.futureDropInDirectory-ceq'/etc/systemd/system/deepseek-harness.service.d' -and $Target.futureDropInFile-ceq'/etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf') 'target-values'
}

function Assert-InstalledEntrypoint {
    param([object]$Installed)
    Assert-ExactKeys $Installed @('wrapperPath','wrapperType','wrapperSymlink','wrapperOwner','wrapperGroup','wrapperMode','wrapperLinkCount','wrapperSha256','entrypointPath','entrypointType','entrypointSymlink','entrypointOwner','entrypointGroup','entrypointMode','entrypointLinkCount','entrypointSha256','packageRoot','packageName','packageVersion','proofRefs') 'installedEntrypoint'
    foreach($name in @('wrapperPath','wrapperType','wrapperOwner','wrapperGroup','wrapperMode','entrypointPath','entrypointType','entrypointOwner','entrypointGroup','entrypointMode','packageRoot','packageName','packageVersion')){Assert-String $Installed.$name "installed-$name"}
    Assert-Bool $Installed.wrapperSymlink 'wrapperSymlink';Assert-Bool $Installed.entrypointSymlink 'entrypointSymlink';Assert-Int $Installed.wrapperLinkCount 'wrapperLinkCount' 1 1;Assert-Int $Installed.entrypointLinkCount 'entrypointLinkCount' 1 1;Assert-Digest $Installed.wrapperSha256 'wrapperSha256';Assert-Digest $Installed.entrypointSha256 'entrypointSha256';Assert-Array $Installed.proofRefs 'installed-proofRefs'
    Assert-StrictPosixPath $Installed.packageRoot '/opt/deepseek-harness' -AllowRoot;Assert-StrictPosixPath $Installed.entrypointPath $Installed.packageRoot
    Assert-True ($Installed.wrapperPath-ceq'/usr/local/bin/dsh' -and $Installed.wrapperType-ceq'regular file' -and -not$Installed.wrapperSymlink -and $Installed.wrapperOwner-ceq'root' -and $Installed.wrapperGroup-ceq'root' -and ([Convert]::ToInt32($Installed.wrapperMode,8)-band18)-eq0 -and $Installed.entrypointType-ceq'regular file' -and -not$Installed.entrypointSymlink -and $Installed.entrypointOwner-ceq'root' -and $Installed.entrypointGroup-ceq'root' -and ([Convert]::ToInt32($Installed.entrypointMode,8)-band18)-eq0) 'installed-entrypoint-fields'
    Assert-True (@($Installed.proofRefs).Count-gt0) 'installed-proof-empty';foreach($ref in @($Installed.proofRefs)){Assert-InstalledSourceRef $ref $Installed.packageRoot}
}

function Assert-Baseline {
    param([object]$Baseline,[string]$SelectorKey)
    Assert-ExactKeys $Baseline @('repositoryOrigin','branch','capturedAt','hostname','address','sshHostKeyIdentity','installedVersion','service','listeners','localHttp','ufw','directLanDenied') 'selectorBaseline'
    foreach($name in @('repositoryOrigin','branch','hostname','address','sshHostKeyIdentity','installedVersion')){Assert-String $Baseline.$name "baseline-$name"};Assert-IsoTime $Baseline.capturedAt 'baseline-capturedAt'
    Assert-True ($Baseline.repositoryOrigin-ceq'https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git' -and $Baseline.branch-ceq'codex/vm105-authoritative-roadmap' -and $Baseline.hostname-ceq'deepseek-harness-01' -and $Baseline.address-ceq'192.168.1.139' -and $Baseline.installedVersion-match'0\.1\.1-rc\.2') 'baseline-identity'
    Assert-SanitizedUnitRef $Baseline.service $SelectorKey;Assert-Array $Baseline.listeners 'baseline-listeners';Assert-True (@($Baseline.listeners).Count-gt0) 'baseline-listeners-empty'
    foreach($listener in @($Baseline.listeners)){Assert-ExactKeys $listener @('address','port','protocol') 'baselineListener';Assert-String $listener.address 'listener-address';Assert-Int $listener.port 'listener-port' 3080 3080;Assert-String $listener.protocol 'listener-protocol';Assert-True (@('127.0.0.1','::1')-ccontains$listener.address -and $listener.protocol-ceq'tcp') 'baseline-listener'}
    Assert-ExactKeys $Baseline.localHttp @('url','statusCode','exitCode') 'baselineHttp';Assert-String $Baseline.localHttp.url 'http-url';Assert-Int $Baseline.localHttp.statusCode 'http-status' 200 200;Assert-Int $Baseline.localHttp.exitCode 'http-exit' 0 0;Assert-True ($Baseline.localHttp.url-ceq'http://127.0.0.1:3080/') 'http-url-value'
    Assert-ExactKeys $Baseline.ufw @('active','defaults','ruleIds','tcp3080Allowed') 'baselineUfw';Assert-Bool $Baseline.ufw.active 'ufw-active';Assert-String $Baseline.ufw.defaults 'ufw-defaults';Assert-StringArray $Baseline.ufw.ruleIds 'ufw-ruleIds';Assert-Bool $Baseline.ufw.tcp3080Allowed 'ufw-tcp3080';Assert-True ($Baseline.ufw.active -and -not$Baseline.ufw.tcp3080Allowed) 'baseline-ufw'
    Assert-ExactKeys $Baseline.directLanDenied @('source','destination','port','denied','timeoutMs') 'baselineDirectLan';Assert-String $Baseline.directLanDenied.source 'direct-source';Assert-String $Baseline.directLanDenied.destination 'direct-destination';Assert-Int $Baseline.directLanDenied.port 'direct-port' 3080 3080;Assert-Bool $Baseline.directLanDenied.denied 'direct-denied';Assert-Int $Baseline.directLanDenied.timeoutMs 'direct-timeout' 1 5000;Assert-True ($Baseline.directLanDenied.denied) 'baseline-direct-denial'
}

function Assert-CandidateBlueprint {
    param([object]$Blueprint,[string]$PackageRoot,[string]$CandidateRoot)
    Assert-ExactKeys $Blueprint @('directories','files','staticValidation','policyAssertions') 'candidateBlueprint';Assert-Array $Blueprint.directories 'candidate-directories';Assert-Array $Blueprint.files 'candidate-files'
    $paths=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($directory in @($Blueprint.directories)){Assert-ExactKeys $directory @('relativePath','owner','group','mode','contentSource','sourceRefs') 'candidateDirectory';Assert-StrictPosixRelativePath $directory.relativePath;Assert-True ($paths.Add($directory.relativePath)) 'candidate-path-duplicate';foreach($name in @('owner','group','mode','contentSource')){Assert-String $directory.$name "candidate-directory-$name"};Assert-True ($directory.owner-ceq'dsh' -and $directory.group-ceq'dsh' -and $directory.mode-ceq'0700' -and @('installed-default','approved-setting')-ccontains$directory.contentSource) 'candidate-directory';Assert-Array $directory.sourceRefs 'candidate-directory-sourceRefs';Assert-True (@($directory.sourceRefs).Count-gt0) 'candidate-source-empty';foreach($ref in @($directory.sourceRefs)){Assert-InstalledSourceRef $ref $PackageRoot}}
    foreach($file in @($Blueprint.files)){Assert-ExactKeys $file @('relativePath','owner','group','mode','contentLines','contentSha256','contentSource','sourceRefs') 'candidateFile';Assert-StrictPosixRelativePath $file.relativePath;Assert-True ($paths.Add($file.relativePath)) 'candidate-path-duplicate';foreach($name in @('owner','group','mode','contentSource')){Assert-String $file.$name "candidate-file-$name"};Assert-True ($file.owner-ceq'dsh' -and $file.group-ceq'dsh' -and ([Convert]::ToInt32($file.mode,8)-band63)-eq0 -and @('installed-default','approved-setting')-ccontains$file.contentSource) 'candidate-file';Assert-StringArray $file.contentLines 'candidate-contentLines';Assert-Digest $file.contentSha256 'candidate-contentSha256';$bytes=[Text.Encoding]::UTF8.GetBytes((@($file.contentLines)-join"`n")+"`n");Assert-True ((Get-UpperSha256 $bytes)-ceq$file.contentSha256) 'candidate-content-digest';Assert-Array $file.sourceRefs 'candidate-file-sourceRefs';Assert-True (@($file.sourceRefs).Count-gt0) 'candidate-source-empty';foreach($ref in @($file.sourceRefs)){Assert-InstalledSourceRef $ref $PackageRoot}}
    $static=$Blueprint.staticValidation;Assert-ExactKeys $static @('supported','executable','argv','timeoutSeconds','parser','acceptedResults','sourceRefs') 'staticValidation';Assert-Bool $static.supported 'static-supported';Assert-Int $static.timeoutSeconds 'static-timeout' 1 60;Assert-String $static.parser 'static-parser';Assert-Array $static.argv 'static-argv';Assert-Array $static.acceptedResults 'static-results';Assert-Array $static.sourceRefs 'static-sourceRefs';foreach($ref in @($static.sourceRefs)){Assert-InstalledSourceRef $ref $PackageRoot}
    if($static.supported){Assert-String $static.executable 'static-executable';Assert-StrictPosixPath $static.executable $PackageRoot;Assert-StringArray $static.argv 'static-argv' -RequireAny;Assert-StringArray $static.acceptedResults 'static-results' -RequireAny;Assert-True (@($static.argv|Where-Object{$_-ceq$CandidateRoot}).Count-eq1) 'static-candidate-argv';Assert-True ($static.parser-cmatch'^[A-Za-z][A-Za-z0-9]{1,31}V1$' -and $static.parser-cne'NoneV1') 'static-parser-value'}else{Assert-True ($null-eq$static.executable -and @($static.argv).Count-eq0 -and $static.parser-ceq'NoneV1' -and @($static.acceptedResults).Count-eq0) 'static-disabled-contract'}
    $policy=$Blueprint.policyAssertions;Assert-ExactKeys $policy @('bindHost','port','activeProviderRoutes','automaticFallback','providerSelectionConfigured','oauthStateConfigured','hermesReferences') 'policyAssertions';Assert-String $policy.bindHost 'policy-bindHost';Assert-Int $policy.port 'policy-port' 3080 3080;Assert-Int $policy.activeProviderRoutes 'policy-routes' 0 0;foreach($name in @('automaticFallback','providerSelectionConfigured','oauthStateConfigured','hermesReferences')){Assert-Bool $policy.$name "policy-$name"};Assert-True ($policy.bindHost-ceq'127.0.0.1' -and -not$policy.automaticFallback -and -not$policy.providerSelectionConfigured -and -not$policy.oauthStateConfigured -and -not$policy.hermesReferences) 'candidate-policy'
}

function Assert-SelectorDiscovery {
    param([object]$Discovery,[string]$CandidateRoot)
    Assert-ExactKeys $Discovery @('capturedAt','installedVersion','verdict','blockers','installedEntrypoint','baseline','selector','candidateBlueprint','selectorDigest','review') 'selectorDiscovery';Assert-IsoTime $Discovery.capturedAt 'selector-capturedAt';Assert-String $Discovery.installedVersion 'selector-version';Assert-String $Discovery.verdict 'selector-verdict';Assert-True (@('PASS','BLOCKED')-ccontains$Discovery.verdict) 'selector-verdict-value';Assert-Blockers $Discovery.blockers ($Discovery.verdict-ceq'BLOCKED') 'selector-blockers';Assert-Digest $Discovery.selectorDigest 'selectorDigest'
    $selectorKey=if($null-ne$Discovery.selector){[string]$Discovery.selector.name}else{''};Assert-Baseline $Discovery.baseline $selectorKey
    if($Discovery.verdict-ceq'BLOCKED'){if($null-ne$Discovery.installedEntrypoint){Assert-InstalledEntrypoint $Discovery.installedEntrypoint};Assert-True ($null-eq$Discovery.selector -and $null-eq$Discovery.candidateBlueprint) 'blocked-selector-artifacts'}
    else {
        Assert-True ($null-ne$Discovery.installedEntrypoint -and $null-ne$Discovery.selector -and $null-ne$Discovery.candidateBlueprint) 'pass-selector-artifacts';Assert-InstalledEntrypoint $Discovery.installedEntrypoint;$packageRoot=$Discovery.installedEntrypoint.packageRoot
        $selector=$Discovery.selector;Assert-ExactKeys $selector @('name','precedence','absoluteCandidateValue','futureUnitSelectorLines','effectiveProfileProbe','proof') 'selector';Assert-String $selector.name 'selector-name';Assert-True ($selector.name-cmatch'^[A-Z][A-Z0-9_]{1,63}$') 'selector-name-value';Assert-String $selector.precedence 'selector-precedence';Assert-String $selector.absoluteCandidateValue 'selector-value';Assert-True ($selector.absoluteCandidateValue-ceq$CandidateRoot) 'selector-candidate-value';Assert-StringArray $selector.futureUnitSelectorLines 'selector-unit-lines' -RequireAny
        Assert-ExactKeys $selector.effectiveProfileProbe @('executable','argv') 'effectiveProfileProbe';Assert-String $selector.effectiveProfileProbe.executable 'probe-executable';Assert-StrictPosixPath $selector.effectiveProfileProbe.executable $packageRoot;Assert-StringArray $selector.effectiveProfileProbe.argv 'probe-argv' -RequireAny;Assert-True (@($selector.effectiveProfileProbe.argv|Where-Object{$_-ceq$CandidateRoot}).Count-eq1) 'probe-candidate-argv'
        $proof=$selector.proof;Assert-ExactKeys $proof @('absolutePath','precedence','fullProfileScope','nonMerge','serviceCompatibility') 'selectorProof';foreach($name in @('absolutePath','precedence','nonMerge')){Assert-Array $proof.$name "proof-$name";Assert-True (@($proof.$name).Count-gt0) "missing-$name";foreach($ref in @($proof.$name)){Assert-InstalledSourceRef $ref $packageRoot}}
        Assert-ExactKeys $proof.fullProfileScope @('credentials','settings','plugins','sessionsState','otherMutableStores') 'fullProfileScope';foreach($store in @('credentials','settings','plugins','sessionsState','otherMutableStores')){Assert-Array $proof.fullProfileScope.$store "scope-$store";Assert-True (@($proof.fullProfileScope.$store).Count-gt0) "missing-$store";foreach($ref in @($proof.fullProfileScope.$store)){Assert-InstalledSourceRef $ref $packageRoot}}
        Assert-ExactKeys $proof.serviceCompatibility @('installed','unit') 'serviceCompatibility';Assert-Array $proof.serviceCompatibility.installed 'compat-installed';Assert-Array $proof.serviceCompatibility.unit 'compat-unit';Assert-True (@($proof.serviceCompatibility.installed).Count-gt0 -and @($proof.serviceCompatibility.unit).Count-gt0) 'missing-service-compatibility';foreach($ref in @($proof.serviceCompatibility.installed)){Assert-InstalledSourceRef $ref $packageRoot};foreach($ref in @($proof.serviceCompatibility.unit)){Assert-SanitizedUnitRef $ref $selector.name}
        Assert-CandidateBlueprint $Discovery.candidateBlueprint $packageRoot $CandidateRoot
    }
    $expected=Get-CanonicalStageDigest $Discovery @('selectorDigest','review');Assert-True ($Discovery.selectorDigest-ceq$expected) 'selector-stage-digest';Assert-Review $Discovery.review $Discovery.selectorDigest @('ACCEPTED','REJECTED');if($Discovery.verdict-ceq'PASS'){Assert-True ($Discovery.review.status-ceq'ACCEPTED') 'selector-review-not-accepted'}
}

function Assert-CutoverPrerequisites {
    param([object]$Value,[string]$FutureFile)
    Assert-ExactKeys $Value @('observedAt','verdict','privilegeSeam','dropInDirectory','blockers') 'cutoverPrerequisites';Assert-IsoTime $Value.observedAt 'prerequisite-observedAt';Assert-String $Value.verdict 'prerequisite-verdict';Assert-True (@('PASS','BLOCKED')-ccontains$Value.verdict) 'prerequisite-verdict-value';Assert-Blockers $Value.blockers ($Value.verdict-ceq'BLOCKED') 'prerequisite-blockers'
    Assert-ExactKeys $Value.privilegeSeam @('verdict','receipts') 'privilegeSeam';Assert-String $Value.privilegeSeam.verdict 'privilege-seam-verdict';Assert-True (@('PASS','BLOCKED')-ccontains$Value.privilegeSeam.verdict) 'privilege-seam-verdict-value';Assert-Array $Value.privilegeSeam.receipts 'privilege-receipts';Assert-PrivilegeSeam @($Value.privilegeSeam.receipts) $FutureFile;$allAllowed=@($Value.privilegeSeam.receipts|Where-Object{$_.result-cne'ALLOWED'}).Count-eq0;Assert-True (($Value.privilegeSeam.verdict-ceq'PASS')-eq$allAllowed) 'privilege-seam-consistency'
    $drop=$Value.dropInDirectory;Assert-ExactKeys $drop @('path','exists','realDirectory','owner','group','mode','linkStatus','broadAcl','unexpectedMount','verdict') 'dropInDirectory';Assert-String $drop.path 'dropin-path';Assert-True ($drop.path-ceq'/etc/systemd/system/deepseek-harness.service.d') 'dropin-path-value';Assert-Bool $drop.exists 'dropin-exists';Assert-Bool $drop.realDirectory 'dropin-real';Assert-String $drop.linkStatus 'dropin-linkStatus';Assert-String $drop.verdict 'dropin-verdict';Assert-True (@('PASS','BLOCKED')-ccontains$drop.verdict) 'dropin-verdict-value'
    if($drop.exists){Assert-String $drop.owner 'dropin-owner';Assert-String $drop.group 'dropin-group';Assert-String $drop.mode 'dropin-mode';Assert-Bool $drop.broadAcl 'dropin-acl';Assert-Bool $drop.unexpectedMount 'dropin-mount';$safe=$drop.realDirectory-and$drop.owner-ceq'root'-and$drop.group-ceq'root'-and$drop.mode-ceq'0755'-and$drop.linkStatus-ceq'not-link'-and-not$drop.broadAcl-and-not$drop.unexpectedMount}else{Assert-True (-not$drop.realDirectory -and $null-eq$drop.owner -and $null-eq$drop.group -and $null-eq$drop.mode -and $drop.linkStatus-ceq'absent' -and $null-eq$drop.broadAcl -and $null-eq$drop.unexpectedMount) 'dropin-absent-fields';$safe=$false};Assert-True (($drop.verdict-ceq'PASS')-eq$safe) 'dropin-consistency';Assert-True (($Value.verdict-ceq'PASS')-eq($allAllowed-and$safe)) 'prerequisite-consistency'
}

function Assert-DirectoryMetadata { param([object]$Value,[string]$ExpectedPath) Assert-ExactKeys $Value @('path','objectType','symlink','owner','group','mode','aclBroad','unexpectedMount') 'CandidateDirectoryMetadataV1';foreach($name in @('path','objectType','owner','group','mode')){Assert-String $Value.$name "directory-$name"};foreach($name in @('symlink','aclBroad','unexpectedMount')){Assert-Bool $Value.$name "directory-$name"};Assert-True ($Value.path-ceq$ExpectedPath -and $Value.objectType-ceq'directory' -and -not$Value.symlink -and $Value.owner-ceq'dsh' -and $Value.group-ceq'dsh' -and $Value.mode-ceq'0700' -and -not$Value.aclBroad -and -not$Value.unexpectedMount) 'directory-metadata-values' }
function Assert-FileMetadata { param([object]$Value,[hashtable]$Expected) Assert-ExactKeys $Value @('path','objectType','symlink','owner','group','mode','linkCount','aclBroad','unexpectedMount','contentSha256') 'CandidateFileMetadataV1';foreach($name in @('path','objectType','owner','group','mode')){Assert-String $Value.$name "file-$name"};foreach($name in @('symlink','aclBroad','unexpectedMount')){Assert-Bool $Value.$name "file-$name"};Assert-Int $Value.linkCount 'file-linkCount' 1 1;Assert-Digest $Value.contentSha256 'file-contentSha256';Assert-True ($Expected.ContainsKey($Value.path) -and $Value.objectType-ceq'regular file' -and -not$Value.symlink -and $Value.owner-ceq'dsh' -and $Value.group-ceq'dsh' -and ([Convert]::ToInt32($Value.mode,8)-band63)-eq0 -and -not$Value.aclBroad -and -not$Value.unexpectedMount -and $Value.contentSha256-ceq$Expected[$Value.path]) 'file-metadata-values' }

function Assert-SafeObservation {
    param([object]$Check,[object]$Evidence)
    $o=$Check.safeObservation;$id=$Check.id;$root=$Evidence.target.candidateRoot;$blueprint=$Evidence.selectorDiscovery.candidateBlueprint
    switch($id){
        'selector-gate'{Assert-True ($Check.parser-ceq'SelectorGateV1') 'check-parser';Assert-ExactKeys $o @('selectorDigest','selectorVerdict','reviewStatus','reviewedDigest') 'SelectorGateV1';Assert-Digest $o.selectorDigest 'gate-selectorDigest';Assert-String $o.selectorVerdict 'gate-verdict';Assert-String $o.reviewStatus 'gate-review';Assert-Digest $o.reviewedDigest 'gate-reviewedDigest';$pass=$o.selectorDigest-ceq$Evidence.selectorDiscovery.selectorDigest-and$o.selectorVerdict-ceq'PASS'-and$o.reviewStatus-ceq'ACCEPTED'-and$o.reviewedDigest-ceq$o.selectorDigest;Assert-True (($Check.result-ceq'PASS')-eq$pass) 'selector-gate-values'}
        'target-preflight'{Assert-True ($Check.parser-ceq'TargetPreflightV1') 'check-parser';Assert-ExactKeys $o @('parentAbsent','rootAbsent','ancestorsSafe') 'TargetPreflightV1';foreach($name in @('parentAbsent','rootAbsent','ancestorsSafe')){Assert-Bool $o.$name "preflight-$name"};$pass=$o.parentAbsent-and$o.rootAbsent-and$o.ancestorsSafe;Assert-True (($Check.result-ceq'PASS')-eq$pass) 'preflight-values'}
        {$_-in@('create-parent','create-root')}{Assert-True ($Check.parser-ceq'CandidateDirectoryMutationV1') 'check-parser';Assert-ExactKeys $o @('path','attempted','completed','metadata') 'CandidateDirectoryMutationV1';Assert-String $o.path 'directory-mutation-path';Assert-Bool $o.attempted 'directory-attempted';Assert-Bool $o.completed 'directory-completed';$expected=if($id-ceq'create-parent'){'/home/dsh/.dsh-profiles'}else{$root};Assert-True ($o.path-ceq$expected) 'directory-mutation-path-value';if($null-ne$o.metadata){Assert-DirectoryMetadata $o.metadata $expected};$pass=$o.attempted-and$o.completed-and$null-ne$o.metadata;Assert-True (($Check.result-ceq'PASS')-eq$pass) 'directory-mutation-values';if($Check.result-ceq'BLOCKED'){Assert-True ($o.attempted-and-not$o.completed-and$null-eq$o.metadata) 'directory-blocked-values'}}
        'write-blueprint'{Assert-True ($Check.parser-ceq'BlueprintWriteV1') 'check-parser';Assert-ExactKeys $o @('plannedWrites','completedWrites','lastOperationOrder') 'BlueprintWriteV1';Assert-Int $o.plannedWrites 'planned-writes' 0;Assert-Int $o.completedWrites 'completed-writes' 0 $o.plannedWrites;Assert-Int $o.lastOperationOrder 'last-operation-order' 0;Assert-True ($o.plannedWrites-eq(@($blueprint.directories).Count+@($blueprint.files).Count)) 'planned-write-count';Assert-True (($Check.result-ceq'PASS')-eq($o.completedWrites-eq$o.plannedWrites)) 'completed-write-count'}
        'metadata'{Assert-True ($Check.parser-ceq'CandidateMetadataSetV1') 'check-parser';Assert-ExactKeys $o @('available','directories','files','allSafe','allDigestsMatch') 'CandidateMetadataSetV1';Assert-Bool $o.available 'metadata-available';Assert-Array $o.directories 'metadata-directories';Assert-Array $o.files 'metadata-files';Assert-Bool $o.allSafe 'metadata-safe';Assert-Bool $o.allDigestsMatch 'metadata-digests';$expectedFiles=@{};foreach($f in @($blueprint.files)){$expectedFiles["$root/$($f.relativePath)"]=$f.contentSha256};foreach($d in @($o.directories)){Assert-DirectoryMetadata $d $d.path;Assert-True ($d.path-ceq'/home/dsh/.dsh-profiles' -or $d.path-ceq$root -or $d.path.StartsWith("$root/",[StringComparison]::Ordinal)) 'metadata-directory-path'};foreach($f in @($o.files)){Assert-FileMetadata $f $expectedFiles};$pass=$o.available-and$o.allSafe-and$o.allDigestsMatch-and@($o.files).Count-eq@($blueprint.files).Count;Assert-True (($Check.result-ceq'PASS')-eq$pass) 'metadata-values'}
        'static-validation'{Assert-True ($Check.parser-ceq'StaticValidationV1') 'check-parser';Assert-ExactKeys $o @('supported','exitCode','parsedResult') 'StaticValidationV1';Assert-Bool $o.supported 'static-observation-supported';Assert-String $o.parsedResult 'static-observation-result';if($null-ne$o.exitCode){Assert-Int $o.exitCode 'static-observation-exit'};if($Check.result-ceq'NOT PROVEN'){Assert-True (-not$o.supported -and $null-eq$o.exitCode -and $o.parsedResult-ceq'NOT PROVEN' -and -not$blueprint.staticValidation.supported) 'static-not-proven-contract'}elseif($Check.result-ceq'PASS'){Assert-True ($o.supported -and $o.exitCode-eq0 -and @($blueprint.staticValidation.acceptedResults)-ccontains$o.parsedResult) 'static-pass-values'}else{Assert-True ($o.parsedResult-ceq'BLOCKED' -and ($null-eq$o.exitCode -or $o.exitCode-ne0)) 'static-blocked-values'}}
        'secret-scan'{Assert-True ($Check.parser-ceq'SecretScanV1') 'check-parser';Assert-ExactKeys $o @('available','filesScanned','findingCount','categories') 'SecretScanV1';Assert-Bool $o.available 'scan-available';Assert-Int $o.filesScanned 'scan-files' 0;Assert-Int $o.findingCount 'scan-findings' 0;Assert-StringArray $o.categories 'scan-categories';$pass=$o.available-and$o.filesScanned-eq@($blueprint.files).Count-and$o.findingCount-eq0-and@($o.categories).Count-eq0;Assert-True (($Check.result-ceq'PASS')-eq$pass) 'scan-values'}
        'service-unchanged'{Assert-True ($Check.parser-ceq'ServiceBaselineV1') 'check-parser';Assert-ExactKeys $o @('available','activeState','subState','user','group','execStart','workingDirectory','umask','result','nRestarts','matchesBaseline') 'ServiceBaselineV1';Assert-Bool $o.available 'service-available';foreach($name in @('activeState','subState','user','group','execStart','workingDirectory','umask','result')){Assert-String $o.$name "service-$name" -AllowEmpty};Assert-Int $o.nRestarts 'service-restarts' 0;Assert-Bool $o.matchesBaseline 'service-match';$pass=$o.available-and$o.activeState-ceq'active'-and$o.subState-ceq'running'-and$o.user-ceq'dsh'-and$o.group-ceq'dsh'-and$o.matchesBaseline;Assert-True (($Check.result-ceq'PASS')-eq$pass) 'service-values'}
        'network-unchanged'{Assert-True ($Check.parser-ceq'NetworkBaselineV1') 'check-parser';Assert-ExactKeys $o @('available','listeners','localHttpStatus','ufwActive','tcp3080Allowed','directLanDenied','matchesBaseline') 'NetworkBaselineV1';Assert-Bool $o.available 'network-available';Assert-Array $o.listeners 'network-listeners';foreach($listener in @($o.listeners)){Assert-ExactKeys $listener @('address','port','protocol') 'network-listener'};Assert-Int $o.localHttpStatus 'network-http' 0 599;foreach($name in @('ufwActive','tcp3080Allowed','directLanDenied','matchesBaseline')){Assert-Bool $o.$name "network-$name"};$pass=$o.available-and$o.localHttpStatus-eq200-and$o.ufwActive-and-not$o.tcp3080Allowed-and$o.directLanDenied-and$o.matchesBaseline;Assert-True (($Check.result-ceq'PASS')-eq$pass) 'network-values'}
        default{throw 'unknown-check-id'}
    }
}

function Assert-CandidatePreparation {
    param([object]$Candidate,[object]$Evidence,[string[]]$ReviewStatuses)
    Assert-ExactKeys $Candidate @('selectorDigest','candidateDigest','startedAt','finishedAt','verdict','checks','mutationLedger','runtimeVerdict','blockers','review') 'candidatePreparation';Assert-Digest $Candidate.selectorDigest 'candidate-selectorDigest';Assert-Digest $Candidate.candidateDigest 'candidateDigest';Assert-IsoTime $Candidate.startedAt 'candidate-startedAt';Assert-IsoTime $Candidate.finishedAt 'candidate-finishedAt';Assert-String $Candidate.verdict 'candidate-verdict';Assert-True (@('PASS','BLOCKED')-ccontains$Candidate.verdict) 'candidate-verdict-value';Assert-True ($Candidate.runtimeVerdict-ceq'NOT PROVEN') 'runtime-verdict';Assert-Blockers $Candidate.blockers ($Candidate.verdict-ceq'BLOCKED') 'candidate-blockers';Assert-Array $Candidate.checks 'candidate-checks';Assert-Array $Candidate.mutationLedger 'mutationLedger';Assert-True ($Candidate.selectorDigest-ceq$Evidence.selectorDiscovery.selectorDigest) 'candidate-selector-digest'
    $ids=@('selector-gate','target-preflight','create-parent','create-root','write-blueprint','metadata','static-validation','secret-scan','service-unchanged','network-unchanged');$blocked=$false;$index=0
    foreach($check in @($Candidate.checks)){if($blocked){throw 'continued-after-block'};Assert-ExactKeys $check @('order','id','result','observedAt','parser','safeObservation','failureState') 'candidateCheck';Assert-Int $check.order 'check-order' 1 10;Assert-String $check.id 'check-id';Assert-String $check.result 'check-result';Assert-IsoTime $check.observedAt 'check-observedAt';Assert-String $check.parser 'check-parser';Assert-String $check.failureState 'check-failureState';Assert-True ($check.order-eq$index+1 -and $check.id-ceq$ids[$index] -and @('PASS','BLOCKED','NOT PROVEN')-ccontains$check.result -and $check.failureState-ceq'BLOCKED') 'candidate-check-fields';Assert-True ($check.result-cne'NOT PROVEN' -or $check.id-ceq'static-validation') 'not-proven-check';Assert-SafeObservation $check $Evidence;if($check.result-ceq'BLOCKED'){$blocked=$true};$index++}
    if($Candidate.verdict-ceq'PASS'){Assert-True (-not$blocked -and $index-eq10) 'candidate-check-count'}else{Assert-True ($blocked -and @($Candidate.checks)[-1].result-ceq'BLOCKED') 'candidate-blocked-check'}
    $last=0;$ledgerFailed=$false;foreach($entry in @($Candidate.mutationLedger)){Assert-ExactKeys $entry @('order','operation','path','contentSha256','result','at','secretObserved') 'mutationLedgerEntry';Assert-Int $entry.order 'mutation-order' 1;Assert-String $entry.operation 'mutation-operation';Assert-String $entry.path 'mutation-path';Assert-String $entry.result 'mutation-result';Assert-IsoTime $entry.at 'mutation-at';Assert-Bool $entry.secretObserved 'mutation-secret';Assert-True ($entry.order-eq++$last -and @('CREATE_DIRECTORY','WRITE_FILE')-ccontains$entry.operation -and @('PASS','FAILED')-ccontains$entry.result -and -not$entry.secretObserved) 'mutation-ledger-fields';if($ledgerFailed){throw 'mutation-after-failure'};if($entry.result-ceq'FAILED'){$ledgerFailed=$true};if($entry.path-ceq'/home/dsh/.dsh-profiles'){Assert-True ($entry.operation-ceq'CREATE_DIRECTORY' -and $null-eq$entry.contentSha256) 'mutation-parent'}elseif($entry.path-ceq$Evidence.target.candidateRoot){Assert-True ($entry.operation-ceq'CREATE_DIRECTORY' -and $null-eq$entry.contentSha256) 'mutation-root'}else{Assert-StrictPosixPath $entry.path $Evidence.target.candidateRoot;if($entry.operation-ceq'CREATE_DIRECTORY'){Assert-True ($null-eq$entry.contentSha256) 'mutation-directory'}else{Assert-Digest $entry.contentSha256 'mutation-file'}}}
    if($Candidate.verdict-ceq'PASS'){Assert-True (@($Candidate.mutationLedger).Count-eq(2+@($Evidence.selectorDiscovery.candidateBlueprint.directories).Count+@($Evidence.selectorDiscovery.candidateBlueprint.files).Count) -and @($Candidate.mutationLedger|Where-Object{$_.result-cne'PASS'}).Count-eq0) 'mutation-ledger-complete'}
    $expected=Get-CanonicalStageDigest $Candidate @('candidateDigest','review');Assert-True ($Candidate.candidateDigest-ceq$expected) 'candidate-stage-digest';Assert-Review $Candidate.review $Candidate.candidateDigest $ReviewStatuses
}

function Assert-OperationLedger {
    param([object]$Entries,[object]$Evidence)
    Assert-Array $Entries 'operationLedger';$failed=$false
    foreach($entry in @($Entries)){Assert-ExactKeys $entry @('at','actor','operation','target','result','secretObserved') 'operationLedgerEntry';Assert-IsoTime $entry.at 'operation-at';Assert-String $entry.actor 'operation-actor';Assert-String $entry.operation 'operation-name';Assert-String $entry.target 'operation-target';Assert-String $entry.result 'operation-result';Assert-Bool $entry.secretObserved 'operation-secret';Assert-True (@('controller','dsh')-ccontains$entry.actor -and @('READ_INSTALLED','READ_BASELINE','READ_PREREQUISITE','CREATE_DIRECTORY','WRITE_FILE','STATIC_VALIDATE','SCAN_CANDIDATE','WRITE_EVIDENCE','WRITE_HANDOFF')-ccontains$entry.operation -and @('PASS','FAILED')-ccontains$entry.result -and -not$entry.secretObserved) 'operation-ledger-values';if($failed){throw 'operation-after-failure'};if($entry.result-ceq'FAILED'){$failed=$true};Assert-True ($entry.operation-notmatch'SERVICE|SYSTEMD|DROPIN|CREDENTIAL|OAUTH|FIREWALL|POWER|ROUTE') 'operation-forbidden';if($entry.operation-in@('CREATE_DIRECTORY','WRITE_FILE','STATIC_VALIDATE','SCAN_CANDIDATE')){Assert-True ($entry.target-ceq'/home/dsh/.dsh-profiles' -or $entry.target-ceq$Evidence.target.candidateRoot -or $entry.target.StartsWith("$($Evidence.target.candidateRoot)/",[StringComparison]::Ordinal)) 'operation-target-scope'}elseif($entry.operation-ceq'WRITE_EVIDENCE'){Assert-True ($entry.target-ceq'docs/evidence/vm105-profile-pointer-preparation.json') 'operation-evidence-target'}elseif($entry.operation-ceq'WRITE_HANDOFF'){Assert-True ($entry.target-ceq'docs/handoffs/2026-09-08-vm105-profile-cutover-requirements.md') 'operation-handoff-target'}}
}

function Assert-Closeout {
    param([object]$Closeout,[object]$Evidence)
    Assert-ExactKeys $Closeout @('closedAt','verdict','selectorDigest','candidateDigest','cutoverPrerequisiteVerdict','handoffPath','handoffSha256','review') 'closeout';Assert-IsoTime $Closeout.closedAt 'closeout-closedAt';Assert-String $Closeout.verdict 'closeout-verdict';Assert-True (@('PREPARATION_READY','BLOCKED')-ccontains$Closeout.verdict) 'closeout-verdict-value';Assert-Digest $Closeout.selectorDigest 'closeout-selectorDigest';Assert-Digest $Closeout.candidateDigest 'closeout-candidateDigest';Assert-String $Closeout.cutoverPrerequisiteVerdict 'closeout-prerequisite';Assert-True (@('PASS','BLOCKED')-ccontains$Closeout.cutoverPrerequisiteVerdict) 'closeout-prerequisite-value';Assert-String $Closeout.handoffPath 'closeout-handoffPath';Assert-True ($Closeout.handoffPath-ceq'docs/handoffs/2026-09-08-vm105-profile-cutover-requirements.md') 'closeout-handoff-path';Assert-Digest $Closeout.handoffSha256 'closeout-handoffSha256';Assert-True ($Closeout.selectorDigest-ceq$Evidence.selectorDiscovery.selectorDigest -and $Closeout.candidateDigest-ceq$Evidence.candidatePreparation.candidateDigest -and $Closeout.cutoverPrerequisiteVerdict-ceq$Evidence.cutoverPrerequisites.verdict) 'closeout-digest-link'
    $ready=$Evidence.selectorDiscovery.verdict-ceq'PASS'-and$Evidence.selectorDiscovery.review.status-ceq'ACCEPTED'-and$Evidence.candidatePreparation.verdict-ceq'PASS'-and$Evidence.candidatePreparation.review.status-ceq'ACCEPTED';Assert-True (($Closeout.verdict-ceq'PREPARATION_READY')-eq$ready) 'closeout-readiness';$digest=Get-CanonicalStageDigest $Closeout @('review');Assert-Review $Closeout.review $digest @('PENDING','ACCEPTED','REJECTED')
    Assert-True (Test-Path -LiteralPath $Closeout.handoffPath -PathType Leaf) 'Missing closeout handoff';$bytes=[IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $Closeout.handoffPath));Assert-True ((Get-UpperSha256 $bytes)-ceq$Closeout.handoffSha256) 'handoff-digest';Test-NonExecutableHandoff ([Text.Encoding]::UTF8.GetString($bytes))
}

function Test-NoSecretShapedData {
    param([object]$Value)
    if($null-eq$Value-or$Value-is[ValueType]){return}
    if($Value-is[string]){Assert-True ($null-eq(Get-SecretFindingCategory $Value)) 'secret-shaped-value';return}
    if($Value-is[Collections.IDictionary]){foreach($item in $Value.Values){Test-NoSecretShapedData $item};return}
    if($Value-is[Collections.IEnumerable]){foreach($item in $Value){Test-NoSecretShapedData $item};return}
    foreach($property in $Value.psobject.Properties){Test-NoSecretShapedData $property.Value}
}

function Get-SecretFindingCategory {
    param([string]$Text)
    $candidate=$Text
    for($i=0;$i-lt3;$i++){
        if($candidate-match'(?i)["'']?(?:key|api[_-]?key|token|secret|password|client[_-]?secret|authorization|code|state|access[_-]?token|refresh[_-]?token|id[_-]?token|oauth[_-]?(?:code|state))["'']?\s*[:=]\s*(?!\(null\)(?:\s|[,}\]]|$))(?:"[^"]+"|''[^'']+''|[^\s,}\]]+)'){return 'secret-shaped-assignment'}
        if($candidate-match'(?i)(?:^|[^A-Za-z0-9_-])(?:sk-(?:or-)?|sess-)[A-Za-z0-9_-]+'){return 'secret-shaped-token'}
        if($candidate-match'-----BEGIN [A-Z ]*PRIVATE KEY-----'){return 'private-key'}
        try{$decoded=[Uri]::UnescapeDataString($candidate)}catch{return 'encoded-value'}
        if($decoded-ceq$candidate){break}
        $candidate=$decoded
    }
    return $null
}

function Test-PreparationEvidence {
    param([object]$Evidence,[ValidateSet('Selector','Candidate','Closeout')][string]$Stage)
    Assert-ExactKeys $Evidence @('schemaVersion','workflowId','target','overallVerdict','selectorDiscovery','cutoverPrerequisites','candidatePreparation','closeout','operationLedger') 'root';Assert-Int $Evidence.schemaVersion 'schemaVersion' 1 1;Assert-True ($Evidence.workflowId-ceq'vm105-profile-preparation') 'workflow-id';Assert-Target $Evidence.target;Assert-SelectorDiscovery $Evidence.selectorDiscovery $Evidence.target.candidateRoot;Assert-CutoverPrerequisites $Evidence.cutoverPrerequisites $Evidence.target.futureDropInFile;Assert-OperationLedger $Evidence.operationLedger $Evidence
    switch($Stage){
        'Selector'{Assert-True ($null-eq$Evidence.candidatePreparation -and $null-eq$Evidence.closeout) 'selector-stage-artifacts';$expected=if($Evidence.selectorDiscovery.verdict-ceq'PASS'){'SELECTOR_PASS'}else{'BLOCKED'};Assert-True ($Evidence.overallVerdict-ceq$expected) 'selector-overall-verdict'}
        'Candidate'{Assert-True ($Evidence.selectorDiscovery.verdict-ceq'PASS') 'candidate-stage-selector';Assert-True ($null-ne$Evidence.candidatePreparation -and $null-eq$Evidence.closeout) 'candidate-stage-artifacts';Assert-CandidatePreparation $Evidence.candidatePreparation $Evidence @('PENDING','ACCEPTED','REJECTED');$expected=if($Evidence.candidatePreparation.verdict-ceq'PASS'){'CANDIDATE_STATIC_PASS'}else{'BLOCKED'};Assert-True ($Evidence.overallVerdict-ceq$expected) 'candidate-overall-verdict'}
        'Closeout'{Assert-True ($Evidence.selectorDiscovery.verdict-ceq'PASS' -and $null-ne$Evidence.candidatePreparation -and $null-ne$Evidence.closeout) 'closeout-stage-artifacts';Assert-CandidatePreparation $Evidence.candidatePreparation $Evidence @('ACCEPTED');Assert-Closeout $Evidence.closeout $Evidence;$expected=if($Evidence.closeout.verdict-ceq'PREPARATION_READY'){'PREPARATION_READY'}else{'BLOCKED'};Assert-True ($Evidence.overallVerdict-ceq$expected) 'closeout-overall-verdict'}
    }
    Test-NoSecretShapedData $Evidence
}

function Test-NonExecutableHandoff {
    param([string]$Text)
    Assert-True ($Text -notmatch '(?m)^```|\b(argv|Invoke-|systemctl\s+(stop|start|restart)|daemon-reload|sudo\s)\b') 'executable-handoff'
    Assert-True ($Text -match 'no authority' -and $Text -match 'NOT PROVEN') 'handoff-boundary'
}
function New-SyntheticPreparationRecord {
    $time = '2026-09-08T00:00:00.0000000Z'
    $digest = 'A' * 64
    $source = [pscustomobject]@{
        sourceClass = 'installed-source'; path = '/opt/deepseek-harness/package/index.js'
        sha256 = $digest; lineStart = 1; lineEnd = 2; claim = 'synthetic installed proof'
    }
    $unit = [pscustomobject]@{
        sourceClass = 'sanitized-unit'; observationId = 'synthetic-unit'; capturedAt = $time
        propertyAllowlist = @('User','Group','ActiveState','SubState')
        observations = @(
            [pscustomobject]@{name='User';value='dsh'}, [pscustomobject]@{name='Group';value='dsh'},
            [pscustomobject]@{name='ActiveState';value='active'}, [pscustomobject]@{name='SubState';value='running'}
        )
        claim = 'synthetic safe unit facts'
    }
    $futureFile='/etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf'
    $privilegeSpecs=@(
        @('future-install','/usr/bin/install','-o','root','-g','root','-m','0644','/dev/stdin',$futureFile),
        @('future-remove','/usr/bin/rm','-f','--',$futureFile),
        @('future-stop','/usr/bin/systemctl','stop','deepseek-harness.service'),
        @('future-start','/usr/bin/systemctl','start','deepseek-harness.service'),
        @('future-reload','/usr/bin/systemctl','daemon-reload'),
        @('future-status','/usr/bin/systemctl','show','deepseek-harness.service')
    )
    $privileges=@($privilegeSpecs | ForEach-Object {[pscustomobject]@{
        sourceClass='privilege-receipt';operationId=$_[0];capturedAt=$time;queryUser='dsh';sudoPath='/usr/bin/sudo';targetExecutable=$_[1]
        targetArgv=@($_[2..($_.Count-1)]);noninteractive=$true;result='DENIED';exitCode=1;rawOutputStored=$false;claim='synthetic denied privilege'
    }})
    $contentLines = @('server:','  host: 127.0.0.1','  port: 3080','providers: []','automaticFallback: false')
    $contentBytes = [Text.Encoding]::UTF8.GetBytes(($contentLines -join "`n") + "`n")
    $record=[pscustomobject]@{
        schemaVersion = 1; workflowId = 'vm105-profile-preparation'
        target = [pscustomobject]@{
            hostname='deepseek-harness-01';address='192.168.1.139';sshHostKeyIdentity='SHA256:synthetic-host-key'
            service='deepseek-harness.service';serviceUser='dsh';serviceGroup='dsh'
            candidateRoot='/home/dsh/.dsh-profiles/vm105-provider-v1';listenerHost='127.0.0.1';listenerPort=3080
            futureDropInDirectory='/etc/systemd/system/deepseek-harness.service.d'
            futureDropInFile='/etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf'
        }
        overallVerdict = 'SELECTOR_PASS'
        selectorDiscovery = [pscustomobject]@{
            capturedAt=$time;installedVersion='0.1.1-rc.2';verdict='PASS';blockers=@()
            installedEntrypoint=[pscustomobject]@{
                wrapperPath='/usr/local/bin/dsh';wrapperType='regular file';wrapperSymlink=$false
                wrapperOwner='root';wrapperGroup='root';wrapperMode='0755';wrapperLinkCount=1;wrapperSha256=$digest
                entrypointPath='/opt/deepseek-harness/package/index.js';entrypointType='regular file';entrypointSymlink=$false
                entrypointOwner='root';entrypointGroup='root';entrypointMode='0644';entrypointLinkCount=1;entrypointSha256=$digest
                packageRoot='/opt/deepseek-harness/package';packageName='synthetic-harness';packageVersion='0.1.1-rc.2';proofRefs=@($source)
            }
            baseline=[pscustomobject]@{
                repositoryOrigin='https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git'
                branch='codex/vm105-authoritative-roadmap';capturedAt=$time;hostname='deepseek-harness-01'
                address='192.168.1.139';sshHostKeyIdentity='SHA256:synthetic-host-key';installedVersion='0.1.1-rc.2'
                service=$unit;listeners=@([pscustomobject]@{address='127.0.0.1';port=3080;protocol='tcp'})
                localHttp=[pscustomobject]@{url='http://127.0.0.1:3080/';statusCode=200;exitCode=0}
                ufw=[pscustomobject]@{active=$true;defaults='deny-in-allow-out';ruleIds=@('synthetic-ssh');tcp3080Allowed=$false}
                directLanDenied=[pscustomobject]@{source='controller-lan';destination='192.168.1.139';port=3080;denied=$true;timeoutMs=1000}
            }
            selector=[pscustomobject]@{
                name='SYNTHETIC_PROFILE_ROOT';precedence='synthetic installed proof';absoluteCandidateValue='/home/dsh/.dsh-profiles/vm105-provider-v1'
                futureUnitSelectorLines=@('synthetic selector line');effectiveProfileProbe=[pscustomobject]@{executable='/opt/deepseek-harness/package/index.js';argv=@('synthetic-safe-paths','/home/dsh/.dsh-profiles/vm105-provider-v1')}
                proof=[pscustomobject]@{
                    absolutePath=@($source);precedence=@($source);nonMerge=@($source)
                    fullProfileScope=[pscustomobject]@{credentials=@($source);settings=@($source);plugins=@($source);sessionsState=@($source);otherMutableStores=@($source)}
                    serviceCompatibility=[pscustomobject]@{installed=@($source);unit=@($unit)}
                }
            }
            candidateBlueprint=[pscustomobject]@{
                directories=@([pscustomobject]@{relativePath='state';owner='dsh';group='dsh';mode='0700';contentSource='installed-default';sourceRefs=@($source)})
                files=@([pscustomobject]@{relativePath='settings.yaml';owner='dsh';group='dsh';mode='0600';contentLines=$contentLines;contentSha256=(Get-UpperSha256 $contentBytes);contentSource='approved-setting';sourceRefs=@($source)})
                staticValidation=[pscustomobject]@{supported=$false;executable=$null;argv=@();timeoutSeconds=1;parser='NoneV1';acceptedResults=@();sourceRefs=@($source)}
                policyAssertions=[pscustomobject]@{bindHost='127.0.0.1';port=3080;activeProviderRoutes=0;automaticFallback=$false;providerSelectionConfigured=$false;oauthStateConfigured=$false;hermesReferences=$false}
            }
            selectorDigest=$null;review=[pscustomobject]@{status='ACCEPTED';reviewedAt=$time;reviewer='synthetic-reviewer';reviewedDigest=$null;findings=@()}
        }
        cutoverPrerequisites=[pscustomobject]@{
            observedAt=$time;verdict='BLOCKED';privilegeSeam=[pscustomobject]@{verdict='BLOCKED';receipts=$privileges}
            dropInDirectory=[pscustomobject]@{path='/etc/systemd/system/deepseek-harness.service.d';exists=$false;realDirectory=$false;owner=$null;group=$null;mode=$null;linkStatus='absent';broadAcl=$null;unexpectedMount=$null;verdict='BLOCKED'}
            blockers=@('Synthetic privilege seam denied')
        }
        candidatePreparation=$null;closeout=$null;operationLedger=@()
    }
    $record.selectorDiscovery.selectorDigest=Get-CanonicalStageDigest $record.selectorDiscovery @('selectorDigest','review')
    $record.selectorDiscovery.review.reviewedDigest=$record.selectorDiscovery.selectorDigest
    return $record
}

function New-SyntheticCandidateResult {
    param([object]$Evidence,[string]$FailAt,[switch]$ContinueAfterFailure)
    $ids = @('selector-gate','target-preflight','create-parent','create-root','write-blueprint','metadata','static-validation','secret-scan','service-unchanged','network-unchanged')
    $root=$Evidence.target.candidateRoot;$file=$Evidence.selectorDiscovery.candidateBlueprint.files[0];$time='2026-09-08T00:00:00.0000000Z'
    $dir={param($path)[pscustomobject]@{path=$path;objectType='directory';symlink=$false;owner='dsh';group='dsh';mode='0700';aclBroad=$false;unexpectedMount=$false}}
    $observations=@(
        [pscustomobject]@{parser='SelectorGateV1';value=[pscustomobject]@{selectorDigest=$Evidence.selectorDiscovery.selectorDigest;selectorVerdict='PASS';reviewStatus='ACCEPTED';reviewedDigest=$Evidence.selectorDiscovery.selectorDigest}},
        [pscustomobject]@{parser='TargetPreflightV1';value=[pscustomobject]@{parentAbsent=$true;rootAbsent=$true;ancestorsSafe=$true}},
        [pscustomobject]@{parser='CandidateDirectoryMutationV1';value=[pscustomobject]@{path='/home/dsh/.dsh-profiles';attempted=$true;completed=$true;metadata=(& $dir '/home/dsh/.dsh-profiles')}},
        [pscustomobject]@{parser='CandidateDirectoryMutationV1';value=[pscustomobject]@{path=$root;attempted=$true;completed=$true;metadata=(& $dir $root)}},
        [pscustomobject]@{parser='BlueprintWriteV1';value=[pscustomobject]@{plannedWrites=2;completedWrites=2;lastOperationOrder=4}},
        [pscustomobject]@{parser='CandidateMetadataSetV1';value=[pscustomobject]@{available=$true;directories=@((& $dir '/home/dsh/.dsh-profiles'),(& $dir $root),(& $dir "$root/state"));files=@([pscustomobject]@{path="$root/settings.yaml";objectType='regular file';symlink=$false;owner='dsh';group='dsh';mode='0600';linkCount=1;aclBroad=$false;unexpectedMount=$false;contentSha256=$file.contentSha256});allSafe=$true;allDigestsMatch=$true}},
        [pscustomobject]@{parser='StaticValidationV1';value=[pscustomobject]@{supported=$false;exitCode=$null;parsedResult='NOT PROVEN'}},
        [pscustomobject]@{parser='SecretScanV1';value=[pscustomobject]@{available=$true;filesScanned=1;findingCount=0;categories=@()}},
        [pscustomobject]@{parser='ServiceBaselineV1';value=[pscustomobject]@{available=$true;activeState='active';subState='running';user='dsh';group='dsh';execStart='/usr/local/bin/dsh';workingDirectory='/opt/deepseek-harness';umask='0077';result='success';nRestarts=0;matchesBaseline=$true}},
        [pscustomobject]@{parser='NetworkBaselineV1';value=[pscustomobject]@{available=$true;listeners=@([pscustomobject]@{address='127.0.0.1';port=3080;protocol='tcp'});localHttpStatus=200;ufwActive=$true;tcp3080Allowed=$false;directLanDenied=$true;matchesBaseline=$true}}
    )
    $checks = [Collections.Generic.List[object]]::new()
    $blocked = $false
    for ($i = 0; $i -lt $ids.Count; $i++) {
        if ($blocked -and -not $ContinueAfterFailure) { break }
        $result = if ($ids[$i] -ceq $FailAt) { 'BLOCKED' } elseif($ids[$i]-ceq'static-validation'){'NOT PROVEN'} else { 'PASS' }
        $observation=Copy-SyntheticRecord $observations[$i].value
        if($result-ceq'BLOCKED'){switch($ids[$i]){'selector-gate'{$observation.selectorVerdict='BLOCKED'}'target-preflight'{$observation.parentAbsent=$false}{$_-in@('create-parent','create-root')}{$observation.completed=$false;$observation.metadata=$null}'write-blueprint'{$observation.completedWrites=$observation.plannedWrites-1}'metadata'{$observation.available=$false;$observation.directories=[object[]]@();$observation.files=[object[]]@();$observation.allSafe=$false;$observation.allDigestsMatch=$false}'static-validation'{$observation.exitCode=$null;$observation.parsedResult='BLOCKED'}'secret-scan'{$observation.available=$false}'service-unchanged'{$observation.available=$false;$observation.matchesBaseline=$false}'network-unchanged'{$observation.available=$false;$observation.matchesBaseline=$false}}}
        $checks.Add([pscustomobject]@{order=$i+1;id=$ids[$i];result=$result;observedAt=$time;parser=$observations[$i].parser;safeObservation=$observation;failureState='BLOCKED'})
        if ($result -ceq 'BLOCKED') { $blocked = $true }
    }
    $verdict = if ($blocked) { 'BLOCKED' } else { 'PASS' }
    $ledger=if($blocked){,[object[]]@()}else{,@(
        [pscustomobject]@{order=1;operation='CREATE_DIRECTORY';path='/home/dsh/.dsh-profiles';contentSha256=$null;result='PASS';at=$time;secretObserved=$false},
        [pscustomobject]@{order=2;operation='CREATE_DIRECTORY';path=$root;contentSha256=$null;result='PASS';at=$time;secretObserved=$false},
        [pscustomobject]@{order=3;operation='CREATE_DIRECTORY';path="$root/state";contentSha256=$null;result='PASS';at=$time;secretObserved=$false},
        [pscustomobject]@{order=4;operation='WRITE_FILE';path="$root/settings.yaml";contentSha256=$file.contentSha256;result='PASS';at=$time;secretObserved=$false}
    )}
    $blockers=[object[]]@();if($blocked){$blockers=@("synthetic failure at $FailAt")}
    $candidate=[pscustomobject]@{selectorDigest=$Evidence.selectorDiscovery.selectorDigest;candidateDigest=$null;startedAt=$time;finishedAt='2026-09-08T00:00:01.0000000Z';verdict=$verdict;checks=@($checks);mutationLedger=$ledger;runtimeVerdict='NOT PROVEN';blockers=$blockers;review=[pscustomobject]@{status='PENDING';reviewedAt=$null;reviewer=$null;reviewedDigest=$null;findings=@()}}
    $candidate.candidateDigest=Get-CanonicalStageDigest $candidate @('candidateDigest','review')
    return $candidate
}

function New-SyntheticBlockedSelectorRecord {
    $record=New-SyntheticPreparationRecord;$record.overallVerdict='BLOCKED';$record.selectorDiscovery.verdict='BLOCKED';$record.selectorDiscovery.blockers=@('Synthetic selector proof unavailable');$record.selectorDiscovery.installedEntrypoint=$null;$record.selectorDiscovery.selector=$null;$record.selectorDiscovery.candidateBlueprint=$null;$record.selectorDiscovery.selectorDigest=Get-CanonicalStageDigest $record.selectorDiscovery @('selectorDigest','review');$record.selectorDiscovery.review.reviewedDigest=$record.selectorDiscovery.selectorDigest;return $record
}

function Test-SyntheticSecretScanner {
    param([string]$Text)
    $category=Get-SecretFindingCategory $Text
    if($category){"finding category=$category"}
}
if ($SelfTest) {
$script:NegativeTestCount=0;$positiveCount=0;$good=New-SyntheticPreparationRecord
function Sync-SelectorDigest { param([object]$Record) $Record.selectorDiscovery.selectorDigest=Get-CanonicalStageDigest $Record.selectorDiscovery @('selectorDigest','review');$Record.selectorDiscovery.review.reviewedDigest=$Record.selectorDiscovery.selectorDigest }
function Attach-Candidate { param([object]$Record,[string]$FailAt='',[switch]$Continue) $Record.candidatePreparation=New-SyntheticCandidateResult $Record $FailAt -ContinueAfterFailure:$Continue;$Record.overallVerdict=if($Record.candidatePreparation.verdict-ceq'PASS'){'CANDIDATE_STATIC_PASS'}else{'BLOCKED'} }

Test-PreparationEvidence $good 'Selector';$positiveCount++
$blocked=New-SyntheticBlockedSelectorRecord;Test-PreparationEvidence $blocked 'Selector';$positiveCount++
$candidate=Copy-SyntheticRecord $good;Attach-Candidate $candidate;Test-PreparationEvidence $candidate 'Candidate';$positiveCount++
$candidateBlocked=Copy-SyntheticRecord $good;Attach-Candidate $candidateBlocked 'metadata';Test-PreparationEvidence $candidateBlocked 'Candidate';$positiveCount++

$negativeCases=[Collections.Generic.List[object]]::new()
function Add-NegativeCase { param([string]$Name,[scriptblock]$Action,[string]$Pattern) $negativeCases.Add([pscustomobject]@{name=$Name;action=$Action;pattern=$Pattern}) }
Add-NegativeCase 'root allowlist' { $r=Copy-SyntheticRecord $good;$r|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'root keys differ'
Add-NegativeCase 'target allowlist' { $r=Copy-SyntheticRecord $good;$r.target|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'target keys differ'
Add-NegativeCase 'target value' { $r=Copy-SyntheticRecord $good;$r.target.address='192.0.2.105';Test-PreparationEvidence $r Selector } 'target-values'
Add-NegativeCase 'selectorDiscovery allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'selectorDiscovery keys differ'
Add-NegativeCase 'blocked selector artifacts' { $r=New-SyntheticBlockedSelectorRecord;$r.selectorDiscovery.selector=$good.selectorDiscovery.selector;Test-PreparationEvidence $r Selector } 'blocked-selector-artifacts'
Add-NegativeCase 'pass selector null installed' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.installedEntrypoint=$null;Test-PreparationEvidence $r Selector } 'pass-selector-artifacts'
Add-NegativeCase 'installed allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.installedEntrypoint|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'installedEntrypoint keys differ'
Add-NegativeCase 'installed symlink' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.installedEntrypoint.wrapperSymlink=$true;Test-PreparationEvidence $r Selector } 'installed-entrypoint-fields'
Add-NegativeCase 'installed ownership' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.installedEntrypoint.entrypointOwner='dsh';Test-PreparationEvidence $r Selector } 'installed-entrypoint-fields'
Add-NegativeCase 'installedSource allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.installedEntrypoint.proofRefs[0]|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'installedSourceRef keys differ'
Add-NegativeCase 'installedSource class' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.nonMerge[0].sourceClass='unknown';Test-PreparationEvidence $r Selector } 'proof-source-class'
Add-NegativeCase 'installedSource path' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.absolutePath[0].path='/tmp/x';Test-PreparationEvidence $r Selector } 'posix-path-root|installed-source-root'
Add-NegativeCase 'installedSource lines' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.precedence[0].lineStart=0;Test-PreparationEvidence $r Selector } 'installed-source-lineStart'
Add-NegativeCase 'sanitizedUnit allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline.service|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'sanitizedUnitRef keys differ'
Add-NegativeCase 'sanitizedUnit property' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline.service.propertyAllowlist[0]='Environment';Test-PreparationEvidence $r Selector } 'unit-property-allowlist'
Add-NegativeCase 'sanitizedUnit duplicate' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline.service.observations[1].name='User';Test-PreparationEvidence $r Selector } 'unit-property-duplicate'
Add-NegativeCase 'baseline allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'selectorBaseline keys differ'
Add-NegativeCase 'listener allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline.listeners[0]|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'baselineListener keys differ'
Add-NegativeCase 'http value' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline.localHttp.statusCode=503;Test-PreparationEvidence $r Selector } 'http-status'
Add-NegativeCase 'ufw value' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline.ufw.tcp3080Allowed=$true;Test-PreparationEvidence $r Selector } 'baseline-ufw'
Add-NegativeCase 'direct denial' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline.directLanDenied.denied=$false;Test-PreparationEvidence $r Selector } 'baseline-direct-denial'
Add-NegativeCase 'selector allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'selector keys differ'
Add-NegativeCase 'selector proof allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'selectorProof keys differ'
Add-NegativeCase 'missing absolute path' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.absolutePath=@();Test-PreparationEvidence $r Selector } 'missing-absolutePath'
Add-NegativeCase 'missing precedence' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.precedence=@();Test-PreparationEvidence $r Selector } 'missing-precedence'
Add-NegativeCase 'missing nonMerge' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.nonMerge=@();Test-PreparationEvidence $r Selector } 'missing-nonMerge'
Add-NegativeCase 'fullProfileScope allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.fullProfileScope|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'fullProfileScope keys differ'
Add-NegativeCase 'missing credentials scope' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.fullProfileScope.credentials=@();Test-PreparationEvidence $r Selector } 'missing-credentials'
Add-NegativeCase 'missing settings scope' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.fullProfileScope.settings=@();Test-PreparationEvidence $r Selector } 'missing-settings'
Add-NegativeCase 'missing plugins scope' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.fullProfileScope.plugins=@();Test-PreparationEvidence $r Selector } 'missing-plugins'
Add-NegativeCase 'missing sessions scope' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.fullProfileScope.sessionsState=@();Test-PreparationEvidence $r Selector } 'missing-sessionsState'
Add-NegativeCase 'missing other scope' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.fullProfileScope.otherMutableStores=@();Test-PreparationEvidence $r Selector } 'missing-otherMutableStores'
Add-NegativeCase 'serviceCompatibility allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.serviceCompatibility|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'serviceCompatibility keys differ'
Add-NegativeCase 'blueprint allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'candidateBlueprint keys differ'
Add-NegativeCase 'directory allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.directories[0]|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'candidateDirectory keys differ'
Add-NegativeCase 'directory mode' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.directories[0].mode='0755';Test-PreparationEvidence $r Selector } 'candidate-directory'
Add-NegativeCase 'file allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.files[0]|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'candidateFile keys differ'
Add-NegativeCase 'file mode' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.files[0].mode='0644';Test-PreparationEvidence $r Selector } 'candidate-file'
Add-NegativeCase 'file digest' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.files[0].contentSha256='B'*64;Test-PreparationEvidence $r Selector } 'candidate-content-digest'
Add-NegativeCase 'static allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.staticValidation|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'staticValidation keys differ'
Add-NegativeCase 'policy allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.policyAssertions|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'policyAssertions keys differ'
Add-NegativeCase 'policy isolation' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.policyAssertions.automaticFallback=$true;Test-PreparationEvidence $r Selector } 'candidate-policy'
Add-NegativeCase 'prerequisite allowlist' { $r=Copy-SyntheticRecord $good;$r.cutoverPrerequisites|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'cutoverPrerequisites keys differ'
Add-NegativeCase 'privilegeSeam allowlist' { $r=Copy-SyntheticRecord $good;$r.cutoverPrerequisites.privilegeSeam|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'privilegeSeam keys differ'
Add-NegativeCase 'privilege receipt allowlist' { $r=Copy-SyntheticRecord $good;$r.cutoverPrerequisites.privilegeSeam.receipts[0]|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'privilegeReceiptRef keys differ'
Add-NegativeCase 'privilege argv' { $r=Copy-SyntheticRecord $good;$r.cutoverPrerequisites.privilegeSeam.receipts[0].targetArgv[1]='dsh';Test-PreparationEvidence $r Selector } 'privilege-receipt-argv'
Add-NegativeCase 'dropIn allowlist' { $r=Copy-SyntheticRecord $good;$r.cutoverPrerequisites.dropInDirectory|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'dropInDirectory keys differ'
Add-NegativeCase 'dropIn consistency' { $r=Copy-SyntheticRecord $good;$r.cutoverPrerequisites.dropInDirectory.verdict='PASS';Test-PreparationEvidence $r Selector } 'dropin-consistency'
Add-NegativeCase 'selector digest' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selectorDigest='B'*64;Test-PreparationEvidence $r Selector } 'selector-stage-digest'
Add-NegativeCase 'review allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.review|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'review keys differ'
Add-NegativeCase 'premature accepted review' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.review.reviewer='pending-independent-review';Test-PreparationEvidence $r Selector } 'reviewer-pending'
Add-NegativeCase 'candidate allowlist' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation|Add-Member extra 1;Test-PreparationEvidence $r Candidate } 'candidatePreparation keys differ'
Add-NegativeCase 'check allowlist' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.checks[0]|Add-Member extra 1;Test-PreparationEvidence $r Candidate } 'candidateCheck keys differ'
Add-NegativeCase 'opaque observation' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.checks[1].safeObservation|Add-Member extra 1;$r.candidatePreparation.candidateDigest=Get-CanonicalStageDigest $r.candidatePreparation @('candidateDigest','review');Test-PreparationEvidence $r Candidate } 'TargetPreflightV1 keys differ'
Add-NegativeCase 'wrong parser' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.checks[0].parser='OpaqueV1';$r.candidatePreparation.candidateDigest=Get-CanonicalStageDigest $r.candidatePreparation @('candidateDigest','review');Test-PreparationEvidence $r Candidate } 'check-parser'
Add-NegativeCase 'illegal not proven' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.checks[7].result='NOT PROVEN';$r.candidatePreparation.candidateDigest=Get-CanonicalStageDigest $r.candidatePreparation @('candidateDigest','review');Test-PreparationEvidence $r Candidate } 'not-proven-check'
Add-NegativeCase 'runtime verdict' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.runtimeVerdict='PASS';$r.candidatePreparation.candidateDigest=Get-CanonicalStageDigest $r.candidatePreparation @('candidateDigest','review');Test-PreparationEvidence $r Candidate } 'runtime-verdict'
Add-NegativeCase 'mutation allowlist' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.mutationLedger[0]|Add-Member extra 1;Test-PreparationEvidence $r Candidate } 'mutationLedgerEntry keys differ'
Add-NegativeCase 'mutation operation' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.mutationLedger[0].operation='SYSTEMCTL';Test-PreparationEvidence $r Candidate } 'mutation-ledger-fields'
Add-NegativeCase 'continued after block' { $r=Copy-SyntheticRecord $good;Attach-Candidate $r 'write-blueprint' -Continue;Test-PreparationEvidence $r Candidate } 'continued-after-block'
Add-NegativeCase 'operationLedger allowlist' { $r=Copy-SyntheticRecord $good;$r.operationLedger=@([pscustomobject]@{at='2026-09-08T00:00:00.0000000Z';actor='controller';operation='READ_BASELINE';target='deepseek-harness.service';result='PASS';secretObserved=$false;extra=1});Test-PreparationEvidence $r Selector } 'operationLedgerEntry keys differ'
Add-NegativeCase 'operationLedger forbidden' { $r=Copy-SyntheticRecord $good;$r.operationLedger=@([pscustomobject]@{at='2026-09-08T00:00:00.0000000Z';actor='controller';operation='SYSTEMCTL';target='deepseek-harness.service';result='PASS';secretObserved=$false});Test-PreparationEvidence $r Selector } 'operation-ledger-values'
Add-NegativeCase 'secret shaped value' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.precedence='api_key=synthetic_nonempty_value';Sync-SelectorDigest $r;Test-PreparationEvidence $r Selector } 'secret-shaped-value'
Add-NegativeCase 'generic key assignment' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.precedence='key=synthetic';Sync-SelectorDigest $r;Test-PreparationEvidence $r Selector } 'secret-shaped-value'
Add-NegativeCase 'one character token' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.precedence='token=x';Sync-SelectorDigest $r;Test-PreparationEvidence $r Selector } 'secret-shaped-value'
Add-NegativeCase 'quoted JSON token' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.precedence='{"token":"synthetic"}';Sync-SelectorDigest $r;Test-PreparationEvidence $r Selector } 'secret-shaped-value'
Add-NegativeCase 'OAuth code assignment' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.precedence='code=synthetic';Sync-SelectorDigest $r;Test-PreparationEvidence $r Selector } 'secret-shaped-value'
Add-NegativeCase 'closeout allowlist' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.review.status='ACCEPTED';$r.candidatePreparation.review.reviewedAt='2026-09-08T00:00:00.0000000Z';$r.candidatePreparation.review.reviewer='synthetic-reviewer';$r.candidatePreparation.review.reviewedDigest=$r.candidatePreparation.candidateDigest;$r.closeout=[pscustomobject]@{closedAt='2026-09-08T00:00:00.0000000Z';verdict='PREPARATION_READY';selectorDigest=$r.selectorDiscovery.selectorDigest;candidateDigest=$r.candidatePreparation.candidateDigest;cutoverPrerequisiteVerdict='BLOCKED';handoffPath='docs/handoffs/2026-09-08-vm105-profile-cutover-requirements.md';handoffSha256=('A'*64);review=[pscustomobject]@{status='PENDING';reviewedAt=$null;reviewer=$null;reviewedDigest=$null;findings=@()};extra=1};$r.overallVerdict='PREPARATION_READY';Test-PreparationEvidence $r Closeout } 'closeout keys differ'

$missed=[Collections.Generic.List[string]]::new()
foreach($case in $negativeCases){
    try{& $case.action;$missed.Add($case.name)}
    catch{Assert-True ($_.Exception.Message-match$case.pattern) "Wrong rejection category: $($case.name) -> $($_.Exception.Message)";$script:NegativeTestCount++}
}
Assert-True ($missed.Count-eq0) "Expected rejection was not raised: $($missed-join', ')"
$captured=&{Test-SyntheticSecretScanner 'api_key: synthetic_nonempty_value'}2>&1|Out-String;Assert-True ($captured-notmatch'synthetic_nonempty_value') 'secret-output-suppression'
Assert-True ($positiveCount-eq4 -and $negativeCases.Count-eq68 -and $script:NegativeTestCount-eq$negativeCases.Count) 'self-test-count-drift'
"SELF_TEST_PASS positive=$positiveCount negative=$script:NegativeTestCount"
    exit 0
}

Assert-True (Test-Path -LiteralPath $EvidencePath -PathType Leaf) 'Evidence file missing'
$evidence = Get-Content -Raw -LiteralPath $EvidencePath | ConvertFrom-Json -DateKind String
Test-PreparationEvidence $evidence $Stage
"EVIDENCE_PASS stage=$Stage"
