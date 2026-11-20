# Changelog

## 1.1.0

**50 activities — every stage is now a real function.** Each of the 50 evolution
stages (`booting`…`phantomroot`) is a runnable activity (`mantis do <key>`,
`mantis activities`) that produces a report, costs PSYCHE, awards XP, advances
the pet, and surfaces a matching Academy teaching moment. Three kinds, colour-
coded throughout: **passive** (real, benign, read-only), **defense** (audits your
own posture), **sim** (offensive-named stages simulated on invented targets —
no real attack, each paired with a defend-against-this lesson).

**Passive / Active idle modes.** `mantis mode active|passive` — active autonomously
performs activities it has grown into; passive stays quiet and acts only on
command. Exposed on the web mode switch, the CLI, and the e-ink *meditate+pet*
button combo; honoured by both the server and e-ink background loops.

**New Command Deck web UI** (default at `/`, old panel view at `/classic`): a
real-time operator console — hero portrait, PSYCHE ring, live activity stream,
the 50-function activity deck, evolution ladder, security-posture gauge,
Inner-Mind coach, Academy quiz and fleet. Mobile-responsive, theme-aware.

**Artwork refreshed from the original reference sheets** and bundled as default
sprites; two cinematic render portraits included as hero art with watermarks
removed (`mantis/assets/art/`).

**De-branding:** all "Metal Gear Solid" / "Foxhound" / "Psycho Mantis" references
removed; the project is an original, non-commercial creation ("FIREFOX" unit).

**Raspberry Pi install kit** (`INSTALL-PI.md` + `deploy/`): a hardened,
idempotent `install_pi.sh` that provisions a venv, enables SPI/I²C, installs the
panel driver, and generates a boot-on-start systemd service for **e-ink / web /
HyperPixel colour**; a one-line `bootstrap.sh` (`curl … | bash`); a headless
`firstrun-mantis.sh` first-boot auto-installer; and a new `mantis color loop`
framebuffer daemon for HyperPixel.

## 1.0.0

Initial release — psychic Tamagotchi: 70 moods, 100 levels (capped MANTIS),
50 evolution stages, 16-spell spellbook, souls/deeds/augments, Academy,
Inner-Mind coach, security posture, consensual fleet, e-ink (2.13") + color
(HyperPixel) + web + TUI, GPIO buttons, battery/hibernate, install wizard.
