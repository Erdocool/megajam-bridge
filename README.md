# MegaJam Claude bridge

A small Windows PowerShell 5.1 script that lets another machine send prompts to [Claude Code](https://docs.claude.com/en/docs/claude-code) on your PC, without Telegram.

The other machine publishes a message to a private [ntfy.sh](https://ntfy.sh) topic. This script listens, runs `claude.exe --print` in your project folder, shows the conversation in the PowerShell window, and posts Claude's reply to a second topic.

**This repository has no secrets.** Topic names and the shared token stay on your PC (and on the machine that sends prompts).

## What you need

- Windows PowerShell 5.1 or later (Windows 10/11 is fine)
- Claude Code CLI already installed and logged in
- Two unguessable ntfy.sh topic names and a shared secret (someone sets these up once and gives you the first-run command)

The script looks for `claude.exe` at `%USERPROFILE%\.local\bin\claude.exe`, then on `PATH`. The default working folder is `C:\MegaJam` (created if it does not exist). You can override both; see below.

## First run (any Windows PC)

Paste the one-line command you were given. It looks like this (values filled in for you):

```powershell
$MJ_IN='IN_TOPIC'; $MJ_OUT='OUT_TOPIC'; $MJ_SECRET='SECRET'; [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12; irm https://raw.githubusercontent.com/Erdocool/megajam-bridge/main/bridge.ps1 | iex
```

The window stays open and prints "Dinleniyor...". Keep it open while you want the bridge to run. Settings are saved to:

`%USERPROFILE%\.megajam-bridge\config.json`

## Later runs

After the first run, either open a new PowerShell window and paste:

```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12; irm https://raw.githubusercontent.com/Erdocool/megajam-bridge/main/bridge.ps1 | iex
```

or run the saved copy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.megajam-bridge\bridge.ps1"
```

The first run also saves a copy of the script to `%USERPROFILE%\.megajam-bridge\bridge.ps1`.

## Optional overrides (set before `irm | iex`)

| Variable | Default | Meaning |
| --- | --- | --- |
| `$MJ_IN` | (required once) | Inbound ntfy topic (prompts) |
| `$MJ_OUT` | (required once) | Outbound ntfy topic (replies) |
| `$MJ_SECRET` | (required once) | Shared secret; messages without it are ignored |
| `$MJ_WORKDIR` | `C:\MegaJam` | Folder where Claude runs |
| `$MJ_CLAUDE` | `%USERPROFILE%\.local\bin\claude.exe` or `PATH` | Full path to `claude.exe` |
| `$MJ_PERMISSION` | `acceptEdits` | Claude `--permission-mode` |
| `$MJ_NTFY` | `https://ntfy.sh` | ntfy base URL |
| `$MJ_TIMEOUT` | `900` | Max seconds for one Claude run |

Environment variables `MEGAJAM_NTFY_IN`, `MEGAJAM_NTFY_OUT`, `MEGAJAM_SECRET`, `MEGAJAM_WORKDIR`, `MEGAJAM_CLAUDE`, `MEGAJAM_PERMISSION`, and `MEGAJAM_NTFY_BASE` work too.

## Claude flags

Each prompt is sent to Claude as:

```text
claude.exe --print --continue --output-format text --permission-mode acceptEdits
```

The prompt is written to stdin (so quotes and Turkish text stay intact). `--continue` keeps the conversation in the working folder. If there is no previous session, the script retries without `--continue`.

`acceptEdits` auto-approves file edits. Other tools (for example Bash) may still wait for approval and look "stuck". If you want fully unattended runs, set `$MJ_PERMISSION='bypassPermissions'` on first run, or edit `PermissionMode` in the local config. That mode can run commands without asking — only use it on a machine you trust.

## Security

- ntfy.sh topics are public to anyone who knows the name. Use long random names.
- The script ignores any message that does not start with your secret.
- Do not commit `%USERPROFILE%\.megajam-bridge\config.json` or paste the one-liner with real secrets into a public issue or gist.
- ntfy.sh free plans cap message size (4 KB body; larger replies go as an attachment) and daily message volume. Attachments expire in about 3 hours; the live window on the PC still shows the full reply.

## License

You may use and change this script for your own machines.
