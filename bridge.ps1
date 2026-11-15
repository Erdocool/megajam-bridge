# MegaJam agent bridge for Windows PowerShell 5.1+
# Secret-free in the repo: pass the bot token and shared secret via $MJ_TOKEN
# and $MJ_SECRET (or a local config file). Transport is the Telegram Bot API
# (language-specific description slots) plus encrypted inline/Telegraph blobs.
# This script never calls getUpdates, so it does not conflict with other
# consumers of the same bot token.
# Default engine is Cursor CLI (cursor-agent). Set $MJ_ENGINE='claude' to use
# Claude Code instead. Set $MJ_ENGINE='exec' for NO AI agent: only '!py'
# (UE Python in the open Unreal Editor via Python Remote Execution) and
# '!pyurl <github-url>' messages are run, everything else gets a short note.
# '!py' / '!pyurl' also work with the cursor/claude engines.
# Usage (first run):
#   $MJ_ENGINE='cursor'; $MJ_TOKEN='...'; $MJ_SECRET='...'; $MJ_PERMISSION='bypassPermissions'; irm <raw-url> | iex
# Later runs (config already saved):
#   irm <raw-url> | iex
# Or run the saved copy:
#   powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.megajam-bridge\bridge.ps1"

$ErrorActionPreference = 'Stop'

# Capture invocation context immediately. After iex, $PSCommandPath is empty
# and $MyInvocation inside functions no longer refers to the script body.
$script:StartupCommandPath = $null
$script:StartupDefinition = $null
$script:StartupScriptBlock = $null
try { $script:StartupCommandPath = $PSCommandPath } catch {}
try { $script:StartupDefinition = [string]$MyInvocation.MyCommand.Definition } catch {}
try {
    if ($MyInvocation.MyCommand.ScriptBlock) {
        $script:StartupScriptBlock = $MyInvocation.MyCommand.ScriptBlock.ToString()
    }
} catch {}

$script:RawScriptUrl = 'https://raw.githubusercontent.com/Erdocool/megajam-bridge/main/bridge.ps1'

function Get-MJVar([string]$Name) {
    try {
        $v = Get-Variable -Name $Name -Scope 1 -ErrorAction SilentlyContinue
        if ($v -ne $null -and -not [string]::IsNullOrWhiteSpace([string]$v.Value)) { return [string]$v.Value }
    } catch {}
    try {
        $v = Get-Variable -Name $Name -Scope Global -ErrorAction SilentlyContinue
        if ($v -ne $null -and -not [string]::IsNullOrWhiteSpace([string]$v.Value)) { return [string]$v.Value }
    } catch {}
    return $null
}

function Write-Live([string]$Text, [string]$Color) {
    if ([string]::IsNullOrWhiteSpace($Color)) {
        Write-Host $Text
    } else {
        Write-Host $Text -ForegroundColor $Color
    }
}

function Hide-Secret([string]$Text) {
    if ([string]::IsNullOrWhiteSpace($Text)) { return $Text }
    $t = $Text
    if (-not [string]::IsNullOrWhiteSpace($script:Token)) { $t = $t.Replace($script:Token, '***') }
    if (-not [string]::IsNullOrWhiteSpace($script:Secret)) { $t = $t.Replace($script:Secret, '***') }
    return $t
}

function Initialize-Utf8Console {
    try { $null = & chcp.com 65001 | Out-Null } catch {}
    try {
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [Console]::InputEncoding = $utf8
        [Console]::OutputEncoding = $utf8
        $script:OutputEncoding = $utf8
        $global:OutputEncoding = $utf8
    } catch {}
}

function Initialize-Tls {
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    } catch {}
}

function Get-ConfigDir {
    return (Join-Path $env:USERPROFILE '.megajam-bridge')
}

function Get-ConfigPath {
    return (Join-Path (Get-ConfigDir) 'config.json')
}

function Read-LocalConfig {
    $path = Get-ConfigPath
    if (-not (Test-Path -LiteralPath $path)) { return $null }
    try {
        $raw = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
        return ($raw | ConvertFrom-Json)
    } catch {
        Write-Live ("Yerel config okunamadi: " + $path) 'Yellow'
        return $null
    }
}

function Save-LocalConfig {
    $dir = Get-ConfigDir
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $obj = @{
        Token          = $script:Token
        Secret         = $script:Secret
        WorkDir        = $script:WorkDir
        Engine         = $script:Engine
        ClaudeExe      = $script:ClaudeExe
        CursorExe      = $script:CursorExe
        Model          = $script:AgentModel
        PermissionMode = $script:PermissionMode
        TimeoutSec     = $script:TimeoutSec
        InLang         = $script:InLang
        OutLang        = $script:OutLang
        PollSec        = $script:PollSec
        LastInSeq      = $script:LastInSeq
        LastOutSeq     = $script:LastOutSeq
        TelegraphToken = $script:TelegraphToken
    }
    $json = $obj | ConvertTo-Json
    $path = Get-ConfigPath
    $utf8bom = New-Object System.Text.UTF8Encoding $true
    [System.IO.File]::WriteAllText($path, $json, $utf8bom)
}

function Resolve-ClaudeExe([string]$Override) {
    if (-not [string]::IsNullOrWhiteSpace($Override) -and (Test-Path -LiteralPath $Override)) {
        return $Override
    }
    $candidates = @()
    $candidates += (Join-Path $env:USERPROFILE (Join-Path '.local' (Join-Path 'bin' 'claude.exe')))
    $cmd = Get-Command claude.exe -ErrorAction SilentlyContinue
    if ($cmd -ne $null -and -not [string]::IsNullOrWhiteSpace($cmd.Source)) { $candidates += $cmd.Source }
    $cmd2 = Get-Command claude -ErrorAction SilentlyContinue
    if ($cmd2 -ne $null -and -not [string]::IsNullOrWhiteSpace($cmd2.Source)) { $candidates += $cmd2.Source }
    foreach ($c in $candidates) {
        if (-not [string]::IsNullOrWhiteSpace($c) -and (Test-Path -LiteralPath $c)) { return $c }
    }
    if (-not [string]::IsNullOrWhiteSpace($Override)) { return $Override }
    return $candidates[0]
}

function Test-MJCursorPath([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    # Prefer the official Cursor CLI binary. Bare "agent" can be another product
    # (for example a Grok agent host), so only accept "agent*" under cursor-agent.
    $leaf = [System.IO.Path]::GetFileName($Path)
    if ($leaf -match '(?i)^cursor-agent(\.(exe|cmd|bat|ps1))?$') { return $true }
    $norm = $Path.Replace('/', '\').ToLower()
    if ($norm -like '*\cursor-agent\agent*') { return $true }
    return $false
}

function Add-MJCandidate {
    param(
        [System.Collections.Generic.List[string]]$List,
        [string]$Path
    )
    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    foreach ($existing in $List) {
        if ([string]::Equals($existing, $Path, [System.StringComparison]::OrdinalIgnoreCase)) { return }
    }
    [void]$List.Add($Path)
}

function Resolve-CursorExe([string]$Override) {
    if (-not [string]::IsNullOrWhiteSpace($Override) -and (Test-Path -LiteralPath $Override)) {
        return $Override
    }

    $candidates = New-Object System.Collections.Generic.List[string]
    $local = $env:LOCALAPPDATA
    if (-not [string]::IsNullOrWhiteSpace($local)) {
        $root = Join-Path $local 'cursor-agent'
        Add-MJCandidate $candidates (Join-Path $root 'cursor-agent.exe')
        Add-MJCandidate $candidates (Join-Path $root 'cursor-agent.cmd')
    }
    $homeBin = Join-Path $env:USERPROFILE (Join-Path '.local' 'bin')
    Add-MJCandidate $candidates (Join-Path $homeBin 'cursor-agent.exe')
    Add-MJCandidate $candidates (Join-Path $homeBin 'cursor-agent.cmd')
    Add-MJCandidate $candidates (Join-Path $homeBin 'cursor-agent')

    foreach ($name in @('cursor-agent.exe', 'cursor-agent.cmd', 'cursor-agent')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd -ne $null -and -not [string]::IsNullOrWhiteSpace($cmd.Source) -and (Test-MJCursorPath $cmd.Source)) {
            Add-MJCandidate $candidates $cmd.Source
        }
    }

    # Official docs also expose an "agent" alias; only use it if it is Cursor's.
    foreach ($name in @('agent.exe', 'agent.cmd', 'agent')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd -ne $null -and -not [string]::IsNullOrWhiteSpace($cmd.Source) -and (Test-MJCursorPath $cmd.Source)) {
            Add-MJCandidate $candidates $cmd.Source
        }
    }

    foreach ($c in $candidates) {
        if (-not [string]::IsNullOrWhiteSpace($c) -and (Test-Path -LiteralPath $c)) { return $c }
    }
    if (-not [string]::IsNullOrWhiteSpace($Override)) { return $Override }
    if (-not [string]::IsNullOrWhiteSpace($local)) {
        return (Join-Path (Join-Path $local 'cursor-agent') 'cursor-agent.exe')
    }
    return (Join-Path $homeBin 'cursor-agent.exe')
}

function Test-MJAutoApprove {
    $pm = $script:PermissionMode
    if ([string]::IsNullOrWhiteSpace($pm)) { return $false }
    $n = $pm.Trim().ToLower()
    return ($n -eq 'bypasspermissions' -or $n -eq 'unrestricted' -or $n -eq 'force' -or $n -eq 'yolo')
}

function Resolve-Config {
    $cfg = Read-LocalConfig

    $tok = Get-MJVar 'MJ_TOKEN'
    if ([string]::IsNullOrWhiteSpace($tok)) { $tok = Get-MJVar 'MJ_BOT' }
    if ([string]::IsNullOrWhiteSpace($tok)) { $tok = Get-MJVar 'MJ_BOT_TOKEN' }
    $sec = Get-MJVar 'MJ_SECRET'
    $wd  = Get-MJVar 'MJ_WORKDIR'
    $ce  = Get-MJVar 'MJ_CLAUDE'
    $cu  = Get-MJVar 'MJ_CURSOR'
    $eng = Get-MJVar 'MJ_ENGINE'
    $md  = Get-MJVar 'MJ_MODEL'
    $pm  = Get-MJVar 'MJ_PERMISSION'
    $to  = Get-MJVar 'MJ_TIMEOUT'
    $il  = Get-MJVar 'MJ_IN_LANG'
    $ol  = Get-MJVar 'MJ_OUT_LANG'
    $po  = Get-MJVar 'MJ_POLL'
    $py  = Get-MJVar 'MJ_PYTHON'
    if ([string]::IsNullOrWhiteSpace($py) -and $env:MEGAJAM_PYTHON) { $py = $env:MEGAJAM_PYTHON }
    $script:PythonOverride = $py

    if ([string]::IsNullOrWhiteSpace($tok) -and $env:MEGAJAM_BOT_TOKEN) { $tok = $env:MEGAJAM_BOT_TOKEN }
    if ([string]::IsNullOrWhiteSpace($tok) -and $env:TELEGRAM_GROK_BOT_TOKEN) { $tok = $env:TELEGRAM_GROK_BOT_TOKEN }
    if ([string]::IsNullOrWhiteSpace($sec) -and $env:MEGAJAM_SECRET) { $sec = $env:MEGAJAM_SECRET }
    if ([string]::IsNullOrWhiteSpace($wd)  -and $env:MEGAJAM_WORKDIR) { $wd = $env:MEGAJAM_WORKDIR }
    if ([string]::IsNullOrWhiteSpace($ce)  -and $env:MEGAJAM_CLAUDE) { $ce = $env:MEGAJAM_CLAUDE }
    if ([string]::IsNullOrWhiteSpace($cu)  -and $env:MEGAJAM_CURSOR) { $cu = $env:MEGAJAM_CURSOR }
    if ([string]::IsNullOrWhiteSpace($eng) -and $env:MEGAJAM_ENGINE) { $eng = $env:MEGAJAM_ENGINE }
    if ([string]::IsNullOrWhiteSpace($md)  -and $env:MEGAJAM_MODEL) { $md = $env:MEGAJAM_MODEL }
    if ([string]::IsNullOrWhiteSpace($pm)  -and $env:MEGAJAM_PERMISSION) { $pm = $env:MEGAJAM_PERMISSION }

    if ([string]::IsNullOrWhiteSpace($tok) -and $cfg -ne $null -and $cfg.Token) { $tok = [string]$cfg.Token }
    if ([string]::IsNullOrWhiteSpace($sec) -and $cfg -ne $null -and $cfg.Secret) { $sec = [string]$cfg.Secret }
    if ([string]::IsNullOrWhiteSpace($wd)  -and $cfg -ne $null -and $cfg.WorkDir) { $wd = [string]$cfg.WorkDir }
    if ([string]::IsNullOrWhiteSpace($ce)  -and $cfg -ne $null -and $cfg.ClaudeExe) { $ce = [string]$cfg.ClaudeExe }
    if ([string]::IsNullOrWhiteSpace($cu)  -and $cfg -ne $null -and $cfg.CursorExe) { $cu = [string]$cfg.CursorExe }
    if ([string]::IsNullOrWhiteSpace($eng) -and $cfg -ne $null -and $cfg.Engine) { $eng = [string]$cfg.Engine }
    if ([string]::IsNullOrWhiteSpace($md)  -and $cfg -ne $null -and $cfg.Model) { $md = [string]$cfg.Model }
    if ([string]::IsNullOrWhiteSpace($pm)  -and $cfg -ne $null -and $cfg.PermissionMode) { $pm = [string]$cfg.PermissionMode }
    if ([string]::IsNullOrWhiteSpace($to)  -and $cfg -ne $null -and $cfg.TimeoutSec) { $to = [string]$cfg.TimeoutSec }
    if ([string]::IsNullOrWhiteSpace($il)  -and $cfg -ne $null -and $cfg.InLang) { $il = [string]$cfg.InLang }
    if ([string]::IsNullOrWhiteSpace($ol)  -and $cfg -ne $null -and $cfg.OutLang) { $ol = [string]$cfg.OutLang }
    if ([string]::IsNullOrWhiteSpace($po)  -and $cfg -ne $null -and $cfg.PollSec) { $po = [string]$cfg.PollSec }

    if ([string]::IsNullOrWhiteSpace($wd)) { $wd = 'C:\MegaJam' }
    if ([string]::IsNullOrWhiteSpace($pm)) { $pm = 'acceptEdits' }
    if ([string]::IsNullOrWhiteSpace($to)) { $to = '900' }
    if ([string]::IsNullOrWhiteSpace($il)) { $il = 'ia' }
    if ([string]::IsNullOrWhiteSpace($ol)) { $ol = 'eo' }
    if ([string]::IsNullOrWhiteSpace($po)) { $po = '1' }

    if ([string]::IsNullOrWhiteSpace($tok) -or [string]::IsNullOrWhiteSpace($sec)) {
        Write-Host ''
        Write-Host 'MegaJam koprusu: bot token veya gizli anahtar eksik.' -ForegroundColor Red
        Write-Host 'Ilk calistirmada PowerShell''e sunlari yazin (tek satir):' -ForegroundColor Yellow
        Write-Host '  $MJ_ENGINE=''cursor''; $MJ_TOKEN=''BOT_TOKEN''; $MJ_SECRET=''SECRET''; irm <raw-url> | iex'
        Write-Host 'Ayarlar sonra su dosyaya kaydedilir:'
        Write-Host ('  ' + (Get-ConfigPath))
        exit 1
    }

    $script:Token          = $tok.Trim()
    $script:Secret         = $sec.Trim()
    $script:WorkDir        = $wd.Trim()
    $script:PermissionMode = $pm.Trim()
    $script:TimeoutSec     = [int]$to
    $script:InLang         = $il.Trim()
    $script:OutLang        = $ol.Trim()
    $script:PollSec        = [double]$po
    if ($script:PollSec -lt 0.4) { $script:PollSec = 0.4 }

    if ([string]::IsNullOrWhiteSpace($eng)) { $eng = 'cursor' }
    $eng = $eng.Trim().ToLower()
    if ($eng -eq 'cursor-agent' -or $eng -eq 'cursorcli' -or $eng -eq 'cursor-cli') { $eng = 'cursor' }
    if ($eng -eq 'raw' -or $eng -eq 'python' -or $eng -eq 'none' -or $eng -eq 'noai' -or $eng -eq 'ue') { $eng = 'exec' }
    if ($eng -ne 'cursor' -and $eng -ne 'claude' -and $eng -ne 'exec') {
        Write-Live ("Bilinmeyen MJ_ENGINE='" + $eng + "', cursor kullanilacak.") 'Yellow'
        $eng = 'cursor'
    }
    $script:Engine = $eng
    if ([string]::IsNullOrWhiteSpace($md)) { $script:AgentModel = '' } else { $script:AgentModel = $md.Trim() }
    $script:ClaudeExe      = Resolve-ClaudeExe $ce
    $script:CursorExe      = Resolve-CursorExe $cu
    $script:UseContinue    = $true
    $script:LastInSeq      = 0
    $script:LastOutSeq     = 0
    $script:TelegraphToken = $null
    if ($cfg -ne $null -and $cfg.LastInSeq) { $script:LastInSeq = [int]$cfg.LastInSeq }
    if ($cfg -ne $null -and $cfg.LastOutSeq) { $script:LastOutSeq = [int]$cfg.LastOutSeq }
    if ($cfg -ne $null -and $cfg.TelegraphToken) { $script:TelegraphToken = [string]$cfg.TelegraphToken }
}

function Ensure-WorkDir {
    if (-not (Test-Path -LiteralPath $script:WorkDir)) {
        New-Item -ItemType Directory -Path $script:WorkDir -Force | Out-Null
        Write-Live ("Klasor olusturuldu: " + $script:WorkDir) 'DarkGray'
    }
}

function Get-Utf8Bytes([string]$Text) {
    return [System.Text.Encoding]::UTF8.GetBytes($Text)
}

function Get-Utf8String([byte[]]$Bytes) {
    return [System.Text.Encoding]::UTF8.GetString($Bytes)
}

function Concat-Bytes([byte[]]$A, [byte[]]$B) {
    $out = New-Object byte[] ($A.Length + $B.Length)
    [Array]::Copy($A, 0, $out, 0, $A.Length)
    [Array]::Copy($B, 0, $out, $A.Length, $B.Length)
    return $out
}

function Get-Sha256([byte[]]$Data) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return $sha.ComputeHash($Data) } finally { $sha.Dispose() }
}

function Get-MJKeys {
    $raw = Get-Utf8Bytes $script:Secret
    $encPrefix = Get-Utf8Bytes 'megajam-bridge-v3-enc|'
    $macPrefix = Get-Utf8Bytes 'megajam-bridge-v3-mac|'
    $script:EncKey = Get-Sha256 (Concat-Bytes $encPrefix $raw)
    $script:MacKey = Get-Sha256 (Concat-Bytes $macPrefix $raw)
}

function ConvertTo-UrlSafeBase64([byte[]]$Bytes) {
    $s = [Convert]::ToBase64String($Bytes)
    return ($s.Replace('+', '-').Replace('/', '_'))
}

function ConvertFrom-UrlSafeBase64([string]$Text) {
    $s = $Text.Trim().Replace('-', '+').Replace('_', '/')
    $s = $s -replace '\s', ''
    $pad = (4 - ($s.Length % 4)) % 4
    if ($pad -gt 0) { $s = $s + ('=' * $pad) }
    return [Convert]::FromBase64String($s)
}

function Protect-MJText([int]$Seq, [string]$Text) {
    $plain = Get-Utf8Bytes (($Seq.ToString() + "`n" + $Text))
    $iv = New-Object byte[] 16
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($iv) } finally { $rng.Dispose() }

    $aes = [System.Security.Cryptography.Aes]::Create()
    try {
        $aes.Mode = [System.Security.Cryptography.CipherMode]::CBC
        $aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7
        $aes.KeySize = 256
        $aes.Key = $script:EncKey
        $aes.IV = $iv
        $enc = $aes.CreateEncryptor()
        try {
            $cipher = $enc.TransformFinalBlock($plain, 0, $plain.Length)
        } finally { $enc.Dispose() }
    } finally { $aes.Dispose() }

    $magic = [byte[]](0x4D, 0x4A, 0x33, 0x01)  # MJ3\x01
    $body = Concat-Bytes (Concat-Bytes $magic $iv) $cipher
    $hmac = New-Object System.Security.Cryptography.HMACSHA256 (,$script:MacKey)
    try { $tag = $hmac.ComputeHash($body) } finally { $hmac.Dispose() }
    return (ConvertTo-UrlSafeBase64 (Concat-Bytes $body $tag))
}

function Unprotect-MJText([string]$Blob) {
    $raw = ConvertFrom-UrlSafeBase64 $Blob
    if ($raw.Length -lt 52) { throw 'blob too short' }
    $bodyLen = $raw.Length - 32
    $body = New-Object byte[] $bodyLen
    $tag = New-Object byte[] 32
    [Array]::Copy($raw, 0, $body, 0, $bodyLen)
    [Array]::Copy($raw, $bodyLen, $tag, 0, 32)
    if ($body[0] -ne 0x4D -or $body[1] -ne 0x4A -or $body[2] -ne 0x33 -or $body[3] -ne 0x01) {
        throw 'bad magic'
    }
    $hmac = New-Object System.Security.Cryptography.HMACSHA256 (,$script:MacKey)
    try { $expect = $hmac.ComputeHash($body) } finally { $hmac.Dispose() }
    $ok = $true
    if ($expect.Length -ne $tag.Length) { $ok = $false }
    else {
        $diff = 0
        for ($i = 0; $i -lt $tag.Length; $i++) { $diff = $diff -bor ($expect[$i] -bxor $tag[$i]) }
        if ($diff -ne 0) { $ok = $false }
    }
    if (-not $ok) { throw 'bad mac' }
    $iv = New-Object byte[] 16
    $cipher = New-Object byte[] ($body.Length - 20)
    [Array]::Copy($body, 4, $iv, 0, 16)
    [Array]::Copy($body, 20, $cipher, 0, $cipher.Length)
    $aes = [System.Security.Cryptography.Aes]::Create()
    try {
        $aes.Mode = [System.Security.Cryptography.CipherMode]::CBC
        $aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7
        $aes.KeySize = 256
        $aes.Key = $script:EncKey
        $aes.IV = $iv
        $dec = $aes.CreateDecryptor()
        try {
            $plain = $dec.TransformFinalBlock($cipher, 0, $cipher.Length)
        } finally { $dec.Dispose() }
    } finally { $aes.Dispose() }
    $text = Get-Utf8String $plain
    $nl = $text.IndexOf("`n")
    if ($nl -lt 0) { throw 'missing seq' }
    $seq = [int]$text.Substring(0, $nl)
    $bodyText = $text.Substring($nl + 1)
    return @{ Seq = $seq; Text = $bodyText }
}

function Invoke-WebUtf8 {
    param(
        [string]$Url,
        [string]$Method = 'GET',
        [string]$ContentType = $null,
        [byte[]]$Body = $null,
        [int]$TimeoutMs = 45000
    )
    $req = [System.Net.HttpWebRequest]::Create($Url)
    $req.Method = $Method
    $req.UserAgent = 'megajam-bridge/3.0'
    $req.Timeout = $TimeoutMs
    $req.ReadWriteTimeout = $TimeoutMs
    try { $req.ServicePoint.Expect100Continue = $false } catch {}
    try {
        $req.AutomaticDecompression = [System.Net.DecompressionMethods]::GZip -bor [System.Net.DecompressionMethods]::Deflate
    } catch {}
    if (-not [string]::IsNullOrWhiteSpace($ContentType)) { $req.ContentType = $ContentType }
    if ($Body -ne $null) {
        $req.ContentLength = $Body.Length
        $s = $req.GetRequestStream()
        $s.Write($Body, 0, $Body.Length)
        $s.Close()
    }
    $resp = $null
    try {
        $resp = $req.GetResponse()
        $reader = New-Object System.IO.StreamReader($resp.GetResponseStream(), [System.Text.Encoding]::UTF8)
        $text = $reader.ReadToEnd()
        $reader.Close()
        return $text
    } catch [System.Net.WebException] {
        $ex = $_.Exception
        $err = $ex.Message
        try {
            if ($ex.Response) {
                $er = New-Object System.IO.StreamReader($ex.Response.GetResponseStream(), [System.Text.Encoding]::UTF8)
                $err = $err + ' ' + $er.ReadToEnd()
                $er.Close()
            }
        } catch {}
        throw (Hide-Secret $err)
    } finally {
        if ($resp -ne $null) { $resp.Close() }
    }
}

function Invoke-Telegram([string]$Method, [hashtable]$Fields) {
    $parts = New-Object System.Collections.Generic.List[string]
    foreach ($k in $Fields.Keys) {
        $v = [string]$Fields[$k]
        $esc = $v.Replace('\', '\\').Replace('"', '\"').Replace("`r", '\r').Replace("`n", '\n').Replace("`t", '\t')
        [void]$parts.Add(('"' + $k + '":"' + $esc + '"'))
    }
    $json = '{' + [string]::Join(',', $parts.ToArray()) + '}'
    $url = 'https://api.telegram.org/bot' + $script:Token + '/' + $Method
    $bytes = Get-Utf8Bytes $json
    $raw = Invoke-WebUtf8 -Url $url -Method 'POST' -ContentType 'application/json; charset=utf-8' -Body $bytes
    $obj = $raw | ConvertFrom-Json
    if (-not $obj.ok) { throw (Hide-Secret ("Telegram " + $Method + " error: " + $raw)) }
    return $obj.result
}

function Get-MJDescription([string]$Lang) {
    $r = Invoke-Telegram 'getMyDescription' @{ language_code = $Lang }
    if ($r -and $r.description) { return [string]$r.description }
    return ''
}

function Set-MJDescription([string]$Lang, [string]$Text) {
    if ($Text.Length -gt 512) { throw ('description too long: ' + $Text.Length) }
    $null = Invoke-Telegram 'setMyDescription' @{ language_code = $Lang; description = $Text }
}

function ConvertTo-FormBody([hashtable]$Fields) {
    $parts = New-Object System.Collections.Generic.List[string]
    foreach ($k in $Fields.Keys) {
        $v = [Uri]::EscapeDataString([string]$Fields[$k])
        [void]$parts.Add(($k + '=' + $v))
    }
    return [string]::Join('&', $parts.ToArray())
}

function Get-TelegraphText($content) {
    $sb = New-Object System.Text.StringBuilder
    function Walk($n) {
        if ($n -eq $null) { return }
        if ($n -is [string]) { [void]$sb.Append($n); return }
        $isList = $false
        if ($n -is [System.Array]) { $isList = $true }
        elseif ($n -is [System.Collections.IList]) { $isList = $true }
        if ($isList) {
            foreach ($i in @($n)) { Walk $i }
            return
        }
        try {
            if ($n.PSObject -and $n.PSObject.Properties['children']) {
                Walk $n.children
            }
        } catch {}
    }
    Walk $content
    return $sb.ToString()
}

function Ensure-TelegraphToken {
    if (-not [string]::IsNullOrWhiteSpace($script:TelegraphToken)) { return }
    $form = ConvertTo-FormBody @{ short_name = 'mjbridge'; author_name = 'mj' }
    $raw = Invoke-WebUtf8 -Url 'https://api.telegra.ph/createAccount' -Method 'POST' -ContentType 'application/x-www-form-urlencoded' -Body (Get-Utf8Bytes $form)
    $obj = $raw | ConvertFrom-Json
    if (-not $obj.ok) { throw ('Telegraph createAccount failed: ' + $raw) }
    $script:TelegraphToken = [string]$obj.result.access_token
    Save-LocalConfig
}

function Publish-Telegraph([string]$Blob) {
    Ensure-TelegraphToken
    $chunkSize = 45000
    $paths = New-Object System.Collections.Generic.List[string]
    $idx = 0
    $nonce = [Guid]::NewGuid().ToString('N').Substring(0, 10)
    while ($idx -lt $Blob.Length) {
        $take = [Math]::Min($chunkSize, $Blob.Length - $idx)
        $part = $Blob.Substring($idx, $take)
        $idx = $idx + $take
        $nodes = New-Object System.Collections.Generic.List[string]
        $p = 0
        while ($p -lt $part.Length) {
            $n = [Math]::Min(700, $part.Length - $p)
            $piece = $part.Substring($p, $n)
            $esc = $piece.Replace('\', '\\').Replace('"', '\"')
            [void]$nodes.Add(('{"tag":"p","children":["' + $esc + '"]}'))
            $p = $p + $n
        }
        $content = '[' + [string]::Join(',', $nodes.ToArray()) + ']'
        $form = ConvertTo-FormBody @{
            access_token = $script:TelegraphToken
            title = ('m' + $nonce + $paths.Count)
            content = $content
            return_content = 'false'
        }
        $raw = Invoke-WebUtf8 -Url 'https://api.telegra.ph/createPage' -Method 'POST' -ContentType 'application/x-www-form-urlencoded' -Body (Get-Utf8Bytes $form) -TimeoutMs 60000
        $obj = $raw | ConvertFrom-Json
        if (-not $obj.ok) { throw ('Telegraph createPage failed: ' + $raw) }
        [void]$paths.Add([string]$obj.result.path)
    }
    return [string]::Join(',', $paths.ToArray())
}

function Read-Telegraph([string]$Ref) {
    $parts = $Ref.Split(',')
    $sb = New-Object System.Text.StringBuilder
    foreach ($path in $parts) {
        $p = $path.Trim()
        if ([string]::IsNullOrWhiteSpace($p)) { continue }
        $url = 'https://api.telegra.ph/getPage/' + [Uri]::EscapeDataString($p) + '?return_content=true'
        $raw = Invoke-WebUtf8 -Url $url -Method 'GET' -TimeoutMs 60000
        $obj = $raw | ConvertFrom-Json
        if (-not $obj.ok) { throw ('Telegraph getPage failed: ' + $raw) }
        [void]$sb.Append((Get-TelegraphText $obj.result.content))
    }
    return $sb.ToString()
}

function Parse-Manifest([string]$Text) {
    $list = New-Object System.Collections.Generic.List[object]
    if ([string]::IsNullOrWhiteSpace($Text)) { return @() }
    $t = $Text -replace "`r`n", "`n"
    $t = $t -replace "`r", "`n"
    $t = $t.Trim()
    if (-not $t.StartsWith('MJ3')) { return @() }
    $lines = $t.Split("`n")
    if ($lines.Length -eq 1) {
        $parts = $lines[0].Trim() -split '\s+', 3
        if ($parts.Length -eq 3 -and $parts[0] -eq 'MJ3') {
            $seq32 = 0
            if ([int]::TryParse($parts[1], [ref]$seq32)) {
                [void]$list.Add((New-Object psobject -Property @{ Seq = $seq32; Ref = $parts[2] }))
            }
        }
        return $list.ToArray()
    }
    for ($i = 1; $i -lt $lines.Length; $i++) {
        $line = $lines[$i].Trim()
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $sp = $line.IndexOf(' ')
        if ($sp -lt 1) { continue }
        $seq32 = 0
        if (-not [int]::TryParse($line.Substring(0, $sp), [ref]$seq32)) { continue }
        $ref = $line.Substring($sp + 1).Trim()
        if ([string]::IsNullOrWhiteSpace($ref)) { continue }
        [void]$list.Add((New-Object psobject -Property @{ Seq = $seq32; Ref = $ref }))
    }
    return $list.ToArray()
}

function Format-Manifest($Entries) {
    if ($Entries -eq $null) { return '' }
    $arr = @($Entries | Sort-Object Seq)
    if ($arr.Count -eq 0) { return '' }
    if ($arr.Count -gt 8) { $arr = $arr[($arr.Count - 8)..($arr.Count - 1)] }
    while ($arr.Count -gt 0) {
        $lines = New-Object System.Collections.Generic.List[string]
        [void]$lines.Add('MJ3')
        foreach ($e in $arr) { [void]$lines.Add(([string]$e.Seq + ' ' + $e.Ref)) }
        $text = [string]::Join("`n", $lines.ToArray())
        if ($text.Length -le 512) { return $text }
        if ($arr.Count -eq 1) { throw 'manifest entry does not fit in 512 characters' }
        $arr = $arr[1..($arr.Count - 1)]
    }
    return ''
}

function New-PayloadRef([int]$Seq, [string]$Text) {
    $blob = Protect-MJText $Seq $Text
    if ($blob.Length -le 180) { return ('i:' + $blob) }
    return (Publish-Telegraph $blob)
}

function Read-PayloadRef([string]$Ref) {
    $blob = $null
    if ($Ref.StartsWith('i:')) {
        $blob = $Ref.Substring(2)
    } elseif ($Ref.StartsWith('http://') -or $Ref.StartsWith('https://')) {
        $blob = Invoke-WebUtf8 -Url $Ref -Method 'GET' -TimeoutMs 60000
    } else {
        $blob = Read-Telegraph $Ref
    }
    return (Unprotect-MJText $blob)
}

function Send-Outbound([string]$Text) {
    try {
        $seq = $script:LastOutSeq + 1
        $ref = New-PayloadRef $seq $Text
        $current = @(Parse-Manifest (Get-MJDescription $script:OutLang))
        $kept = New-Object System.Collections.Generic.List[object]
        foreach ($e in $current) {
            if ($e.Seq -lt $seq) { [void]$kept.Add($e) }
        }
        [void]$kept.Add((New-Object psobject -Property @{ Seq = $seq; Ref = $ref }))
        Set-MJDescription $script:OutLang (Format-Manifest $kept)
        $script:LastOutSeq = $seq
        Save-LocalConfig
    } catch {
        Write-Live ("Yanit gonderilemedi: " + (Hide-Secret $_.Exception.Message)) 'Yellow'
    }
}

function Get-InboundNew {
    $desc = Get-MJDescription $script:InLang
    $entries = @(Parse-Manifest $desc)
    $entries = @($entries | Sort-Object Seq)
    $out = New-Object System.Collections.Generic.List[object]
    foreach ($e in $entries) {
        if ($e.Seq -le $script:LastInSeq) { continue }
        try {
            $got = Read-PayloadRef $e.Ref
            if ([int]$got.Seq -ne [int]$e.Seq) { throw ('seq mismatch pointer=' + $e.Seq + ' blob=' + $got.Seq) }
            [void]$out.Add((New-Object psobject -Property @{ Seq = [int]$e.Seq; Text = [string]$got.Text }))
        } catch {
            Write-Live ("Gelen paket okunamadi (seq " + $e.Seq + "): " + (Hide-Secret $_.Exception.Message)) 'Yellow'
        }
    }
    return $out.ToArray()
}

function Get-MJEngineLabel {
    if ($script:Engine -eq 'exec') { return 'Exec' }
    if ($script:Engine -eq 'cursor') { return 'Cursor' }
    return 'Claude'
}

function Get-MJEngineExe {
    if ($script:Engine -eq 'exec') {
        $pyExe = Resolve-MJPython
        if ([string]::IsNullOrWhiteSpace($pyExe)) { return '(python bulunamadi - Unreal Editor acilinca tekrar aranir)' }
        return $pyExe
    }
    if ($script:Engine -eq 'cursor') { return $script:CursorExe }
    return $script:ClaudeExe
}

function New-MJClaudeArgs([bool]$ContinueSession) {
    $argList = New-Object System.Collections.Generic.List[string]
    [void]$argList.Add('--print')
    if ($ContinueSession) { [void]$argList.Add('--continue') }
    [void]$argList.Add('--output-format')
    [void]$argList.Add('text')
    [void]$argList.Add('--permission-mode')
    [void]$argList.Add($script:PermissionMode)
    return ,$argList
}

function New-MJCursorArgs([bool]$ContinueSession) {
    # Official Cursor CLI equivalents of claude --print --continue:
    #   --print / -p, --continue (alias of --resume=-1), --output-format text
    # Auto-approve: --force (alias --yolo) plus --trust so headless mode
    # does not stop on the workspace trust dialog. --approve-mcps and
    # --sandbox disabled avoid hangs on MCP prompts or a command sandbox
    # when PermissionMode is bypassPermissions.
    $argList = New-Object System.Collections.Generic.List[string]
    [void]$argList.Add('--print')
    if ($ContinueSession) { [void]$argList.Add('--continue') }
    [void]$argList.Add('--output-format')
    [void]$argList.Add('text')
    if (Test-MJAutoApprove) {
        [void]$argList.Add('--force')
        [void]$argList.Add('--trust')
        [void]$argList.Add('--approve-mcps')
        [void]$argList.Add('--sandbox')
        [void]$argList.Add('disabled')
    } else {
        [void]$argList.Add('--trust')
    }
    if (-not [string]::IsNullOrWhiteSpace($script:AgentModel)) {
        [void]$argList.Add('--model')
        [void]$argList.Add($script:AgentModel)
    }
    return ,$argList
}

function Invoke-MJCli([string]$Prompt) {
    $label = Get-MJEngineLabel
    $exe = Get-MJEngineExe
    if ([string]::IsNullOrWhiteSpace($exe) -or -not (Test-Path -LiteralPath $exe)) {
        return ('HATA: ' + $label + ' bulunamadi: ' + $exe)
    }

    $attemptContinue = $script:UseContinue
    $try = 0
    while ($try -lt 2) {
        $try = $try + 1
        if ($script:Engine -eq 'cursor') {
            $argList = New-MJCursorArgs $attemptContinue
        } else {
            $argList = New-MJClaudeArgs $attemptContinue
        }

        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $ext = ''
        try { $ext = [System.IO.Path]::GetExtension($exe) } catch {}
        if ($ext -match '(?i)^\.(cmd|bat)$') {
            $psi.FileName = $env:ComSpec
            $psi.Arguments = '/d /c "' + $exe + '" ' + (@($argList) -join ' ')
        } else {
            $psi.FileName = $exe
            $psi.Arguments = (@($argList) -join ' ')
        }
        $psi.WorkingDirectory = $script:WorkDir
        $psi.UseShellExecute = $false
        $psi.RedirectStandardInput = $true
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true
        $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
        $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8
        try { $psi.EnvironmentVariables['NO_COLOR'] = '1' } catch {}
        try { $psi.EnvironmentVariables['TERM'] = 'dumb' } catch {}

        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $psi
        [void]$p.Start()
        $tOut = $p.StandardOutput.ReadToEndAsync()
        $tErr = $p.StandardError.ReadToEndAsync()
        $promptBytes = [System.Text.Encoding]::UTF8.GetBytes($Prompt)
        $p.StandardInput.BaseStream.Write($promptBytes, 0, $promptBytes.Length)
        $p.StandardInput.BaseStream.Flush()
        $p.StandardInput.Close()

        $timeoutMs = $script:TimeoutSec * 1000
        if (-not $p.WaitForExit($timeoutMs)) {
            try { $p.Kill() } catch {}
            try {
                Start-Process -FilePath 'taskkill.exe' -ArgumentList @('/PID', [string]$p.Id, '/T', '/F') -WindowStyle Hidden -Wait -ErrorAction SilentlyContinue | Out-Null
            } catch {}
            return ('HATA: ' + $label + ' ' + $script:TimeoutSec + ' saniye icinde bitmedi, islem durduruldu.')
        }
        try { [void]$tOut.Wait(15000) } catch {}
        try { [void]$tErr.Wait(15000) } catch {}
        $stdout = ''
        $stderr = ''
        try { $stdout = [string]$tOut.Result } catch {}
        try { $stderr = [string]$tErr.Result } catch {}
        $code = $p.ExitCode

        $looksLikeNoSession = $false
        if ($attemptContinue -and $code -ne 0) {
            $combined = ($stdout + ' ' + $stderr)
            if ($combined -match '(?i)no (conversation|session|chat)|nothing to (continue|resume)|cannot continue|unable to (continue|resume)|chat not found|unknown chat') {
                $looksLikeNoSession = $true
            }
        }
        if ($looksLikeNoSession) {
            Write-Live 'Onceki sohbet yok, yeni oturum aciliyor...' 'DarkGray'
            $attemptContinue = $false
            $script:UseContinue = $false
            continue
        }

        if ($code -eq 0) { $script:UseContinue = $true }

        $out = $stdout.Trim()
        if ([string]::IsNullOrWhiteSpace($out)) {
            if (-not [string]::IsNullOrWhiteSpace($stderr)) {
                $out = $stderr.Trim()
            } else {
                $out = ('(' + $label + ' bos yanit verdi, cikis kodu ' + $code + ')')
            }
        } elseif (-not [string]::IsNullOrWhiteSpace($stderr) -and $code -ne 0) {
            $errTrim = $stderr.Trim()
            if ($errTrim.Length -gt 4000) { $errTrim = $errTrim.Substring(0, 4000) + '...' }
            $out = $out + "`n`n--- stderr (cikis " + $code + ") ---`n" + $errTrim
        }
        return $out
    }
    return ('HATA: ' + $label + ' calistirilamadi.')
}


# ---------------------------------------------------------------------------
# Exec mode: run UE Python in the open Unreal Editor without any AI agent.
# The runner below is a stdlib-only Python Remote Execution client
# (UDP 239.0.0.1:6766 discovery, TCP command channel on 127.0.0.1).
# ---------------------------------------------------------------------------
$script:MJRunnerSource = @'
# MegaJam bridge: run a Python file inside the open Unreal Editor via
# Python Remote Execution (UDP multicast discovery + TCP command channel).
# Stdlib only, so it runs with the engine's bundled python.exe.
# Usage: python mj_ue_exec.py <code_file> [timeout_sec] [project_hint]
import json, os, socket, sys, time, uuid

GROUP = ('239.0.0.1', 6766)
MAGIC = 'ue_py'
VERSION = 1

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


def mk(kind, src, dest=None, data=None):
    m = {'version': VERSION, 'magic': MAGIC, 'type': kind, 'source': src}
    if dest:
        m['dest'] = dest
    if data is not None:
        m['data'] = data
    return json.dumps(m, ensure_ascii=False).encode('utf-8')


def parse(raw):
    try:
        m = json.loads(raw.decode('utf-8'))
    except Exception:
        return None
    if not isinstance(m, dict) or m.get('magic') != MAGIC:
        return None
    return m


def open_udp(bind_addr):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    if hasattr(socket, 'SO_REUSEPORT'):
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    else:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((bind_addr, GROUP[1]))
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 0)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                 socket.inet_aton(GROUP[0]) + socket.inet_aton(bind_addr))
    s.settimeout(0.2)
    return s


def discover(udp, me, seconds):
    nodes = {}
    end = time.time() + seconds
    next_ping = 0.0
    while time.time() < end:
        if time.time() >= next_ping:
            udp.sendto(mk('ping', me), GROUP)
            next_ping = time.time() + 1.0
        try:
            raw, _ = udp.recvfrom(65536)
        except socket.timeout:
            continue
        except OSError:
            continue
        m = parse(raw)
        if not m or m.get('source') == me or m.get('type') != 'pong':
            continue
        nodes[m['source']] = m.get('data') or {}
        # small grace period to collect other editors, then stop
        end = min(end, time.time() + 0.6)
    return nodes


def pick(nodes, hint):
    if not nodes:
        return None, None
    if hint:
        h = hint.lower()
        for nid, d in nodes.items():
            if h in str(d.get('project_name', '')).lower() or h in str(d.get('project_root', '')).lower():
                return nid, d
    nid = sorted(nodes.keys())[0]
    return nid, nodes[nid]


def recv_json(conn, timeout):
    conn.settimeout(timeout)
    buf = b''
    while True:
        chunk = conn.recv(1 << 20)
        if not chunk:
            break
        buf += chunk
        m = parse(buf)
        if m is not None:
            return m
    return parse(buf)


def main():
    if len(sys.argv) < 2:
        print('usage: mj_ue_exec.py <code_file> [timeout_sec] [project_hint]')
        return 64
    path = sys.argv[1]
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 600.0
    hint = sys.argv[3] if len(sys.argv) > 3 else 'DirectorsCut'
    with open(path, 'rb') as f:
        code = f.read().decode('utf-8-sig')

    me = str(uuid.uuid4())
    binds = [os.environ.get('MJ_UE_BIND') or '0.0.0.0']
    if '127.0.0.1' not in binds:
        binds.append('127.0.0.1')

    udp = None
    nodes = {}
    for b in binds:
        try:
            udp = open_udp(b)
        except OSError as e:
            print('[UE] multicast bind %s failed: %s' % (b, e))
            udp = None
            continue
        nodes = discover(udp, me, 4.0)
        if nodes:
            break
        udp.close()
        udp = None
    if not nodes:
        print('[UE] HATA: Unreal Editor bulunamadi. Editor acik mi, Python Remote Execution acik mi?')
        return 3

    nid, info = pick(nodes, hint)
    print('[UE] editor: %s | %s | %s' % (info.get('project_name', '?'), info.get('engine_version', '?'), info.get('machine', '?')))

    lst = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lst.bind(('127.0.0.1', 0))
    lst.listen(1)
    lst.settimeout(1.0)
    port = lst.getsockname()[1]
    conn = None
    end = time.time() + 8.0
    while conn is None and time.time() < end:
        udp.sendto(mk('open_connection', me, nid, {'command_ip': '127.0.0.1', 'command_port': port}), GROUP)
        try:
            conn, _ = lst.accept()
        except socket.timeout:
            conn = None
    if conn is None:
        print('[UE] HATA: editor komut baglantisini acmadi.')
        udp.close()
        return 4

    rc = 0
    try:
        conn.settimeout(30)
        conn.sendall(mk('command', me, nid, {'command': code, 'unattended': True, 'exec_mode': 'ExecuteFile'}))
        res = recv_json(conn, timeout)
        if not res:
            print('[UE] HATA: bos yanit')
            rc = 5
        else:
            d = res.get('data') or {}
            for o in d.get('output') or []:
                kind = o.get('type', 'Info')
                text = str(o.get('output', '')).rstrip('\n')
                print(text if kind == 'Info' else '[%s] %s' % (kind, text))
            ok = bool(d.get('success'))
            result = d.get('result')
            if result not in (None, '', 'None'):
                print('[UE] result: %s' % result)
            print('[UE] success=%s' % ok)
            rc = 0 if ok else 2
    except socket.timeout:
        print('[UE] HATA: %s sn icinde yanit gelmedi (editor hala calisiyor olabilir).' % int(timeout))
        rc = 6
    finally:
        try:
            udp.sendto(mk('close_connection', me, nid), GROUP)
        except Exception:
            pass
        for s in (conn, lst, udp):
            try:
                s.close()
            except Exception:
                pass
    return rc


if __name__ == '__main__':
    sys.exit(main())

'@

$script:MJPyUrlPrefixes = @(
    'https://raw.githubusercontent.com/Erdocool/',
    'https://github.com/Erdocool/',
    'https://gist.githubusercontent.com/Erdocool/'
)

function Get-MJExecDir {
    $d = Join-Path (Get-ConfigDir) 'exec'
    if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
    return $d
}

function Ensure-MJRunner {
    $dir = Get-ConfigDir
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $path = Join-Path $dir 'mj_ue_exec.py'
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($path, $script:MJRunnerSource, $utf8)
    return $path
}

function Get-MJEnginePython([string]$EngineDir) {
    if ([string]::IsNullOrWhiteSpace($EngineDir)) { return $null }
    $c = Join-Path $EngineDir 'Binaries\ThirdParty\Python3\Win64\python.exe'
    if (Test-Path -LiteralPath $c) { return $c }
    $c = Join-Path $EngineDir 'Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
    if (Test-Path -LiteralPath $c) { return $c }
    return $null
}

function Resolve-MJPython {
    if (-not [string]::IsNullOrWhiteSpace($script:PythonOverride) -and (Test-Path -LiteralPath $script:PythonOverride)) {
        return $script:PythonOverride
    }
    # 1) The python.exe bundled with the running Unreal Editor
    try {
        $procs = @(Get-Process -Name 'UnrealEditor' -ErrorAction SilentlyContinue)
        foreach ($pr in $procs) {
            $exePath = $null
            try { $exePath = $pr.Path } catch {}
            if ([string]::IsNullOrWhiteSpace($exePath)) { continue }
            $engDir = Split-Path (Split-Path (Split-Path $exePath -Parent) -Parent) -Parent
            $c = Get-MJEnginePython $engDir
            if ($c) { return $c }
        }
    } catch {}
    # 2) Installed engines from the registry (newest first)
    try {
        $keys = @(Get-ChildItem 'HKLM:\SOFTWARE\EpicGames\Unreal Engine' -ErrorAction SilentlyContinue | Sort-Object PSChildName -Descending)
        foreach ($k in $keys) {
            $inst = $null
            try { $inst = (Get-ItemProperty -LiteralPath $k.PSPath -ErrorAction SilentlyContinue).InstalledDirectory } catch {}
            if ([string]::IsNullOrWhiteSpace($inst)) { continue }
            $c = Get-MJEnginePython (Join-Path $inst 'Engine')
            if ($c) { return $c }
        }
    } catch {}
    # 3) Default Epic Games locations
    foreach ($v in @('UE_5.8', 'UE_5.7', 'UE_5.6', 'UE_5.5')) {
        foreach ($root in @($env:ProgramFiles, 'C:\Program Files', 'D:\Epic Games', 'C:\Epic Games')) {
            if ([string]::IsNullOrWhiteSpace($root)) { continue }
            $base = $root
            if ($root -notmatch '(?i)Epic Games$') { $base = Join-Path $root 'Epic Games' }
            $c = Get-MJEnginePython (Join-Path (Join-Path $base $v) 'Engine')
            if ($c) { return $c }
        }
    }
    # 4) A normal Python on PATH (skip the Microsoft Store stub)
    foreach ($n in @('py.exe', 'python.exe', 'python3.exe')) {
        try {
            $cmd = Get-Command $n -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($cmd -and $cmd.Source -and ($cmd.Source -notmatch '(?i)\\WindowsApps\\')) { return $cmd.Source }
        } catch {}
    }
    return $null
}

function Limit-MJText([string]$Text, [int]$Max) {
    if ([string]::IsNullOrEmpty($Text) -or $Text.Length -le $Max) { return $Text }
    $head = [int]($Max * 0.3)
    $tail = $Max - $head
    return $Text.Substring(0, $head) + "`n...[" + ($Text.Length - $Max) + " karakter kesildi]...`n" + $Text.Substring($Text.Length - $tail)
}

function Invoke-MJUePython([string]$Code, [string]$Source) {
    $pyExe = Resolve-MJPython
    if ([string]::IsNullOrWhiteSpace($pyExe)) {
        return 'HATA: python bulunamadi (Unreal Editor acik mi? Gerekirse $MJ_PYTHON ile python.exe yolunu verin).'
    }
    $runner = Ensure-MJRunner
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
    $codeFile = Join-Path (Get-MJExecDir) ('in_' + $stamp + '.py')
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($codeFile, $Code, $utf8)

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $pyExe
    $pre = ''
    if ([System.IO.Path]::GetFileName($pyExe) -ieq 'py.exe') { $pre = '-3 ' }
    $psi.Arguments = $pre + '-u "' + $runner + '" "' + $codeFile + '" ' + [string]$script:TimeoutSec + ' DirectorsCut'
    $psi.WorkingDirectory = $script:WorkDir
    $psi.UseShellExecute = $false
    $psi.RedirectStandardInput = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8
    try { $psi.EnvironmentVariables['PYTHONIOENCODING'] = 'utf-8' } catch {}
    try { $psi.EnvironmentVariables['PYTHONUTF8'] = '1' } catch {}

    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    [void]$p.Start()
    $tOut = $p.StandardOutput.ReadToEndAsync()
    $tErr = $p.StandardError.ReadToEndAsync()
    $waitMs = ($script:TimeoutSec + 30) * 1000
    if (-not $p.WaitForExit($waitMs)) {
        try { $p.Kill() } catch {}
        return ('HATA: UE python ' + $script:TimeoutSec + ' saniyede bitmedi, istemci durduruldu (editor icindeki is surebilir).')
    }
    try { [void]$tOut.Wait(15000) } catch {}
    try { [void]$tErr.Wait(15000) } catch {}
    $stdout = ''
    $stderr = ''
    try { $stdout = [string]$tOut.Result } catch {}
    try { $stderr = [string]$tErr.Result } catch {}
    $out = ('[exec ' + $Source + ' | cikis ' + $p.ExitCode + ' | ' + [System.IO.Path]::GetFileName($codeFile) + "]`n" + $stdout.TrimEnd())
    if (-not [string]::IsNullOrWhiteSpace($stderr)) {
        $out = $out + "`n--- stderr ---`n" + $stderr.Trim()
    }
    return (Limit-MJText $out 50000)
}

function Test-MJPyUrl([string]$Url) {
    foreach ($pfx in $script:MJPyUrlPrefixes) {
        if ($Url.StartsWith($pfx, [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    return $false
}

# Returns $null when the message is not an exec command, otherwise the reply.
function Try-MJExecCommand([string]$Prompt) {
    $text = $Prompt.Replace("`r`n", "`n").TrimStart()
    $nl = $text.IndexOf("`n")
    if ($nl -ge 0) { $first = $text.Substring(0, $nl).Trim(); $rest = $text.Substring($nl + 1) } else { $first = $text.Trim(); $rest = '' }
    $firstClean = ($first -replace '\s*#\s*$', '').Trim()

    if ($firstClean -match '^(?i)!pyurl\s+(\S+)$') {
        $url = $Matches[1]
        if (-not (Test-MJPyUrl $url)) {
            return ('HATA: !pyurl sadece su adreslerden indirir: ' + ($script:MJPyUrlPrefixes -join ', '))
        }
        try {
            $code = Invoke-WebUtf8 -Url $url -Method 'GET' -TimeoutMs 60000
        } catch {
            return ('HATA: script indirilemedi: ' + (Hide-Secret $_.Exception.Message))
        }
        if ([string]::IsNullOrWhiteSpace($code)) { return 'HATA: indirilen script bos.' }
        return (Invoke-MJUePython $code $url)
    }
    if ($firstClean -match '^(?i)!py$') {
        if ([string]::IsNullOrWhiteSpace($rest)) { return 'HATA: !py satirindan sonra Python kodu yok.' }
        return (Invoke-MJUePython $rest 'inline')
    }
    if ($firstClean -match '^(?i)!py\s+(.+)$') {
        # one-liner: !py print(1)
        $one = ($first -replace '^(?i)!py\s+', '')
        if (-not [string]::IsNullOrWhiteSpace($rest)) { $one = $one + "`n" + $rest }
        return (Invoke-MJUePython $one 'inline')
    }
    return $null
}

function Show-Banner {
    $label = Get-MJEngineLabel
    $exe = Get-MJEngineExe
    Write-Host ''
    Write-Host '========================================' -ForegroundColor Cyan
    Write-Host ('  MegaJam ' + $label + ' koprusu') -ForegroundColor Cyan
    Write-Host '========================================' -ForegroundColor Cyan
    Write-Host ('  Motor  : ' + $script:Engine)
    Write-Host ('  Klasor : ' + $script:WorkDir)
    Write-Host ('  Yazilim: ' + $exe)
    if ($script:Engine -eq 'cursor' -and -not [string]::IsNullOrWhiteSpace($script:AgentModel)) {
        Write-Host ('  Model  : ' + $script:AgentModel)
    }
    Write-Host ('  Izin   : ' + $script:PermissionMode)
    Write-Host '  Transport: Telegram Bot API (anlik, getUpdates yok)'
    if ($script:Engine -eq 'exec') {
        Write-Host '  Exec: yapay zeka YOK. Sadece !py / !pyurl mesajlari'
        Write-Host '        acik Unreal Editor''da Python olarak calisir.'
    } elseif ($script:Engine -eq 'cursor') {
        Write-Host '  Cursor: --print --continue --output-format text'
        if (Test-MJAutoApprove) {
            Write-Host '          --force --trust --approve-mcps --sandbox disabled'
        } else {
            Write-Host '          --trust (dosya yazabilir; kabuk icin --force yok).'
            Write-Host '          Takilirsa $MJ_PERMISSION=''bypassPermissions'' yazin.'
        }
    } else {
        Write-Host '  Izinler: acceptEdits = dosya duzenlemeleri otomatik.'
        Write-Host '           Bash vs. hala onay isteyebilir; takilirsa'
        Write-Host '           config''te PermissionMode = bypassPermissions yapin.'
    }
    if ($script:Engine -ne 'exec' -and -not (Test-Path -LiteralPath $exe)) {
        Write-Host ('  UYARI: ' + $label + ' bulunamadi. Yolu kontrol edin.') -ForegroundColor Yellow
    }
    Write-Host '========================================' -ForegroundColor Cyan
    Write-Host 'Dinleniyor...  Ctrl+C ile cikis' -ForegroundColor Green
    Write-Host ''
}

function Handle-Message([string]$Prompt) {
    $stamp = Get-Date -Format 'HH:mm:ss'
    Write-Host ''
    Write-Host ('----- GROK  [' + $stamp + '] -----') -ForegroundColor Magenta
    Write-Host $Prompt
    Write-Host ''

    if ($Prompt.Trim() -eq '!ping') {
        $reply = 'pong  kopru calisiyor  ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
        Write-Host ('----- KOPRU [' + (Get-Date -Format 'HH:mm:ss') + '] -----') -ForegroundColor Green
        Write-Host $reply
        Send-Outbound $reply
        return
    }

    $execReply = $null
    try {
        $execReply = Try-MJExecCommand $Prompt
    } catch {
        $execReply = 'HATA: exec basarisiz: ' + (Hide-Secret $_.Exception.Message)
    }
    if ($execReply -ne $null) {
        Write-Host ('----- EXEC  [' + (Get-Date -Format 'HH:mm:ss') + '] -----') -ForegroundColor Green
        Write-Host $execReply
        Write-Host ''
        Send-Outbound $execReply
        Write-Host 'Dinleniyor...' -ForegroundColor Green
        return
    }
    if ($script:Engine -eq 'exec') {
        $reply = 'Exec modu: yapay zeka kapali. Komutlar: !ping, "!py" + yeni satirda Python kodu, "!pyurl <github-raw-url>".'
        Write-Host $reply -ForegroundColor Yellow
        Send-Outbound $reply
        Write-Host 'Dinleniyor...' -ForegroundColor Green
        return
    }

    $label = Get-MJEngineLabel
    Write-Host ($label + ' calisiyor...') -ForegroundColor DarkGray
    $reply = Invoke-MJCli $Prompt
    Write-Host ''
    Write-Host ('----- ' + $label.ToUpper() + ' [' + (Get-Date -Format 'HH:mm:ss') + '] -----') -ForegroundColor Cyan
    Write-Host $reply
    Write-Host ''
    Send-Outbound $reply
    Write-Host 'Dinleniyor...' -ForegroundColor Green
}

function Start-ListenLoop {
    Write-Live 'Sadece bundan sonra gelen mesajlar islenecek (oncekiler atlanir, sonraki calistirmada kuyruk alinir).' 'DarkGray'
    while ($true) {
        try {
            $new = @(Get-InboundNew)
            foreach ($m in $new) {
                $script:LastInSeq = [int]$m.Seq
                Save-LocalConfig
                Handle-Message ([string]$m.Text)
            }
        } catch {
            Write-Live ('Baglanti koptu, 3 sn sonra yeniden: ' + (Hide-Secret $_.Exception.Message)) 'DarkGray'
            Start-Sleep -Seconds 3
            continue
        }
        Start-Sleep -Milliseconds ([Math]::Max(400, [int]($script:PollSec * 1000)))
    }
}

function Save-LocalScriptCopy {
    $dir = Get-ConfigDir
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $dest = Join-Path $dir 'bridge.ps1'
    $utf8bom = New-Object System.Text.UTF8Encoding $true
    $saved = $false
    $from = $null

    if (-not [string]::IsNullOrWhiteSpace($script:StartupCommandPath) -and (Test-Path -LiteralPath $script:StartupCommandPath)) {
        if ($script:StartupCommandPath -ne $dest) {
            try {
                Copy-Item -LiteralPath $script:StartupCommandPath -Destination $dest -Force
                $saved = $true
                $from = 'dosya kopyasi'
            } catch {}
        } else {
            $saved = $true
            $from = 'zaten yerel dosya'
        }
    }

    if (-not $saved -and -not [string]::IsNullOrWhiteSpace($script:StartupScriptBlock) -and $script:StartupScriptBlock.Length -gt 500) {
        try {
            [System.IO.File]::WriteAllText($dest, $script:StartupScriptBlock, $utf8bom)
            $saved = $true
            $from = 'script blogu'
        } catch {}
    }

    if (-not $saved -and -not [string]::IsNullOrWhiteSpace($script:StartupDefinition) -and $script:StartupDefinition.Length -gt 500) {
        try {
            [System.IO.File]::WriteAllText($dest, $script:StartupDefinition, $utf8bom)
            $saved = $true
            $from = 'komut tanimi'
        } catch {}
    }

    if (-not $saved) {
        try {
            $raw = Invoke-WebUtf8 -Url $script:RawScriptUrl -Method 'GET' -TimeoutMs 30000
            if (-not [string]::IsNullOrWhiteSpace($raw) -and $raw.Length -gt 500) {
                [System.IO.File]::WriteAllText($dest, $raw, $utf8bom)
                $saved = $true
                $from = 'GitHub'
            }
        } catch {}
    }

    if ($saved) {
        Write-Live ("Yerel kopya kaydedildi (" + $from + "): " + $dest) 'DarkGray'
    } else {
        Write-Live ("Yerel kopya kaydedilemedi. Sonra soyle calistirin: irm " + $script:RawScriptUrl + " | iex") 'Yellow'
    }
}

# --- main ---
Initialize-Tls
Initialize-Utf8Console
Resolve-Config
Get-MJKeys
Ensure-WorkDir
Save-LocalConfig
Save-LocalScriptCopy

# First run (no LastInSeq in a pre-existing config): skip whatever is already in the inbox.
# Subsequent runs keep LastInSeq and catch up anything queued while the window was closed.
$hadPrior = $false
$cfgPrior = Read-LocalConfig
if ($cfgPrior -ne $null -and $cfgPrior.LastInSeq -and ([int]$cfgPrior.LastInSeq -gt 0)) { $hadPrior = $true }
if (-not $hadPrior) {
    try {
        $existing = @(Parse-Manifest (Get-MJDescription $script:InLang))
        $max = 0
        foreach ($e in $existing) { if ($e.Seq -gt $max) { $max = [int]$e.Seq } }
        $script:LastInSeq = $max
        Save-LocalConfig
    } catch {
        Write-Live ('Mevcut gelen kutusu okunamadi: ' + (Hide-Secret $_.Exception.Message)) 'Yellow'
    }
}

Show-Banner
$boot = "Kopru hazir.`nMotor: $($script:Engine)`nKlasor: $($script:WorkDir)`nYazilim: $(Get-MJEngineExe)`nIzin: $($script:PermissionMode)`nTransport: Telegram`nSaat: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Send-Outbound $boot
Start-ListenLoop
