# DIRECTOR'S CUT — Glass Box development log

**Event:** 2026 Epic AI MegaJam  
**Theme:** DIRECTOR'S CUT  
**Game:** DIRECTOR'S CUT  
**Engine:** Unreal Engine 5.8.3  
**Participation:** Solo Driver (one human, Erdoğan Zeylan)  
**Date:** 16 November 2026, Europe/Istanbul (UTC+3)  
**Itch page:** https://erdocool.itch.io/directors-cut  
**Gameplay video:** https://youtu.be/F3Lbm8QCBL0  

This is the public Glass Box development log for the jam submission.

---

## Concept and theme fit

DIRECTOR'S CUT is a first-person mystery about a film editor. The theme is taken literally: the player is a cutter, and the truth is on the footage.

The opening of the design is a package that arrives at the player's studio. Inside it are a hard disk and a small card. At the editing desk the player matches a clip to its sound. When the pair is correct, the desk yields the address of an old apartment building and a hint to the first key. The rest of the mystery is not spelled out on screen. Short clue videos on the studio monitors, and whatever the player writes down, are meant to be enough; memory and notes do the rest.

Play then moves to that building. A street of City Sample shells, `L_Town`, holds the studio building (a copy of City Sample building 3 NYAF) and the main apartment block (a copy of building 5 SFA). The enterable interiors are the project's own levels, placed inside those shells: the studio (`LI_Studio_MJ`, from `L_Apartment`) and the apartment block (`LI_Building_MJ`, from `L_Building`). Leaving the studio fades and teleports the player to the apartment entrance rather than asking them to walk the whole street.

Inside the block, the design has a doorman's flat, a boiler room, neighbour flats, the manager's flat, and a hidden room. Doors are separate hinged actors with a lock and a key ID; a door opens only with its matching key. The key chain, as built, is:

street door → Flat 1 → doorman → boiler room → Flat 2 → Flat 3 → manager → hidden room

No key is left behind the door it opens. Residents (doorman Hasan, the Aksoy family — Sevgi, Kemal, and young Elif — neighbour Deniz, and manager Selim) stand in their rooms. The project had no MetaHuman characters, so these are recolored engine mannequins (Manny / Quinn) with collision off so they do not block doorways.

A countdown starts when the player enters the apartment's street door. The timer starts at 3:00, and each newly collected key adds 60 seconds. If time runs out, a Game Over screen appears, but the whole game does not reset. Only the current day restarts: the player is returned to the studio and the timer is cleared. Knowledge stays with the player.

The blue envelope on the editing desk is the ending. The first time the player tries to open it, the game says it is not time yet. After the timer has run out once, opening the envelope plays the finale and a "DIRECTOR'S CUT" screen.

That loop — watch, cut, enter the building, run out of time, wake up in the studio, cut again with better knowledge — is the theme: the player is editing the day as well as the footage.

---

## What shipped

Core systems were built in Unreal Blueprints (`BP_MJHUD`, `BP_MJGameMode`, door/key components `BPC_MJDoor` / `BPC_MJKey`, studio-exit teleport, and media-texture slots on the two editing-desk screens) and placed on `L_Town`.

**Scope cut.** Budget and time ran out before every flat could be finished to the same standard. The playable scope was cut to one fully dressed flat. The other flats and the stairwell exits were walled off by the developer himself.

**Editing desk.** Pressing E at the desk blends to a fixed camera (`MJ_DeskCam`) aimed at the monitors. Pressing E again stands the player up.

**Pause menu.** ESC or P opens a pause menu (Resume, R to restart the day, Q to quit). It uses time dilation, because SetGamePaused and QuitGame nodes crashed the editor during scripted graph building.

**Start-point fix.** In the packaged build, the player could fall into the void at startup. `L_Town` is not a World Partition world, so the level instances streamed in asynchronously. The fix is to FlushLevelStreaming, freeze movement for two seconds, then teleport the player to the day start.

**Language.** All in-game text was switched to English.

**Intro and clips.** A 10-second English intro movie, with the tagline "Every cut hides a truth.", plays at startup through MoviePlayer StartupMovies. The Movies folder is staged as non-UFS so the intro and the monitor clips ship with the build.

**Music.** The tension music is an original 60-second seamless loop, generated procedurally with Python (numpy and scipy). No samples and no paid or AI audio service were used. In the game it loops as a 2D ambient sound, and it also plays under the intro.

**Night lighting.** The shipped lighting is a moonlight-blue, low directional light. Earlier in production an unbound post-process volume, `MJ_Exposure_PPV`, was added to cap eye adaptation (EV100 −2.5 to 0.5) after blown-out daylight shots; that calibration was carried to `L_Town`.

**Package and upload.** The game was packaged as a Windows Shipping build after Windows Smart App Control was turned off (it had blocked the Unreal build tool). The zip is about 6.6 GB, over itch.io's 1 GB web-upload limit, so it was uploaded with itch's butler tool. The page is at https://erdocool.itch.io/directors-cut. The gameplay video is at https://youtu.be/F3Lbm8QCBL0.

---

## How AI was used

One human directed the project. Agents wrote scripts, generated reference images and some 3D props, and drove the Unreal Editor on the home PC through a small bridge. No gameplay or asset work was purchased as a paid service beyond the jam credits and subscriptions already on the accounts. Every generated image and 3D step was logged.

**Direction and code.** Grok Bot broke the work into tasks, wrote Unreal Python, built Blender export scripts, and kept the production log. Early on, Claude Code ran on the laptop and then on the home PC, talking to Unreal through the same kind of bridge, until Anthropic API credits ran out on 14 November 2026 (around 13:10 Europe/Istanbul). The bridge was then switched to the Cursor CLI (`cursor-agent`) in the project folder. The Cursor subscription went past due (the 14 November Pro+ invoice was unpaid). From then, the bridge ran a no-AI exec mode: scripts written by Grok Bot were executed directly in the already-open Unreal Editor, and the printed output was sent back. No Cursor or Claude call is made in that mode. Exec mode is in the public bridge repo (commit `e231cf3`).

**The bridge.** The public repo is [Erdocool/megajam-bridge](https://github.com/Erdocool/megajam-bridge). A PowerShell listener on the Windows PC polls an encrypted Telegram mailbox (it does not call `getUpdates`). Short messages travel in the slot; longer ones are stored as encrypted pages on telegra.ph. `!py` and `!pyurl` use Unreal's bundled Python and the editor's Python Remote Execution (Python Editor Script Plugin and Remote Execution enabled) to run scripts in the open project. Exec mode also accepts `!ping`. The Unreal connection is local (`127.0.0.1`, multicast `239.0.0.1:6766`).

**Images.** Approved studio stills and isolated product photos were made with the built-in GenerateImage tool (not a paid jam image credit). Those stills were the visual brief for the studio and for image-to-3D.

**3D.** Early story props (shipping box, blue envelope, hard disk, note card) were generated with Hyper3D Rodin Gen-2.5 and then cleaned, scaled, and re-exported in Blender 4.5.14 LTS. A larger furniture set was made as image-to-3D on Tripo Studio's web app (existing Studio credits; the API client was not used, and API credits are a separate pool). Those GLBs were postprocessed in the same Blender (units, pivots, decimation where it did not break UVs, FBX for Unreal). Many other props — kitchen units, doors, bathroom and boiler-room fittings, curtains, and earlier apartment-prop backups — were modelled procedurally in Blender for no generation credit, with CC0 textures from Poly Haven and ambientCG. Engine packs already in the project (FreeFurniturePack, Lucapy Old Living Room, Starter Content) were reused. City Sample building assets were copied into the project for the street and the two hero shells; the original City Sample files were not edited.

**Audio and video tooling.** The tension loop was written in Python with numpy and scipy, not with an AI audio service. The intro movie was assembled with ffmpeg. There is no production-log record of fal, PBRgen, Meshy, Rokoko, MetaHuman, or a video model being used in production. A full City Sample project rebuild, and a later Fab city backdrop in a second Unreal project, were tried and then dropped in favour of the working DirectorsCut / `L_Town` build.

---

## Problems we hit

**Credits ran out, twice.** Anthropic API credits ended on 14 November, which stopped Claude Code on the home PC. The MegaJam $50 Cursor event credit had already reached its claim limit and was not used; work continued on the existing Cursor subscription. When that subscription went past due, editor work continued through the free exec mode. The 15 November itch / Epic "last day" mail also treated the Claude and Cursor / Grok Bot credits as exhausted. PBRgen's jam offer was only valid that day and was not used in the production log.

**Telegraph flood limit.** Long bridge replies, including editor screenshots, were published through telegra.ph. That path hit a flood limit, so screenshots were no longer sent through the bridge. The workaround was to batch each task into one script, let the user check the result in Play, and have the user send phone photos. Small editor tweaks that were faster by hand were written out as short steps instead of being forced through the bridge.

**Lighting blowout.** Early `L_Building` shots showed blown-out lighting: a white street facade, a washed-out corridor, and ground-floor cutaways that were hard to read. Contrast was also uneven — some floors too dark, others too bright. The level had a weak sun (2.5 lux) and SkyLight (1.0) and no post-process volume. `MJ_Exposure_PPV` was added to cap eye adaptation without changing lights. A related auto-exposure problem the fix was written for: the exterior could also darken when the player walked up to the building. Separately, a night lighting setup had been saved over in daylight; a restore script was kept for that. The shipped look is the moonlight-blue low directional light described above.

**City pivots, and the cost of them.** The playable work began in DirectorsCut (`L_Apartment`, then `L_Building`). Mid-jam the interiors were moved into City Sample shells on a new street map, `L_Town`. The project was then migrated to a second Unreal project and wrapped in a Fab city pack used as a backdrop (center meshes only, no collision or shadows). The Fab city was rejected. A further plan was to abandon that and rebuild the flats from scratch inside the full City Sample sample project, with larger rooms. With the deadline at 04:59 Europe/Istanbul on 16 November, that rebuild was judged a time sink. Work returned to DirectorsCut and the existing `L_Town` build, and that is the version that was packaged.

**Scripted Blueprint crashes.** Building some Blueprint graphs from scripts crashed the editor. A player-FX graph built from a script crashed the editor; the asset was never saved to disk and was not attached to the player. SetGamePaused and QuitGame nodes also crashed the editor during scripted graph building, which is why the pause menu uses time dilation. The interact key (E) could not be pressed from the remote machine, so playtests by the developer were required.

**Packaged start in the void.** Because `L_Town` is not a World Partition world, level instances streamed asynchronously in the packaged build and the player spawned into empty space. FlushLevelStreaming, a two-second movement freeze, and a teleport to the day start fixed it.

**The 1 GB itch limit, and a blocked build tool.** Windows Smart App Control blocked the Unreal build tool until it was turned off. The Shipping zip was about 6.6 GB, so the itch web uploader (1 GB limit) could not take it; butler could.

**Furniture repetition, then a hard scope cut.** Many furnishings in the flats were the same meshes, only retinted (material variants on 126 props, plus five newly added objects: a safe, a phone, a folder, a radio, and a book). A playtest photo showed repeated coat racks and shoe racks and placements that felt random. Unique per-flat models and a tighter layout were started after that feedback, and later room rebuilds retired some of the repeated pieces. There was not enough time to finish every flat. The developer walled off the other flats and the stairwell exits and shipped one fully dressed apartment.

Other friction that slowed the same days: Cursor CLI tasks on the bridge hitting a 900-second timeout during the first `L_Building` blockout; and doors or props that were technically present but not sitting where a player would expect them.

---

## Lessons

- Keep a no-AI path into the editor. Exec mode (`!py` / `!pyurl`) is what still let us ship systems after both Claude and Cursor were unavailable.
- Batch remote Unreal work. One script per task, verified in Play, beats a stream of screenshot replies that can trip a Telegraph flood limit.
- Cap exposure early. A cheap sun and default auto-exposure will blow out facades and corridors; a single post-process volume is cheaper than relighting under a deadline.
- Recoloring the same couch is not a different flat. Unique silhouettes have to be modelled or the repetition is obvious in a screenshot. When time runs out, a hard scope cut is cleaner than shipping every room half-finished.
- Scope the city to what already plays. The City Sample and Fab pivots cost hours. Falling back to the working DirectorsCut / `L_Town` map is what left a build to upload.
- Do not hide a key behind the door it opens, and do not reset the whole game on a timeout. The day-restart loop keeps the player's knowledge, which is the point of the theme.
- Test the packaged build, not only Play-in-Editor. Async level streaming and a blocked build tool only showed up at package time.
- Log prompts and tools as you go. The Glass Box and Hyper3D "tools you used" fields are then a summary, not a reconstruction.

---

## Sources

Only facts from the production record, the public bridge repo ([Erdocool/megajam-bridge](https://github.com/Erdocool/megajam-bridge)), and the final state of the shipped build as of 16 November 2026, about 02:45 Europe/Istanbul (UTC+3). No counts, times, or tool names were invented.
