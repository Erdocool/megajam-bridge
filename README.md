# MegaJam Claude bridge

A small Windows PowerShell 5.1 script that lets another machine send prompts to [Claude Code](https://docs.claude.com/en/docs/claude-code) on your PC.

The other machine publishes an encrypted prompt through the [Telegram Bot API](https://core.telegram.org/bots/api). This script polls a private slot on that bot (it does **not** call `getUpdates`, so it will not fight with other uses of the same bot), runs `claude.exe --print` in your project folder, shows the conversation in the PowerShell window, and publishes Claude's reply the same way.

Short messages travel in the slot itself. Longer ones are stored as encrypted pages on [telegra.ph](https://telegra.ph); only a path is written to the slot. The public repo and those pages never contain the bot token, the shared secret, or plaintext prompts.

**This repository has no secrets.** The bot token and the shared secret stay on your PC (and on the machine that sends prompts).

## What you need

- Windows PowerShell 5.1 or later (Windows 10/11 is fine)
- Claude Code CLI already installed and logged in
- Outbound HTTPS to `api.telegram.org` and `api.telegra.ph`
- A Telegram bot token and a shared secret (someone sets these up once and gives you the first-run command)

The script looks for `claude.exe` at `%USERPROFILE%\.local\bin\claude.exe`, then on `PATH`. The default working folder is `C:\MegaJam` (created if it does not exist). You can override both; see below.

## First run (any Windows PC)

Paste the one-line command you were given. It looks like this (values filled in for you):

```powershell
$MJ_TOKEN='BOT_TOKEN'; $MJ_SECRET='SECRET'; $MJ_PERMISSION='bypassPermissions'; [Net.ServicePointManager]::SecurityProtocol='Tls12'; iex (irm https://raw.githubusercontent.com/Erdocool/megajam-bridge/main/bridge.ps1)
```

The window stays open and prints "Dinleniyor...". Keep it open while you want the bridge to run. Settings, including the token, are saved to:

`%USERPROFILE%\.megajam-bridge\config.json`

The first run also saves a copy of the script to `%USERPROFILE%\.megajam-bridge\bridge.ps1`. If that copy was missing on an earlier run, use the `irm | iex` line above rather than `-File`.

Do not run this on two PCs at the same time; they share one mailbox.

## Later runs

After the first run, either open a new PowerShell window and paste:

```powershell
[Net.ServicePointManager]::SecurityProtocol='Tls12'; iex (irm https://raw.githubusercontent.com/Erdocool/megajam-bridge/main/bridge.ps1)
```

or run the saved copy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.megajam-bridge\bridge.ps1"
```

## Optional overrides (set before `irm | iex`)

| Variable | Default | Meaning |
| --- | --- | --- |
| `$MJ_TOKEN` | (required once) | Telegram bot token |
| `$MJ_SECRET` | (required once) | Shared secret; messages that do not decrypt are ignored |
| `$MJ_PERMISSION` | `acceptEdits` | Claude `--permission-mode` |
| `$MJ_WORKDIR` | `C:\MegaJam` | Folder where Claude runs |
| `$MJ_CLAUDE` | `%USERPROFILE%\.local\bin\claude.exe` or `PATH` | Full path to `claude.exe` |
| `$MJ_TIMEOUT` | `900` | Max seconds for one Claude run |
| `$MJ_POLL` | `1` | Seconds between inbox checks |
| `$MJ_IN_LANG` | `ia` | Telegram description language slot for prompts |
| `$MJ_OUT_LANG` | `eo` | Telegram description language slot for replies |

Environment variables `MEGAJAM_BOT_TOKEN`, `TELEGRAM_GROK_BOT_TOKEN`, `MEGAJAM_SECRET`, `MEGAJAM_WORKDIR`, `MEGAJAM_CLAUDE`, and `MEGAJAM_PERMISSION` work too.

## Claude flags

Each prompt is sent to Claude as:

```text
claude.exe --print --continue --output-format text --permission-mode acceptEdits
```

The prompt is written to stdin (so quotes and Turkish text stay intact). `--continue` keeps the conversation in the working folder. If there is no previous session, the script retries without `--continue`.

`acceptEdits` auto-approves file edits. Other tools (for example Bash) may still wait for approval and look "stuck". If you want fully unattended runs, set `$MJ_PERMISSION='bypassPermissions'` on first run, or edit `PermissionMode` in the local config. That mode can run commands without asking — only use it on a machine you trust.

## Security

- The script never calls `getUpdates` or sends chat messages, so it will not steal updates from another poller and will not spam a group or DM.
- Prompts and replies are encrypted with the shared secret (AES-256-CBC and HMAC-SHA256) before they leave the machine. A language-specific bot description only holds a sequence number and a pointer.
- Do not commit `%USERPROFILE%\.megajam-bridge\config.json` or paste the one-liner with real secrets into a public issue or gist.
- Anyone with the bot token can speak as that bot. Keep `config.json` on the PC private.
- Do not run two listeners at once against the same bot.

## License

You may use and change this script for your own machines.
