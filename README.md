# MegaJam agent bridge

A small Windows PowerShell 5.1 script that lets another machine send prompts to an agent CLI on your PC. The default engine is [Cursor CLI](https://cursor.com/docs/cli) (`cursor-agent`). Set `$MJ_ENGINE='claude'` to fall back to [Claude Code](https://docs.claude.com/en/docs/claude-code).

The other machine publishes an encrypted prompt through the [Telegram Bot API](https://core.telegram.org/bots/api). This script polls a private slot on that bot (it does **not** call `getUpdates`, so it will not fight with other uses of the same bot), runs the selected CLI in your project folder, shows the conversation in the PowerShell window, and publishes the reply the same way.

Short messages travel in the slot itself. Longer ones are stored as encrypted pages on [telegra.ph](https://telegra.ph); only a path is written to the slot. The public repo and those pages never contain the bot token, the shared secret, or plaintext prompts.

**This repository has no secrets.** The bot token and the shared secret stay on your PC (and on the machine that sends prompts).

## What you need

- Windows PowerShell 5.1 or later (Windows 10/11 is fine)
- For the default engine: Cursor CLI installed and logged in (`irm 'https://cursor.com/install?win32=true' | iex`, then `cursor-agent login`)
- For the Claude fallback: Claude Code CLI installed and logged in
- Outbound HTTPS to `api.telegram.org` and `api.telegra.ph`
- A Telegram bot token and a shared secret (someone sets these up once and gives you the first-run command)

The script looks for Cursor CLI at `%LOCALAPPDATA%\cursor-agent\cursor-agent.exe` (the official Windows install path), then on `PATH`, preferring `cursor-agent` over a bare `agent` command so another product is not started by mistake. For Claude it still looks at `%USERPROFILE%\.local\bin\claude.exe`, then `PATH`. The default working folder is `C:\MegaJam` (created if it does not exist). You can override these; see below.

## First run (any Windows PC)

Paste the one-line command you were given. It looks like this (values filled in for you):

```powershell
$MJ_ENGINE='cursor'; $MJ_TOKEN='BOT_TOKEN'; $MJ_SECRET='SECRET'; $MJ_PERMISSION='bypassPermissions'; [Net.ServicePointManager]::SecurityProtocol='Tls12'; iex (irm https://raw.githubusercontent.com/Erdocool/megajam-bridge/main/bridge.ps1)
```

The window stays open and prints "Dinleniyor...". Keep it open while you want the bridge to run. Settings, including the token, are saved to:

`%USERPROFILE%\.megajam-bridge\config.json`

The first run also saves a copy of the script to `%USERPROFILE%\.megajam-bridge\bridge.ps1`. If that copy was missing on an earlier run, use the `irm | iex` line above rather than `-File`.

Do not run this on two PCs at the same time; they share one mailbox. Close any previous bridge window before starting a new one.

## Later runs

After the first run, either open a new PowerShell window and paste:

```powershell
[Net.ServicePointManager]::SecurityProtocol='Tls12'; iex (irm https://raw.githubusercontent.com/Erdocool/megajam-bridge/main/bridge.ps1)
```

or run the saved copy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.megajam-bridge\bridge.ps1"
```

If a local `config.json` already exists and has no `Engine` field, the script defaults to Cursor. Set `$MJ_ENGINE='claude'` before the command (or edit `Engine` in the config) to go back to Claude Code.

## Optional overrides (set before `irm | iex`)

| Variable | Default | Meaning |
| --- | --- | --- |
| `$MJ_ENGINE` | `cursor` | `cursor` or `claude` |
| `$MJ_TOKEN` | (required once) | Telegram bot token |
| `$MJ_SECRET` | (required once) | Shared secret; messages that do not decrypt are ignored |
| `$MJ_PERMISSION` | `acceptEdits` | Claude: `--permission-mode`. Cursor: `bypassPermissions` (or `force` / `yolo`) adds `--force --trust --approve-mcps --sandbox disabled` |
| `$MJ_WORKDIR` | `C:\MegaJam` | Folder where the agent runs |
| `$MJ_CURSOR` | `%LOCALAPPDATA%\cursor-agent\cursor-agent.exe` or `PATH` | Full path to `cursor-agent` |
| `$MJ_CLAUDE` | `%USERPROFILE%\.local\bin\claude.exe` or `PATH` | Full path to `claude.exe` |
| `$MJ_MODEL` | (Cursor default) | Optional Cursor `--model` value |
| `$MJ_TIMEOUT` | `900` | Max seconds for one agent run |
| `$MJ_POLL` | `1` | Seconds between inbox checks |
| `$MJ_IN_LANG` | `ia` | Telegram description language slot for prompts |
| `$MJ_OUT_LANG` | `eo` | Telegram description language slot for replies |

Environment variables `MEGAJAM_ENGINE`, `MEGAJAM_BOT_TOKEN`, `TELEGRAM_GROK_BOT_TOKEN`, `MEGAJAM_SECRET`, `MEGAJAM_WORKDIR`, `MEGAJAM_CURSOR`, `MEGAJAM_CLAUDE`, `MEGAJAM_MODEL`, and `MEGAJAM_PERMISSION` work too.

## Agent flags

Each prompt is written to stdin (so quotes and Turkish text stay intact). `--continue` keeps the conversation in the working folder. If there is no previous session, the script retries without `--continue`.

### Cursor (default)

```text
cursor-agent.exe --print --continue --output-format text --force --trust --approve-mcps --sandbox disabled
```

`--force` (and the extra flags) are only added when `$MJ_PERMISSION` is `bypassPermissions`, `unrestricted`, `force`, or `yolo`. Otherwise the script passes `--print --continue --output-format text --trust`. In that mode Cursor can still write workspace files, but shell, MCP, and web-fetch actions that need approval are rejected and the run can look stuck. For unattended runs, use `$MJ_PERMISSION='bypassPermissions'`. That mode can run commands without asking — only use it on a machine you trust.

Cursor CLI also reads `AGENTS.md` and `CLAUDE.md` at the project root, plus `.cursor/rules`. Copying `CLAUDE.md` to `AGENTS.md` is optional.

### Claude (fallback)

```text
claude.exe --print --continue --output-format text --permission-mode acceptEdits
```

`acceptEdits` auto-approves file edits. Other tools (for example Bash) may still wait for approval and look "stuck". If you want fully unattended runs, set `$MJ_PERMISSION='bypassPermissions'` on first run, or edit `PermissionMode` in the local config.

## Security

- The script never calls `getUpdates` or sends chat messages, so it will not steal updates from another poller and will not spam a group or DM.
- Prompts and replies are encrypted with the shared secret (AES-256-CBC and HMAC-SHA256) before they leave the machine. A language-specific bot description only holds a sequence number and a pointer.
- Do not commit `%USERPROFILE%\.megajam-bridge\config.json` or paste the one-liner with real secrets into a public issue or gist.
- Anyone with the bot token can speak as that bot. Keep `config.json` on the PC private.
- Do not run two listeners at once against the same bot.

## License

You may use and change this script for your own machines.
