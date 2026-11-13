# MegaJam Claude bridge for Windows PowerShell 5.1+
# Secret-free: pass topics/secret via $MJ_IN, $MJ_OUT, $MJ_SECRET (or a local config).
# Usage (first run):
#   $MJ_IN='...'; $MJ_OUT='...'; $MJ_SECRET='...'; irm <raw-url> | iex
# Later runs (config already saved):
#   irm <raw-url> | iex
# Or run the saved copy:
#   powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.megajam-bridge\bridge.ps1"

$ErrorActionPreference = 'Stop'

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

function Get-UnixNow {
    return [DateTimeOffset]::Now.ToUnixTimeSeconds()
}

function Write-Live([string]$Text, [string]$Color) {
    if ([string]::IsNullOrWhiteSpace($Color)) {
        Write-Host $Text
    } else {
        Write-Host $Text -ForegroundColor $Color
    }
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

function Get-ConfigPath {
    return (Join-Path $env:USERPROFILE (Join-Path '.megajam-bridge' 'config.json'))
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
    $dir = Join-Path $env:USERPROFILE '.megajam-bridge'
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $obj = @{
        InTopic        = $script:InTopic
        OutTopic       = $script:OutTopic
        Secret         = $script:Secret
        WorkDir        = $script:WorkDir
        ClaudeExe      = $script:ClaudeExe
        PermissionMode = $script:PermissionMode
        NtfyBase       = $script:NtfyBase
        TimeoutSec     = $script:TimeoutSec
    }
    $json = $obj | ConvertTo-Json
    $path = Get-ConfigPath
    $utf8bom = New-Object System.Text.UTF8Encoding $true
    [System.IO.File]::WriteAllText($path, $json, $utf8bom)
    Write-Live ("Ayarlar kaydedildi: " + $path) 'DarkGray'
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

function Resolve-Config {
    $cfg = Read-LocalConfig

    $in  = Get-MJVar 'MJ_IN'
    $out = Get-MJVar 'MJ_OUT'
    $sec = Get-MJVar 'MJ_SECRET'
    $wd  = Get-MJVar 'MJ_WORKDIR'
    $ce  = Get-MJVar 'MJ_CLAUDE'
    $pm  = Get-MJVar 'MJ_PERMISSION'
    $nb  = Get-MJVar 'MJ_NTFY'
    $to  = Get-MJVar 'MJ_TIMEOUT'

    if ([string]::IsNullOrWhiteSpace($in)  -and $env:MEGAJAM_NTFY_IN)      { $in  = $env:MEGAJAM_NTFY_IN }
    if ([string]::IsNullOrWhiteSpace($out) -and $env:MEGAJAM_NTFY_OUT)     { $out = $env:MEGAJAM_NTFY_OUT }
    if ([string]::IsNullOrWhiteSpace($sec) -and $env:MEGAJAM_SECRET)       { $sec = $env:MEGAJAM_SECRET }
    if ([string]::IsNullOrWhiteSpace($wd)  -and $env:MEGAJAM_WORKDIR)      { $wd  = $env:MEGAJAM_WORKDIR }
    if ([string]::IsNullOrWhiteSpace($ce)  -and $env:MEGAJAM_CLAUDE)       { $ce  = $env:MEGAJAM_CLAUDE }
    if ([string]::IsNullOrWhiteSpace($pm)  -and $env:MEGAJAM_PERMISSION)   { $pm  = $env:MEGAJAM_PERMISSION }
    if ([string]::IsNullOrWhiteSpace($nb)  -and $env:MEGAJAM_NTFY_BASE)    { $nb  = $env:MEGAJAM_NTFY_BASE }

    if ([string]::IsNullOrWhiteSpace($in)  -and $cfg -ne $null) { $in  = [string]$cfg.InTopic }
    if ([string]::IsNullOrWhiteSpace($out) -and $cfg -ne $null) { $out = [string]$cfg.OutTopic }
    if ([string]::IsNullOrWhiteSpace($sec) -and $cfg -ne $null) { $sec = [string]$cfg.Secret }
    if ([string]::IsNullOrWhiteSpace($wd)  -and $cfg -ne $null -and $cfg.WorkDir)        { $wd  = [string]$cfg.WorkDir }
    if ([string]::IsNullOrWhiteSpace($ce)  -and $cfg -ne $null -and $cfg.ClaudeExe)      { $ce  = [string]$cfg.ClaudeExe }
    if ([string]::IsNullOrWhiteSpace($pm)  -and $cfg -ne $null -and $cfg.PermissionMode) { $pm  = [string]$cfg.PermissionMode }
    if ([string]::IsNullOrWhiteSpace($nb)  -and $cfg -ne $null -and $cfg.NtfyBase)       { $nb  = [string]$cfg.NtfyBase }
    if ([string]::IsNullOrWhiteSpace($to)  -and $cfg -ne $null -and $cfg.TimeoutSec)     { $to  = [string]$cfg.TimeoutSec }

    if ([string]::IsNullOrWhiteSpace($wd)) { $wd = 'C:\MegaJam' }
    if ([string]::IsNullOrWhiteSpace($pm)) { $pm = 'acceptEdits' }
    if ([string]::IsNullOrWhiteSpace($nb)) { $nb = 'https://ntfy.sh' }
    if ([string]::IsNullOrWhiteSpace($to)) { $to = '900' }

    if ([string]::IsNullOrWhiteSpace($in) -or [string]::IsNullOrWhiteSpace($out) -or [string]::IsNullOrWhiteSpace($sec)) {
        Write-Host ''
        Write-Host 'MegaJam Claude koprusu: ntfy konu adi veya gizli anahtar eksik.' -ForegroundColor Red
        Write-Host 'Ilk calistirmada PowerShell''e sunlari yazin (tek satir):' -ForegroundColor Yellow
        Write-Host '  $MJ_IN=''IN_TOPIC''; $MJ_OUT=''OUT_TOPIC''; $MJ_SECRET=''SECRET''; irm <raw-url> | iex'
        Write-Host 'Ayarlar sonra su dosyaya kaydedilir:'
        Write-Host ('  ' + (Get-ConfigPath))
        exit 1
    }

    $script:InTopic        = $in.Trim()
    $script:OutTopic       = $out.Trim()
    $script:Secret         = $sec.Trim()
    $script:WorkDir        = $wd.Trim()
    $script:PermissionMode = $pm.Trim()
    $script:NtfyBase       = $nb.Trim().TrimEnd('/')
    $script:TimeoutSec     = [int]$to
    $script:ClaudeExe      = Resolve-ClaudeExe $ce
    $script:UseContinue    = $true
}

function Ensure-WorkDir {
    if (-not (Test-Path -LiteralPath $script:WorkDir)) {
        New-Item -ItemType Directory -Path $script:WorkDir -Force | Out-Null
        Write-Live ("Klasor olusturuldu: " + $script:WorkDir) 'DarkGray'
    }
}

function Send-NtfyBody {
    param(
        [string]$Topic,
        [byte[]]$Bytes,
        [string]$Filename
    )
    $url = $script:NtfyBase + '/' + $Topic
    $req = [System.Net.HttpWebRequest]::Create($url)
    $req.Method = 'POST'
    $req.UserAgent = 'megajam-bridge/1.0'
    $req.ContentType = 'text/plain; charset=utf-8'
    $req.Timeout = 60000
    $req.ReadWriteTimeout = 60000
    try { $req.ServicePoint.Expect100Continue = $false } catch {}
    $req.Headers.Add('Priority', 'min')
    if (-not [string]::IsNullOrWhiteSpace($Filename)) {
        $req.Headers.Add('Filename', $Filename)
    }
    $req.ContentLength = $Bytes.Length
    $s = $req.GetRequestStream()
    $s.Write($Bytes, 0, $Bytes.Length)
    $s.Close()
    $resp = $null
    try {
        $resp = $req.GetResponse()
        $reader = New-Object System.IO.StreamReader($resp.GetResponseStream(), [System.Text.Encoding]::UTF8)
        $body = $reader.ReadToEnd()
        $reader.Close()
        return $body
    } finally {
        if ($resp -ne $null) { $resp.Close() }
    }
}

function Send-NtfyText([string]$Topic, [string]$Text) {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    if ($bytes.Length -le 3500) {
        return (Send-NtfyBody -Topic $Topic -Bytes $bytes)
    }
    return (Send-NtfyBody -Topic $Topic -Bytes $bytes -Filename 'claude-reply.txt')
}

function Send-Outbound([string]$Text) {
    $wrapped = $script:Secret + "`n" + $Text
    try {
        $null = Send-NtfyText -Topic $script:OutTopic -Text $wrapped
    } catch {
        Write-Live ("Yanit gonderilemedi: " + $_.Exception.Message) 'Yellow'
    }
}

function Get-InboundPrompt([string]$Raw) {
    if ([string]::IsNullOrWhiteSpace($Raw)) { return $null }
    $t = $Raw -replace "`r`n", "`n"
    $t = $t -replace "`r", "`n"
    $prefixNl = $script:Secret + "`n"
    $prefixSp = $script:Secret + ' '
    if ($t.StartsWith($prefixNl)) { return $t.Substring($prefixNl.Length) }
    if ($t.StartsWith($prefixSp)) { return $t.Substring($prefixSp.Length) }
    if ($t -eq $script:Secret) { return '' }
    if ($t.StartsWith('MJ1 ')) {
        $nl = $t.IndexOf("`n")
        $first = $t
        $body = ''
        if ($nl -ge 0) {
            $first = $t.Substring(0, $nl)
            $body = $t.Substring($nl + 1)
        }
        $parts = $first.Split(' ')
        if ($parts.Length -ge 2 -and $parts[1] -eq $script:Secret) { return $body }
    }
    return $null
}

function Get-UrlText([string]$Url) {
    $req = [System.Net.HttpWebRequest]::Create($Url)
    $req.Method = 'GET'
    $req.UserAgent = 'megajam-bridge/1.0'
    $req.Timeout = 60000
    $req.ReadWriteTimeout = 60000
    $resp = $null
    try {
        $resp = $req.GetResponse()
        $reader = New-Object System.IO.StreamReader($resp.GetResponseStream(), [System.Text.Encoding]::UTF8)
        $text = $reader.ReadToEnd()
        $reader.Close()
        return $text
    } finally {
        if ($resp -ne $null) { $resp.Close() }
    }
}

function Invoke-Claude([string]$Prompt) {
    if (-not (Test-Path -LiteralPath $script:ClaudeExe)) {
        return ('HATA: claude.exe bulunamadi: ' + $script:ClaudeExe)
    }

    $attemptContinue = $script:UseContinue
    $try = 0
    while ($try -lt 2) {
        $try = $try + 1
        $argList = New-Object System.Collections.Generic.List[string]
        [void]$argList.Add('--print')
        if ($attemptContinue) { [void]$argList.Add('--continue') }
        [void]$argList.Add('--output-format')
        [void]$argList.Add('text')
        [void]$argList.Add('--permission-mode')
        [void]$argList.Add($script:PermissionMode)

        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $script:ClaudeExe
        $psi.Arguments = [string]::Join(' ', $argList.ToArray())
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
        # PS 5.1 / .NET Framework has no StandardInputEncoding; write UTF-8 bytes.
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
            return ('HATA: Claude ' + $script:TimeoutSec + ' saniye icinde bitmedi, islem durduruldu.')
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
            if ($combined -match '(?i)no (conversation|session)|nothing to (continue|resume)|cannot continue') {
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
                $out = ('(Claude bos yanit verdi, cikis kodu ' + $code + ')')
            }
        } elseif (-not [string]::IsNullOrWhiteSpace($stderr) -and $code -ne 0) {
            $errTrim = $stderr.Trim()
            if ($errTrim.Length -gt 4000) { $errTrim = $errTrim.Substring(0, 4000) + '...' }
            $out = $out + "`n`n--- stderr (cikis " + $code + ") ---`n" + $errTrim
        }
        return $out
    }
    return 'HATA: Claude calistirilamadi.'
}

function Show-Banner {
    Write-Host ''
    Write-Host '========================================' -ForegroundColor Cyan
    Write-Host '  MegaJam Claude koprusu' -ForegroundColor Cyan
    Write-Host '========================================' -ForegroundColor Cyan
    Write-Host ('  Klasor : ' + $script:WorkDir)
    Write-Host ('  Claude : ' + $script:ClaudeExe)
    Write-Host ('  Izin   : ' + $script:PermissionMode)
    Write-Host '  Transport: ntfy.sh (anlik HTTP)'
    Write-Host '  Izinler: acceptEdits = dosya duzenlemeleri otomatik.'
    Write-Host '           Bash vs. hala onay isteyebilir; takilirsa'
    Write-Host '           config''te PermissionMode = bypassPermissions yapin.'
    if (-not (Test-Path -LiteralPath $script:ClaudeExe)) {
        Write-Host '  UYARI: claude.exe bulunamadi. Yolu kontrol edin.' -ForegroundColor Yellow
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

    Write-Host 'Claude calisiyor...' -ForegroundColor DarkGray
    $reply = Invoke-Claude $Prompt
    Write-Host ''
    Write-Host ('----- CLAUDE [' + (Get-Date -Format 'HH:mm:ss') + '] -----') -ForegroundColor Cyan
    Write-Host $reply
    Write-Host ''
    Send-Outbound $reply
    Write-Host 'Dinleniyor...' -ForegroundColor Green
}

function Process-NtfyLine([string]$Line, [ref]$SinceId) {
    if ([string]::IsNullOrWhiteSpace($Line)) { return }
    $ev = $null
    try { $ev = $Line | ConvertFrom-Json } catch { return }
    if ($ev.id) { $SinceId.Value = [string]$ev.id }
    if ($ev.event -ne 'message') { return }

    $body = [string]$ev.message
    if ($ev.attachment -and $ev.attachment.url) {
        try {
            $body = Get-UrlText ([string]$ev.attachment.url)
        } catch {
            Write-Live ('Ek indirilemedi: ' + $_.Exception.Message) 'Yellow'
        }
    }
    $prompt = Get-InboundPrompt $body
    if ($prompt -eq $null) { return }
    Handle-Message $prompt
}

function Start-NtfyLoop {
    $since = [string](Get-UnixNow)
    Write-Live 'Sadece bundan sonra gelen mesajlar islenecek.' 'DarkGray'
    while ($true) {
        $url = $script:NtfyBase + '/' + $script:InTopic + '/json?since=' + $since
        $req = $null
        $resp = $null
        $reader = $null
        try {
            $req = [System.Net.HttpWebRequest]::Create($url)
            $req.Method = 'GET'
            $req.UserAgent = 'megajam-bridge/1.0'
            $req.Timeout = 30000
            $req.ReadWriteTimeout = 180000
            $req.KeepAlive = $true
            try {
                $req.AutomaticDecompression = [System.Net.DecompressionMethods]::GZip -bor [System.Net.DecompressionMethods]::Deflate
            } catch {}
            $resp = $req.GetResponse()
            $reader = New-Object System.IO.StreamReader($resp.GetResponseStream(), [System.Text.Encoding]::UTF8)
            while ($true) {
                $line = $reader.ReadLine()
                if ($line -eq $null) { break }
                Process-NtfyLine $line ([ref]$since)
            }
        } catch {
            Write-Live ('Baglanti koptu, 3 sn sonra yeniden: ' + $_.Exception.Message) 'DarkGray'
        } finally {
            if ($reader -ne $null) { try { $reader.Close() } catch {} }
            if ($resp -ne $null) { try { $resp.Close() } catch {} }
        }
        Start-Sleep -Seconds 3
    }
}

# --- main ---
Initialize-Tls
Initialize-Utf8Console
Resolve-Config
Ensure-WorkDir
Save-LocalConfig

# Keep a local copy so later runs do not need the network.
try {
    $destScript = Join-Path $env:USERPROFILE (Join-Path '.megajam-bridge' 'bridge.ps1')
    if ($PSCommandPath -and (Test-Path -LiteralPath $PSCommandPath)) {
        if ($PSCommandPath -ne $destScript) {
            Copy-Item -LiteralPath $PSCommandPath -Destination $destScript -Force
        }
    } else {
        $def = $MyInvocation.MyCommand.Definition
        if (-not [string]::IsNullOrWhiteSpace($def) -and $def.Length -gt 500) {
            $utf8bom = New-Object System.Text.UTF8Encoding $true
            [System.IO.File]::WriteAllText($destScript, $def, $utf8bom)
        }
    }
} catch {}

Show-Banner
$boot = "Kopru hazir.`nKlasor: $($script:WorkDir)`nClaude: $($script:ClaudeExe)`nIzin: $($script:PermissionMode)`nSaat: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Send-Outbound $boot
Start-NtfyLoop
