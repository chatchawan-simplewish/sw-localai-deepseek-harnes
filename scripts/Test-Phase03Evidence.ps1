[CmdletBinding()]
param([ValidateSet('Network','Complete')][string]$Stage = 'Network', [switch]$SelfTest)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$files = @(
    'docs/evidence/phase-03-provider-prerequisites.md',
    'docs/evidence/phase-03-firewall-packet.json',
    'docs/evidence/phase-03-firewall-review.md',
    'docs/evidence/phase-03-firewall-results.json',
    'docs/evidence/phase-03-provider-credentials.md',
    '.planning/phases/03-provider-prerequisites/03-01-SUMMARY.md',
    '.planning/phases/03-provider-prerequisites/03-02-SUMMARY.md'
)

function Find-Categories([string]$Line) {
    # Decode repeatedly so encoded parameter separators and names cannot bypass URL checks.
    $decoded = $Line
    for ($i = 0; $i -lt 6; $i++) {
        $next = [Uri]::UnescapeDataString($decoded)
        if ($next -ceq $decoded) { break }
        $decoded = $next
    }
    if ($decoded -match '(?i)(?:[?&#]|^)(?:code|state|access_token|refresh_token|id_token)\s*=\s*[^\s&#"''<>]+') { 'oauth-parameter' }
    if ($Line -match '(?i)\b(?:sk-or-|sk-|sess-|gsk_|hf_|ghp_|github_pat_|AIza)[A-Za-z0-9_-]+') { 'provider-key' }
    if ($Line -match '-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----') { 'private-key' }
    if ($Line -match '(?i)["'']?\b(?:Proxy-Authorization|Authorization)["'']?\s*[:=]\s*(?:(?:"[^"\r\n]+")|(?:''[^''\r\n]+'')|(?:[^\s"'',}\]]+))') { 'authorization-header' }
    if ($Line -match '(?i)(?<![\w-])["'']?(?:key|api[_-]?key|token|secret|password|client_secret|access_token|refresh_token|id_token)["'']?\s*[:=]\s*(?:(?:"[^"\r\n]+")|(?:''[^''\r\n]+'')|(?:(?!null\b)[^\s"'',}\]]+))') { 'credential-assignment' }
}

function Get-Findings([hashtable]$Contents, [string]$SelectedStage) {
    $required = if ($SelectedStage -eq 'Complete') { $files } else { $files[0,1,2,3,5] }
    foreach ($file in $files) {
        if (-not $Contents.ContainsKey($file)) {
            if ($file -in $required) { '{0}:1:missing-required-file' -f $file }
            continue
        }
        $lines = [regex]::Split([string]$Contents[$file], '\r?\n')
        $pending = ''; $pendingIndent = 0; $pendingJson = $false; $pendingEquals = $false
        for ($line = 0; $line -lt $lines.Count; $line++) {
            $categories = @(Find-Categories $lines[$line])
            $indent = [regex]::Match($lines[$line], '^[ \t]*').Length
            $jsonValue = $pendingJson -and $lines[$line] -match '^\s*(?:["{\[]|(?:-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null)(?=\s*[,}\]]?\s*$))'
            if ($pending -and ($pendingEquals -or $jsonValue -or $indent -gt $pendingIndent) -and $lines[$line] -notmatch '^\s*(?:#.*)?$') {
                $categories += @(Find-Categories ($pending + $lines[$line]))
            }
            foreach ($category in @($categories | Select-Object -Unique)) { '{0}:{1}:{2}' -f $file, ($line + 1), $category }
            if ($lines[$line] -notmatch '^\s*(?:#.*)?$') { $pending = '' }
            $assignment = [regex]::Match($lines[$line], '(?i)(?:^|[{,])(?<indent>[ \t]*)(?:-[ \t]+)?(?:\$(?:env:)?)?(?<quote>["'']?)(?:key|api[_-]?key|token|secret|password|client_secret|access_token|refresh_token|id_token|Authorization|Proxy-Authorization)\k<quote>\s*(?<operator>[:=])\s*$')
            if ($assignment.Success) {
                $pending = $lines[$line]; $pendingIndent = $assignment.Groups['indent'].Length
                $pendingJson = $assignment.Groups['quote'].Value -ceq '"' -and $assignment.Groups['operator'].Value -ceq ':'
                $pendingEquals = $assignment.Groups['operator'].Value -ceq '='
            }
        }
    }
}

try {
    if ($SelfTest) {
        $tests = @(
            @('key = synthetic', 'credential-assignment'), @('"api_key":"synthetic"', 'credential-assignment'),
            @('token=synthetic', 'credential-assignment'), @('secret: synthetic', 'credential-assignment'),
            @('password = synthetic', 'credential-assignment'), @('client_secret="synthetic"', 'credential-assignment'),
            @('"refresh_token":"synthetic"', 'credential-assignment'),
            @('sk-synthetic', 'provider-key'), @('sk-or-synthetic', 'provider-key'), @('sess-synthetic', 'provider-key'),
            @('gsk_synthetic', 'provider-key'), @('hf_synthetic', 'provider-key'), @('AIzaSynthetic', 'provider-key'),
            @('Authorization: Bearer synthetic', 'authorization-header'), @('"Proxy-Authorization":"synthetic"', 'authorization-header'),
            @('-----BEGIN OPENSSH PRIVATE KEY-----', 'private-key'),
            @('https://invalid.example/?code=synthetic', 'oauth-parameter'), @('?state=synthetic', 'oauth-parameter'),
            @('?access_token=synthetic', 'oauth-parameter'), @('?refresh_token=synthetic', 'oauth-parameter'), @('?id_token=synthetic', 'oauth-parameter'),
            @('https%3A%2F%2Finvalid.example%2F%3F%63ode%3Dsynthetic', 'oauth-parameter'),
            @('%253Fstate%253Dsynthetic', 'oauth-parameter')
        )
        foreach ($test in $tests) { if ($test[1] -notin @(Find-Categories $test[0])) { throw 'Detection self-test failed' } }
        foreach ($safe in @('API key field; native OAuth; no value recorded.', 'api_key:', 'key =', '"api_key": ""', '"token": null', 'secret: ', 'Authorization:', 'https://invalid.example/?state=')) {
            if (@(Find-Categories $safe).Count) { throw 'Harmless-text self-test failed' }
        }
        $contents = @{}; foreach ($file in $files) { $contents[$file] = 'Credential-free evidence.' }
        if (@(Get-Findings $contents 'Complete').Count) { throw 'Clean allowlist self-test failed' }
        $contents[$files[4]] = "api_key=synthetic`npassword=synthetic"
        $findings = @(Get-Findings $contents 'Network')
        if ($findings.Count -ne 2 -or ($findings -join '') -match 'synthetic|api_key|password') { throw 'Value-suppression or full-allowlist self-test failed' }
        $contents.Remove($files[5]); if (@(Get-Findings $contents 'Network') -notcontains ($files[5] + ':1:missing-required-file')) { throw 'Missing-file self-test failed' }
        $contents[$files[4]] = '"api_key":' + "`n" + '"synthetic"'
        if (@(Get-Findings $contents 'Network') -notcontains ($files[4] + ':2:credential-assignment')) { throw 'Multiline-JSON self-test failed' }
        $contents[$files[5]] = 'Credential-free evidence.'
        $continuations = @(
            @('"api_key":', '123456789'), @('{"api_key":', '123456789}'),
            @('"api_key":', '[]'), @('"api_key":', '{}'),
            @('"api_key":', '"synthetic"'), @('"api_key":', '  "synthetic",'),
            @('api_key:', '  synthetic'), @('api_key:', "  'synthetic'"),
            @('api_key =', '  synthetic'), @("'api_key' =", "  'synthetic'"),
            @("'api_key':", '  synthetic'), @("'api_key':", "  'synthetic'"),
            @('  api_key:', '    123456789'), @('  - api_key:', '    synthetic'),
            @('$api_key =', 'synthetic'), @('$env:API_KEY =', 'synthetic')
        )
        foreach ($case in $continuations) {
            $contents[$files[4]] = $case[0] + "`n" + $case[1]
            $findings = @(Get-Findings $contents 'Network')
            if ($findings.Count -ne 1 -or $findings[0] -cne ($files[4] + ':2:credential-assignment')) { throw 'Continuation or exact-suppressed-report self-test failed' }
        }
        $contents[$files[4]] = "api_key:`n  # Credential-free comment`n  synthetic"
        $findings = @(Get-Findings $contents 'Network')
        if ($findings.Count -ne 1 -or $findings[0] -cne ($files[4] + ':3:credential-assignment')) { throw 'YAML-comment continuation self-test failed' }
        foreach ($safe in @("api_key:`nSeparate credential-free prose.", "'api_key':`nSeparate credential-free prose.", "api_key:`n`nSeparate credential-free prose.", "  api_key:`n  Separate credential-free prose.", ('"api_key":' + "`n" + 'null'), ('"api_key":' + "`n" + '""'), ('"api_key":' + "`n" + '}'), ('"api_key":' + "`n" + ']'), "api_key:`n  null")) {
            $contents[$files[4]] = $safe
            if (@(Get-Findings $contents 'Network').Count) { throw 'Empty-label continuation self-test failed' }
        }
        Write-Output ('SelfTest PASS ({0} detection cases; {1} continuation cases; clean, required-file, allowlist and exact suppressed-report checks)' -f $tests.Count, $continuations.Count)
        exit 0
    }
    $contents = @{}; $readFailures = @()
    foreach ($file in $files) {
        $path = Join-Path (Split-Path $PSScriptRoot -Parent) $file
        try { if (Test-Path -LiteralPath $path) { $contents[$file] = [IO.File]::ReadAllText($path) } }
        catch { $readFailures += '{0}:1:read-failure' -f $file }
    }
    $findings = @($readFailures) + @(Get-Findings $contents $Stage)
    if ($findings.Count) { $findings | Write-Output; exit 1 }
    exit 0
}
catch { Write-Output ($files[0] + ':1:scanner-failure'); exit 1 }
