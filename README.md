# Kinesis Advantage 360 Pro

ZMK config for my Advantage 360 Pro. Fork of
[KinesisCorporation/Adv360-Pro-ZMK](https://github.com/KinesisCorporation/Adv360-Pro-ZMK);
Kinesis' own README is kept at [docs/upstream-readme.md](docs/upstream-readme.md)
for its reference tables — layer indicator colours, NKRO, battery reporting,
key positions.

- `config/adv360.keymap` — the layout. The only file worth editing.
- `keymap.html` — visual layer map. Open it in a browser; no server, no build.
- `tools/keymap-page.py` — regenerates `keymap.html` from the keymap.

## Why this exists rather than Clique

Clique (Kinesis' ZMK Studio build) cannot express `quick-release` on a sticky
key, and that one property is the difference between sticky shift being useful
and being a nuisance. Stock `&sk` drops the modifier when the **next key is
released**, so a fast roll after tapping shift capitalises more than one letter.
`quick-release` drops it on the next key **press**.

Moving to a config repo also puts the layout in git, which is what makes the
layer map below possible.

**The cost:** the layout now lives here, not in the keyboard. See
[Flashing](#flashing) — in particular, do not save in Clique again.

## The board

|                  |                                                        |
| ---------------- | ------------------------------------------------------ |
| Board            | Advantage 360 **Professional** (KB360-PRO), split, BLE  |
| Upstream config  | https://github.com/KinesisCorporation/Adv360-Pro-ZMK    |
| Branch           | `V3.0`                                                  |
| ZMK              | `ReFil/zmk`, revision `adv360-z3.5-2` (a Kinesis fork)  |
| Boards           | `adv360_left`, `adv360_right` — flashed separately      |
| Bootloader       | Mod + the inner column beside `T` (left) or `Y` (right) |

Not base ZMK. Kinesis maintain their own fork for the indicator LEDs and Clique;
some upstream ZMK features land here late or not at all. Anything you want to
use, check it exists in `ReFil/zmk@adv360-z3.5-2` first rather than in the ZMK
docs — the docs describe mainline.

## What this changes from stock

| # | Layer | Indicator | |
| --- | --- | --- | --- |
| 0 | Base | off | brackets on combos, sticky mods, Delete on shifted backspace |
| 1 | Kp | white | stock Kinesis keypad, untouched |
| 2 | Fn | blue | F1–F12, plus media and brightness |
| 3 | Mod | green | stock — Bluetooth, bootloader, battery, backlight |
| 4 | Nav | red | word and line motions |

Indicator is the colour the board's own layer LED shows, which is the only
feedback the keyboard gives about which layer is live.

### Brackets are combos

Left hand opens, right hand closes, and the row picks the pair:

|          |     |          |     |
| -------- | --- | -------- | --- |
| `R` + `T` | `(` | `Y` + `U` | `)` |
| `F` + `G` | `[` | `H` + `J` | `]` |
| `V` + `B` | `{` | `N` + `M` | `}` |

Every pair is two adjacent keys on one row, under one flattened index finger,
and no pair crosses the split — cross-half combos are the ones that suffer
latency.

This replaces a symbol layer that never became muscle memory, and the reason it
never did is worth writing down: the 360 has a full number row with every ANSI
symbol printed in its standard shifted position, so a symbol layer is a *second*
route to keys that already have one. The fingers keep taking the first. Combos
avoid that trap because four of these six — `(` `)` `{` `}` — had no dedicated
key at all before, only shift-chords on the number row.

`mod3` and `mod4`, the inner columns either side of `T` and `Y` (positions 20
and 21), are `&none` for the same reason. They used to hold `[` and `]`. Leaving
them bound would hand the brackets a fallback, and a fallback is what stops the
habit forming.

`require-prior-idle-ms = <125>` is what makes this safe to type on. `R`+`T` is
the only pair that is a common English bigram — *start*, *part*, *short* — and
prior-idle means a combo cannot fire if another key went down in the last 125 ms,
so a mid-word roll can never reach it. The other five (`fg`, `vb`, `yu`, `hj`,
`nm`) are rare enough not to matter. If `(` still misfires, lower `timeout-ms`
toward 30 before touching prior-idle.

### Sticky modifiers

Eight keys, all with `quick-release`: shift (both), ctrl (both thumbs), hyper,
alt and cmd on the bottom row, and `&caps_word` where the symbol layer key used
to be.

Three things about `quick-release` that are easy to get wrong:

- **It only affects the tapped path.** It is gated on `timer_started`, which is
  set in `on_sticky_key_binding_released`. *Hold* one of these and it falls
  through to "act like a normal key" and stays down as long as you do — so
  holding sticky Cmd and tapping Tab still walks the app switcher.
- **`ignore-modifiers` is what lets two of them chain.** Tap ctrl, tap shift,
  press `T` and you get Ctrl+Shift+T. Without it the ctrl is consumed by the
  shift press.
- **Hyper gets its own instance** (`&skh`) with a 2 s fuse rather than 1 s. It is
  a window-manager chord, not a typing modifier; you are usually thinking about
  where the window goes.

### Media, on the Fn layer

Fn is held from *either* bottom-row corner (positions 60 and 75), so the left
pinky holds it and the whole right hand is free. The arrangement is vim motion
rather than anything new to learn:

```
        U      I            bri− / bri+
  H     J      K     L     ;
prev  vol−   vol+  next  mute
        Space = play/pause
```

`j`/`k` is down/up, so it is volume. `h`/`l` is left/right, so it is track. `U`
and `I` sit in the same two columns as `J` and `K` (x=12.75 and 13.75), so
brightness is the same two fingers one row up. Space is play/pause because Space
is always play/pause.

F1–F12 stay on the number row, untouched.

This is on Fn rather than Mod deliberately. Mod carries `&bootloader` and
`&bt BT_CLR`; everyday volume does not belong on the same layer as the keys that
drop your Bluetooth pairing.

### The nav layer

Held with the left index from the inner column beside `G`. Every motion on it is
one that had no key before, only a two- or three-finger chord. Plain arrows are
deliberately absent — the base layer already has a dedicated arrow cluster, and
duplicating it here would be the same mistake the symbol layer made.

```
  Y      U      I      O          select
 ⇧⌥←    ⇧⌘←    ⇧⌘→    ⇧⌥→

  H      J      K      L      ;      '     move / delete
  ⌥←     ⌘←     ⌘→     ⌥→    ⌥⌫     ⌘⌫

                ,      .      /            zoom
               ⌘-     ⌘=     ⌘0
```

Left two go left, right two go right; outer jumps by word, inner by line.
`Y U I O` sit in the same columns as `H J K L`, so **the row above is the same
motion with shift added** — select rather than move, same finger, one row up.
That is the one worth having: `⇧⌘←` is awkward as a chord and trivial as a key.
Zoom uses `,` and `.` because they are `<` and `>`.

Alphas on this layer are `&none` rather than `&trans`, so a mistimed hold cannot
dump letters into a document. Modifiers, thumbs, Tab/Esc and the base arrows all
still pass through.

**The key position is on trial.** All three left inner-column keys sit in one
column; the nav key was moved down to the home row on 2026-09-12, swapping with
the duplicate Esc, on the principle that a key you *hold* belongs on the home row
and a key you *tap* can afford the reach. Swap them back to revert.

### Delete, and the repeat key

Delete had no key on the base layer at all — not moved, missing. It was lost when
Tab took the thumb position it used to occupy and survived only on the keypad
layer, so in practice the board could not delete forwards. A mod-morph on
Backspace recovers it for nothing: **Backspace normally, Delete when shifted.**
It composes with sticky shift rather than fighting it — tap shift, tap
backspace, never holding two keys.

`&key_repeat`, on the inner column beside `Y`, resends the last keycode *with
its modifiers*. That turns an awkward chord into one chord plus however many
cheap taps you need: `⌥⌫` once and three taps deletes four words back.

`&caps_word`, where the symbol layer key used to be, is the partner to sticky
shift — *one letter* versus *one word* — and `SCREAMING_CASE` had nowhere else
to live.

## The layer map page

`keymap.html` draws all four layers on a board you can click through. Open it
straight off disk — one file, no libraries, no build step. Hovering a key shows
the raw binding behind it. `⌘P` gives one layer per A4 page.

It is generated, not hand-written, so it cannot drift from the layout:

```sh
./tools/keymap-page.py
```

Run it after editing `config/adv360.keymap` and commit what changes.

Two things it reads, both already in the repo and both maintained upstream:

- `config/adv360.keymap` — what every key does. Layers are found by their
  `display-name`, and bindings are split on `&`, which is exact rather than a
  guess: every binding starts with one and none contain one.
- `config/info.json` — where every key physically is. KLE-style `x`/`y`/`w`/`h`
  in key units plus `r`/`rx`/`ry` rotation, in key-position order.

Taking the geometry from `info.json` rather than hardcoding a grid is what lets
the page draw this board honestly — the columns are staggered by different
amounts, the thumb clusters sit at ±15°, and several keys are 1.25u or double
height. Combos are drawn as a badge at the midpoint of the two keys that trigger
them, which is the whole point: a combo you cannot see on the map is a combo you
will not remember.

Only two things in `tools/keymap-page.py` are human knowledge rather than data:
`LAYER_META` (neither file records layer colours or what a layer is *for*) and
the keycode-to-legend table. A keycode with no entry falls back to a readable
form of its own name, so an unmapped key looks slightly ugly rather than
silently wrong.

`config/keymap.json` is the Kinesis GUI editor's copy of the layout. Nothing
here reads it and the build ignores it, so it will drift. That is fine — do not
try to maintain it.

## Building

**GitHub Actions**, which is the easy route: push, then download the artifact
from the run. `.github/workflows/build.yml` builds both halves on every push.

**Locally**, needs Docker or Podman:

```sh
make            # both halves -> firmware/
make left       # left only
```

On Apple Silicon the container is x86_64, so colima has to be started to match:

```sh
brew install docker colima
colima start --arch x86_64
```

It is slow. Actions is the better default.

## Flashing

**Read this before the first flash.** Clique and ZMK Studio save the keymap to
the settings partition, and settings **override the keymap compiled into
firmware**. Flashing a new build onto a board that has ever been saved from
Clique appears to do nothing at all.

Clearing that saved keymap is all it takes, and Clique can do it itself — no
reset image, no wiped pairings:

1. Open Clique and hit **Reset to Stock Keymap**. That drops the saved keymap
   from the settings partition, which is the thing that was shadowing the
   firmware.
2. Put the left half in the bootloader: hold **Mod** and press the inner column
   beside `T`. It mounts as a USB drive. Mod is `&mo 3` on the *right* half, so
   the right half has to be powered on to reach the key at all — switch it off
   once the drive has mounted.
3. Copy `left.uf2` onto the drive.
4. Right half only when the change needs it, see below: Mod + the inner column
   beside `Y` puts *that* half in the bootloader, then `right.uf2`.

Confirmed on hardware: reset to stock in Clique, bootloader from the keymap,
flashed `left.uf2`, and the build came up as expected — nothing needed
re-pairing.

The **Settings Reset** image on
[kinesis-ergo.com/support/kb360pro](https://kinesis-ergo.com/support/kb360pro/#firmware-updates)
is the heavier fallback if a board is wedged in some other way — flash it, then
`left.uf2`, following *their* ordering, and expect to re-pair Bluetooth
afterwards. It has not been needed here. If the keymap route to the bootloader
is not available either, double-clicking the module's own reset button mounts
the drive.

Then, permanently: **do not save in Clique again.** One save and this repo stops
being the source of truth, silently. Opening Clique to look is fine.

If you ever need the stock layout back, Kinesis publish factory-default firmware
on the same support page.

### Which half to flash

**Left only when you changed `config/adv360.keymap`. Both halves when you
changed anything under `config/boards/`, a defconfig, or `west.yml`.**

This is not because the halves sync — nothing is transferred, and the right half
is simply never updated. In ZMK the peripheral does not process the keymap at
all; it reports key *positions* over BLE and the left half resolves them against
the keymap, behaviours and combos. So for a keymap change the right half has
nothing to learn. Anything touching ZMK itself or the split protocol does need
both, or the halves can fail to pair.

**Adding a layer does not change this**, which is worth knowing because it looks
like it should. The layer indicator LED on the right module keys off the layer
*number* that crosses the split, and the number-to-colour table is compiled into
that module's firmware for all 32 layers regardless of how many the keymap
defines. Confirmed on hardware: the nav layer was added and only the left half
flashed, and the right module lit red for a layer it had never been told about.

### Which artifact

Two jobs build on every push, and **both produce files with identical names**,
so downloading one on top of the other silently overwrites it. Clear the
directory between downloads.

| Job | Artifact | Left half |
| --- | --- | --- |
| `Build (Clique)` | `firmware-clique` | ZMK Studio compiled in |
| `Build (Legacy)` | `firmware-no-clique` | no Studio |

"Legacy" does not mean outdated — it is Kinesis' word for the original
repo-based workflow, built from the same commit as the other. This board runs
the **Clique** build, so Clique can still connect, which is exactly why the
"never save in Clique" rule above has to be kept by hand rather than being
enforced. The left half is about 63 KB larger in that build; the right half is
byte-identical between the two.

Mod+V types the build date, branch and commit, so you can always check what is
actually running. Flash from a build of the branch you merged to, not of a
feature branch that is about to be squashed away — otherwise it reports a commit
that no longer exists.

## Checking it works

The combos and the sticky behaviour are the whole point, so test those:

- All six bracket combos fire — `R`+`T` → `(`, `H`+`J` → `]`, and so on.
- Type *start* and *part* at speed. No stray `(`. This is `require-prior-idle-ms`
  doing its job and it is the one number most likely to need tuning.
- Positions 20 and 21, the inner columns beside `T` and `Y`, are dead.
- Tap sticky shift, then type `abc` quickly → `Abc`. `ABC` means `quick-release`
  did not take.
- Tap sticky shift, wait a second, type `a` → `a`. The fuse works.
- Tap sticky ctrl, tap sticky shift, press `T` → Ctrl+Shift+T. Chaining works.
- *Hold* sticky Cmd and tap Tab twice → the app switcher advances two apps.
- Hyper still fires your window-manager chords.
- `&caps_word` at position 39: tap, type `const`, press space → `CONST `.
- The Mod layer still reaches `&bootloader`. You need it to reflash.

## Keeping up with upstream

```sh
git fetch upstream
git merge upstream/V3.0
```

Expect one conflict the first time: upstream still has a `README.md` where this
fork moved it to `docs/upstream-readme.md`. Keep this fork's version.
