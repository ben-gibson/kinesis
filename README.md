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
| Bootloader       | double-click the reset button on the module             |

Not base ZMK. Kinesis maintain their own fork for the indicator LEDs and Clique;
some upstream ZMK features land here late or not at all. Anything you want to
use, check it exists in `ReFil/zmk@adv360-z3.5-2` first rather than in the ZMK
docs — the docs describe mainline.

## What this changes from stock

Layers 1 (Kp) and 3 (Mod) are untouched. Layer 2 (Fn) keeps its F-keys and gains
media controls; everything else is on the base layer.

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

### Everything else

`&caps_word` at position 39 is the only genuinely new key. It is the partner to
sticky shift — *one letter* versus *one word* — and `SCREAMING_CASE` had nowhere
else to live.

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

1. Get the **Settings Reset** image from
   [kinesis-ergo.com/support/kb360pro](https://kinesis-ergo.com/support/kb360pro/#firmware-updates)
   and follow *their* ordering — it is their procedure, not mine.
2. Double-click the reset button on the left module. It mounts as a USB drive.
   Flash the reset image, then `left.uf2`.
3. Repeat on the right module with `right.uf2`.
4. **This wipes Bluetooth pairings.** Expect to re-pair.

Then, permanently: **do not save in Clique again.** One save and this repo stops
being the source of truth, silently. Opening Clique to look is fine.

If you ever need the stock layout back, Kinesis publish factory-default firmware
on the same support page.

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
