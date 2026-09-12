#!/usr/bin/env python3
"""Render keymap.html from the keymap and the board's physical layout.

    ./tools/keymap-page.py

Two inputs, both already in the repo and both maintained by someone else:

  config/adv360.keymap   what every key does. The source of truth for the
                         firmware, so the page cannot drift from what gets
                         flashed.
  config/info.json       where every key physically is. KLE-style x/y/w/h in
                         key units plus r/rx/ry rotation for the thumb
                         clusters, listed in key-position order.

Taking the geometry from info.json rather than hardcoding a grid is what lets
this draw the 360 honestly: the columns are staggered by different amounts, the
thumb clusters sit at +/-15 degrees, and several keys are 1.25u or double
height. None of that is worth retyping, and all of it is already there.

Only two things here are human knowledge rather than data: LAYER_META below
(neither file records layer colours or what a layer is *for*) and the
keycode-to-legend table. A keycode with no entry falls back to a readable form
of its own name, so an unmapped key looks slightly ugly rather than silently
wrong.
"""

import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYMAP = os.path.join(ROOT, "config", "adv360.keymap")
INFO = os.path.join(ROOT, "config", "info.json")
TEMPLATE = os.path.join(ROOT, "tools", "keymap-page.template.html")
OUTPUT = os.path.join(ROOT, "keymap.html")

KEY_COUNT = 76

# `led` is the colour the board's own layer indicator shows, from the table in
# README.md. Worth carrying onto the page: it is the only feedback the keyboard
# gives you about which layer is live, so the page's accent matching it means
# one less thing to translate.
LAYER_META = [
    {"name": "Base", "accent": "--l0", "led": "off",
     "blurb": "Nothing held. Brackets come from the combos drawn between the "
              "keys; the inner columns either side of T and Y are deliberately "
              "dead."},
    {"name": "Keypad", "accent": "--l1", "led": "white",
     "blurb": "Stock Kinesis keypad layer, untouched. Toggled from the key "
              "above 5."},
    {"name": "Fn", "accent": "--l2", "led": "blue",
     "blurb": "F1-F12 across the number row, and media under the right hand. "
              "Held from either bottom-row corner key, so the left pinky holds "
              "while the right hand works. j/k is volume because j/k is "
              "down/up; u/i is brightness, the same two fingers one row up; "
              "h/l is previous/next; Space is play/pause."},
    {"name": "Mod", "accent": "--l3", "led": "green",
     "blurb": "Bluetooth profiles, bootloader, battery and backlight. Held "
              "from the key above 6. This is how you get back into the "
              "bootloader to reflash."},
    {"name": "Nav", "accent": "--l4", "led": "red",
     "blurb": "Word and line motions, held with the left index from the inner "
              "column beside T so the whole right hand is free. Left two go "
              "left, right two go right; outer jumps by word, inner by line. "
              "No plain arrows on purpose — those already have dedicated keys "
              "on the base layer."},
]

TRANSPARENT = ("&trans",)
UNBOUND = ("&none",)

# Plain &kp keycodes whose legend is not just the name.
LEGEND = {
    "EQUAL": "=", "MINUS": "-", "GRAVE": "`", "BSLH": "\\",
    "SEMI": ";", "SQT": "'", "COMMA": ",", "DOT": ".", "FSLH": "/",
    "LBKT": "[", "RBKT": "]", "LBRC": "{", "RBRC": "}",
    "LPAR": "(", "RPAR": ")", "TILDE": "~", "UNDER": "_", "PLUS": "+",
    "PIPE": "|", "COLON": ":", "DQT": "\"", "QMARK": "?", "EXCL": "!",
    "AT": "@", "HASH": "#", "DLLR": "$", "PRCNT": "%", "CARET": "^",
    "AMPS": "&", "STAR": "*", "LT": "<", "GT": ">",
    "N0": "0", "N1": "1", "N2": "2", "N3": "3", "N4": "4",
    "N5": "5", "N6": "6", "N7": "7", "N8": "8", "N9": "9",
    "TAB": "Tab", "ESC": "Esc", "BSPC": "Bksp", "DEL": "Del",
    "ENTER": "Enter", "RET": "Enter", "SPACE": "Space", "CAPS": "Caps",
    "LEFT": "←", "DOWN": "↓", "UP": "↑", "RIGHT": "→",
    "HOME": "Home", "END": "End", "PG_UP": "PgUp", "PG_DN": "PgDn",
    "LSHFT": "Shift", "RSHFT": "Shift", "LCTRL": "Ctrl", "RCTRL": "Ctrl",
    "LALT": "Alt", "RALT": "Alt", "LGUI": "Cmd", "RGUI": "Cmd",
    "KP_NUM": "Num", "KP_EQUAL": "=", "KP_DIVIDE": "/", "KP_MULTIPLY": "*",
    "KP_MINUS": "-", "KP_PLUS": "+", "KP_ENTER": "Enter", "KP_DOT": ".",
    "C_VOL_UP": "Vol+", "C_VOL_DN": "Vol−", "C_MUTE": "Mute",
    "C_PP": "Play", "C_NEXT": "Next", "C_PREV": "Prev",
    "C_BRI_UP": "Bri+", "C_BRI_DN": "Bri−",
}
for _n in range(10):
    LEGEND["KP_N%d" % _n] = str(_n)

# Modifier functions, for things like LS(LC(LA(LGUI))).
MOD_FN = {
    "LS": "⇧", "RS": "⇧", "LC": "⌃", "RC": "⌃",
    "LA": "⌥", "RA": "⌥", "LG": "⌘", "RG": "⌘",
}
MOD_NAME = {
    "LSHFT": "Shift", "RSHFT": "Shift", "LCTRL": "Ctrl", "RCTRL": "Ctrl",
    "LALT": "Alt", "RALT": "Alt", "LGUI": "Cmd", "RGUI": "Cmd",
}

# Behaviours that take a layer number.
LAYER_BEHAVIOURS = {
    "mo": ("hold for layer", "sw"),
    "tog": ("toggle layer", "sw"),
    "to": ("switch to layer", "sw"),
    "sl": ("sticky layer", "sw"),
    "lt": ("layer tap", "sw"),
}

# Sticky modifier behaviours defined in the keymap, and how long they last.
STICKY = {
    "sk": "sticky",
    "skq": "sticky, quick-release",
    "skh": "sticky, quick-release, 2s",
}


def strip_comments(text):
    """Drop // and /* */ comments so they cannot be read as bindings."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


# ---------------------------------------------------------------- geometry

def load_geometry():
    """The 76 key rectangles, in key-position order, from config/info.json."""
    with open(INFO) as fh:
        info = json.load(fh)

    raw = info["layouts"]["LAYOUT"]["layout"]
    if len(raw) != KEY_COUNT:
        sys.exit("config/info.json describes %d keys, expected %d"
                 % (len(raw), KEY_COUNT))

    keys = []
    for k in raw:
        keys.append({
            "x": float(k["x"]), "y": float(k["y"]),
            "w": float(k.get("w", 1)), "h": float(k.get("h", 1)),
            "r": float(k.get("r", 0)),
            "rx": float(k.get("rx", 0)), "ry": float(k.get("ry", 0)),
            "label": k.get("label", ""),
        })
    return keys


def key_centre(k):
    """Centre of a key in board coordinates, after any rotation."""
    cx, cy = k["x"] + k["w"] / 2, k["y"] + k["h"] / 2
    if not k["r"]:
        return cx, cy
    a = math.radians(k["r"])
    dx, dy = cx - k["rx"], cy - k["ry"]
    return (k["rx"] + dx * math.cos(a) - dy * math.sin(a),
            k["ry"] + dx * math.sin(a) + dy * math.cos(a))


def board_extent(keys):
    """Bounding box of the board, taking rotated corners into account."""
    xs, ys = [], []
    for k in keys:
        corners = [(k["x"], k["y"]), (k["x"] + k["w"], k["y"]),
                   (k["x"], k["y"] + k["h"]), (k["x"] + k["w"], k["y"] + k["h"])]
        if k["r"]:
            a = math.radians(k["r"])
            rot = []
            for (px, py) in corners:
                dx, dy = px - k["rx"], py - k["ry"]
                rot.append((k["rx"] + dx * math.cos(a) - dy * math.sin(a),
                            k["ry"] + dx * math.sin(a) + dy * math.cos(a)))
            corners = rot
        xs += [c[0] for c in corners]
        ys += [c[1] for c in corners]
    return max(xs), max(ys)


# ---------------------------------------------------------------- keymap

def split_bindings(body):
    """A bindings block -> one string per key.

    Every binding starts with '&' and none of them contain one, so splitting
    before each '&' is exact rather than a guess.
    """
    body = " ".join(body.split())
    parts = [p.strip() for p in re.split(r"(?=&)", body) if p.strip()]
    return parts


def load_layers():
    src = strip_comments(open(KEYMAP).read())

    pattern = r'(\w+)\s*\{\s*display-name = "([^"]*)";\s*bindings = <(.*?)>;'
    found = re.findall(pattern, src, re.S)
    if not found:
        sys.exit("no layers with bindings found in config/adv360.keymap")

    layers = []
    for node, name, body in found:
        binds = split_bindings(body)
        if len(binds) != KEY_COUNT:
            sys.exit("layer %s (%s) has %d bindings, expected %d"
                     % (node, name, len(binds), KEY_COUNT))
        layers.append({"node": node, "name": name, "bindings": binds})

    if len(layers) != len(LAYER_META):
        sys.exit("keymap has %d layers, LAYER_META describes %d"
                 % (len(layers), len(LAYER_META)))
    return layers


def load_combos():
    """The combos node -> {layer number: [combo, ...]}."""
    src = strip_comments(open(KEYMAP).read())

    block = re.search(r'combos\s*\{(.*?)\n\s{2}\};', src, re.S)
    if not block:
        return {}

    combos = {}
    child = (r'(\w+)\s*\{(.*?)\};')
    for node, body in re.findall(child, block.group(1), re.S):
        pos = re.search(r'key-positions = <([^>]*)>', body)
        binding = re.search(r'bindings = <([^>]*)>', body)
        if not pos or not binding:
            continue
        positions = [int(p) for p in pos.group(1).split()]
        on = re.search(r'layers = <([^>]*)>', body)
        on_layers = [int(n) for n in on.group(1).split()] if on else [0]

        cell = render_binding(binding.group(1).strip())
        for n in on_layers:
            combos.setdefault(n, []).append({
                "positions": positions,
                "lg": cell["lg"],
                "title": "%s  —  %s" % (
                    " + ".join(str(p) for p in positions), cell["title"]),
            })
    return combos


# ---------------------------------------------------------------- legends

def mods_legend(code):
    """LS(LC(LA(LGUI))) -> the stacked glyphs, innermost keycode last."""
    glyphs = []
    while True:
        m = re.match(r"^(\w+)\((.*)\)$", code)
        if not m or m.group(1) not in MOD_FN:
            break
        glyphs.append(MOD_FN[m.group(1)])
        code = m.group(2)

    if not glyphs:
        return None

    # A stack of four mods over another mod is hyper; name it rather than
    # printing five glyphs into a 1u cap.
    inner = MOD_NAME.get(code)
    if inner and len(glyphs) == 3:
        return "Hyper"
    tail = LEGEND.get(code, code.title())
    return "".join(glyphs) + ("" if inner else tail)


def keycode_legend(code):
    if code in LEGEND:
        return LEGEND[code]
    stacked = mods_legend(code)
    if stacked:
        return stacked
    if len(code) == 1:
        return code
    if re.match(r"^F\d+$", code):
        return code
    return code.replace("_", " ").title()


def render_binding(binding):
    """One binding string -> the dict the page needs to draw a cap."""
    cell = {"lg": "", "kind": None, "trns": False, "title": binding}

    parts = binding.split()
    behaviour, params = parts[0], parts[1:]

    if binding in TRANSPARENT:
        cell["trns"] = True
        return cell
    if binding in UNBOUND:
        cell["lg"] = "✕"
        cell["kind"] = "none"
        return cell

    name = behaviour[1:]

    if name == "kp" and params:
        cell["lg"] = keycode_legend(params[0])
        return cell

    if name in LAYER_BEHAVIOURS and params:
        verb, kind = LAYER_BEHAVIOURS[name]
        n = int(params[0])
        cell["lg"] = LAYER_META[n]["name"] if n < len(LAYER_META) else "L%d" % n
        cell["kind"] = kind
        cell["layer"] = n
        cell["title"] = "%s  —  %s %d" % (binding, verb, n)
        return cell

    if name in STICKY and params:
        cell["lg"] = keycode_legend(params[0])
        cell["kind"] = "mod"
        cell["title"] = "%s  —  %s %s" % (binding, STICKY[name], cell["lg"])
        return cell

    if name == "bspc_del":
        cell["lg"] = "Bksp"
        cell["kind"] = "mod"
        cell["title"] = "&bspc_del  —  Backspace, or Delete when shifted"
        return cell

    if name == "key_repeat":
        cell["lg"] = "Rept"
        cell["title"] = "&key_repeat  —  resend the last keycode, modifiers and all"
        return cell

    if name == "caps_word":
        cell["lg"] = "CapsWd"
        cell["kind"] = "mod"
        cell["title"] = "&caps_word  —  caps until the next word break"
        return cell

    if name == "bt":
        arg = " ".join(params)
        cell["lg"] = "BT" + params[-1] if arg.startswith("BT_SEL") else "BT clr"
        cell["kind"] = "sys"
        return cell

    if name == "bootloader":
        cell["lg"] = "Boot"
        cell["kind"] = "sys"
        return cell

    if name == "studio_unlock":
        cell["lg"] = "Studio"
        cell["kind"] = "sys"
        return cell

    if name in ("bl", "rgb_ug", "stp"):
        arg = params[-1] if params else ""
        cell["lg"] = {
            "BL_TOG": "Light", "BL_INC": "Light+", "BL_DEC": "Light−",
            "RGB_TOG": "RGB", "STP_BAT": "Batt",
        }.get(arg, arg.title())
        cell["kind"] = "sys"
        return cell

    if name == "macro_ver":
        cell["lg"] = "Ver"
        cell["kind"] = "sys"
        return cell

    cell["lg"] = name.replace("_", " ").title()
    return cell


# ---------------------------------------------------------------- build

def build():
    geometry = load_geometry()
    raw_layers = load_layers()
    combos = load_combos()

    layers = []
    for n, (meta, raw) in enumerate(zip(LAYER_META, raw_layers)):
        cells = [render_binding(b) for b in raw["bindings"]]
        layer = dict(meta)
        layer["n"] = n
        layer["display"] = raw["name"]
        layer["keys"] = cells
        layers.append(layer)

    # A layer-switching key is legended with that layer's own display-name from
    # the keymap ("Kp"), not the longer name this file gives it for the tabs
    # ("Keypad"). The short one is what fits on a 1u cap, and it is data rather
    # than a second opinion.
    for layer in layers:
        for cell in layer["keys"]:
            if "layer" in cell:
                cell["lg"] = raw_layers[cell["layer"]]["name"]

    # A transparent key falls through to base, so draw it with the base legend
    # greyed out. That is what makes "the thumbs mean the same thing on every
    # layer" visible rather than a claim in the README.
    base = layers[0]["keys"]
    for layer in layers[1:]:
        for i, cell in enumerate(layer["keys"]):
            if cell["trns"]:
                cell["lg"] = base[i]["lg"]
                cell["kind"] = base[i]["kind"]
                cell["title"] = "&trans  —  falls through to " + base[i]["title"]

    # Tint every bound key on a non-base layer with that layer's colour, so each
    # layer reads as its own shape rather than a flat wash.
    for layer in layers:
        for cell in layer["keys"]:
            cell["lit"] = layer["n"] != 0 and not cell["trns"] and cell["kind"] != "none"

    # Combos are placed at the midpoint of the two keys that trigger them.
    for layer in layers:
        placed = []
        for combo in combos.get(layer["n"], []):
            pts = [key_centre(geometry[p]) for p in combo["positions"]]
            placed.append({
                "lg": combo["lg"],
                "title": combo["title"],
                "x": sum(p[0] for p in pts) / len(pts),
                "y": sum(p[1] for p in pts) / len(pts),
            })
        layer["combos"] = placed

    width, height = board_extent(geometry)
    return {
        "keys": geometry,
        "width": width,
        "height": height,
        "layers": layers,
    }


def main():
    data = build()

    with open(TEMPLATE) as fh:
        html = fh.read()

    marker = "/*__DATA__*/null"
    if marker not in html:
        sys.exit("marker %s missing from %s" % (marker, TEMPLATE))

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    with open(OUTPUT, "w") as fh:
        fh.write(html.replace(marker, payload))

    n_combos = len(data["layers"][0]["combos"])
    print("wrote %s (%d layers, %d keys, %d combos, %d bytes)"
          % (os.path.relpath(OUTPUT, ROOT), len(data["layers"]),
             len(data["keys"]), n_combos, os.path.getsize(OUTPUT)))


if __name__ == "__main__":
    main()
