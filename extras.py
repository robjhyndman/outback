#!/usr/bin/env python3
"""Build the Outback themes for other apps from themes/outback.json and palette.toml.

The Zed theme, Konsole colour scheme, KDE colour scheme and bat (tmTheme) theme map
Positron colour keys and TextMate scopes, so they are generated from the Positron theme
and written to extras/.

Usage:
    python3 -I extras.py           # rewrite extras/
    python3 -I extras.py --check   # exit 1 if anything in extras/ is out of date
"""

import json
import plistlib
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "themes/outback.json"
PALETTE = ROOT / "palette.toml"
ZED_OUT = ROOT / "extras/zed/outback.json"
KONSOLE_OUT = ROOT / "extras/konsole/Outback.colorscheme"
KDE_OUT = ROOT / "extras/kde/Outback.colors"
BAT_OUT = ROOT / "extras/bat/Outback.tmTheme"

# Header for the generated files; the Zed theme (JSON) has no room for one.
NOTE = ["Outback: generated from themes/outback.json by extras.py",
        "(https://github.com/robjhyndman/outback). Don't edit by hand; run `make extras`."]

TRANSPARENT = "#00000000"

# Zed UI key -> VS Code colour key, or (VS Code key, alpha), or a literal (TRANSPARENT/None).
UI = {
    "border": "sideBar.border",
    "border.variant": "editorWidget.border",
    "border.focused": "focusBorder",
    "border.selected": "tab.activeBorder",
    "border.transparent": TRANSPARENT,
    "border.disabled": "editorWidget.background",
    "elevated_surface.background": "editorWidget.background",
    "surface.background": "sideBar.background",
    "background": "sideBar.background",
    "element.background": "button.background",
    "element.hover": "button.hoverBackground",
    "element.active": "button.hoverBackground",
    "element.selected": "editorSuggestWidget.selectedBackground",
    "element.disabled": "button.background",
    "drop_target.background": "list.dropBackground",
    "ghost_element.background": TRANSPARENT,
    "ghost_element.hover": "list.hoverBackground",
    # Positron also turns selected list items yellow, which Zed can't, so use a stronger tint.
    "ghost_element.active": ("editor.foreground", "19"),
    "ghost_element.selected": ("editor.foreground", "19"),
    "ghost_element.disabled": TRANSPARENT,
    "text": "foreground",
    "text.muted": "descriptionForeground",
    "text.placeholder": "input.placeholderForeground",
    "text.disabled": "activityBar.inactiveForeground",
    "text.accent": "textLink.foreground",
    "icon": "icon.foreground",
    "icon.muted": "input.placeholderForeground",
    "icon.disabled": "activityBar.inactiveForeground",
    "icon.placeholder": "input.placeholderForeground",
    "icon.accent": "textLink.foreground",
    "status_bar.background": "statusBar.background",
    "title_bar.background": "titleBar.activeBackground",
    "title_bar.inactive_background": "titleBar.inactiveBackground",
    "toolbar.background": "editor.background",
    # Zed has no active-tab underline, so inactive tabs sit on the darker sidebar colour.
    "tab_bar.background": "sideBar.background",
    "tab.inactive_background": "sideBar.background",
    "tab.active_background": "tab.activeBackground",
    "search.match_background": "editor.findMatchHighlightBackground",
    "search.active_match_background": ("editor.findMatchBorder", "4d"),
    "panel.background": "sideBar.background",
    "panel.focused_border": None,
    "pane.focused_border": None,
    "scrollbar.thumb.background": "scrollbarSlider.background",
    "scrollbar.thumb.hover_background": "scrollbarSlider.hoverBackground",
    "scrollbar.thumb.active_background": "scrollbarSlider.activeBackground",
    "scrollbar.thumb.border": TRANSPARENT,
    "scrollbar.track.background": TRANSPARENT,
    "scrollbar.track.border": TRANSPARENT,
    "minimap.thumb.background": "scrollbarSlider.background",
    "minimap.thumb.hover_background": "scrollbarSlider.hoverBackground",
    "minimap.thumb.active_background": "scrollbarSlider.activeBackground",
    "minimap.thumb.border": TRANSPARENT,
    "editor.foreground": "editor.foreground",
    "editor.background": "editor.background",
    "editor.gutter.background": "editorGutter.background",
    "editor.subheader.background": "sideBar.background",
    "editor.active_line.background": "editor.lineHighlightBackground",
    "editor.highlighted_line.background": "editor.rangeHighlightBackground",
    "editor.debugger_active_line.background": "editor.stackFrameHighlightBackground",
    "editor.line_number": "editorLineNumber.foreground",
    "editor.active_line_number": "editorLineNumber.activeForeground",
    "editor.hover_line_number": "descriptionForeground",
    "editor.invisible": "editorWhitespace.foreground",
    "editor.wrap_guide": "editorIndentGuide.background",
    "editor.active_wrap_guide": "editorLineNumber.foreground",
    "editor.indent_guide": "editorIndentGuide.background",
    "editor.indent_guide_active": "editorLineNumber.foreground",
    "editor.document_highlight.read_background": "editor.wordHighlightBackground",
    "editor.document_highlight.write_background": "editor.wordHighlightStrongBackground",
    "editor.document_highlight.bracket_background": ("editorBracketMatch.border", "66"),
    "terminal.background": "terminal.background",
    "terminal.foreground": "terminal.foreground",
    "terminal.bright_foreground": "terminal.foreground",
    "terminal.dim_foreground": "descriptionForeground",
    "link_text.hover": "editorLink.activeForeground",
    "version_control.added": "editorGutter.addedBackground",
    "version_control.modified": "editorGutter.modifiedBackground",
    "version_control.deleted": "editorGutter.deletedBackground",
    "version_control.word_added": ("editorGutter.addedBackground", "33"),
    "version_control.word_deleted": ("editorGutter.deletedBackground", "33"),
    "version_control.conflict_marker.ours": ("editorGutter.addedBackground", "26"),
    "version_control.conflict_marker.theirs": ("editorInfo.foreground", "26"),
}

# Zed status colours; each also gets a faint .background and a solid .border.
STATUS = {
    "conflict": "gitDecoration.conflictingResourceForeground",
    "created": "gitDecoration.addedResourceForeground",
    "deleted": "gitDecoration.deletedResourceForeground",
    "error": "errorForeground",
    "hidden": "gitDecoration.ignoredResourceForeground",
    "hint": "editorHint.foreground",
    "ignored": "gitDecoration.ignoredResourceForeground",
    "info": "editorInfo.foreground",
    "modified": "gitDecoration.modifiedResourceForeground",
    "predictive": "editorGhostText.foreground",
    "renamed": "editorInfo.foreground",
    "success": "gitDecoration.addedResourceForeground",
    "unreachable": "editorGhostText.foreground",
    "warning": "editorWarning.foreground",
}

ANSI = ["Black", "Red", "Green", "Yellow", "Blue", "Magenta", "Cyan", "White"]

# Zed syntax key -> TextMate scope resolved against tokenColors.
# A dict instead gives an explicit colour key and/or style.
SYNTAX = {
    "attribute": "entity.other.attribute-name",
    "boolean": "constant.language",
    "comment": "comment",
    "comment.doc": "comment.block.documentation",
    "constant": "constant",
    "constructor": "meta.instance.constructor",
    "embedded": "source",
    "emphasis": {"style_scope": "markup.italic"},
    "emphasis.strong": {"style_scope": "markup.bold"},
    "enum": "entity.name.type.enum",
    "function": "entity.name.function",
    "hint": {"color": "editorInlayHint.foreground"},
    "keyword": "keyword.control",
    "label": "entity.name.label",
    "link_text": "string.other.link.title",
    "link_uri": "markup.underline.link",
    "namespace": "entity.name.namespace",
    "number": "constant.numeric",
    "operator": "keyword.operator",
    "predictive": {"color": "editorGhostText.foreground", "font_style": "italic"},
    "preproc": "meta.preprocessor",
    "primary": "source",
    "property": "variable.other.property",
    "punctuation": "punctuation",
    "punctuation.bracket": "meta.brace.round",
    "punctuation.delimiter": "punctuation.separator",
    "punctuation.list_marker": "punctuation.definition.list.begin.markdown",
    "punctuation.markup": "punctuation.definition.heading",
    "punctuation.special": "punctuation.section.embedded",
    "selector": "entity.other.attribute-name.class.css",
    "selector.pseudo": "entity.other.attribute-name.pseudo-class.css",
    "string": "string",
    "string.escape": "constant.character.escape",
    "string.regex": "string.regexp",
    "string.special": "constant.other.placeholder",
    "string.special.symbol": "constant.other.symbol",
    "tag": "entity.name.tag",
    "text.literal": "markup.inline.raw",
    "title": "entity.name.section",
    "type": "entity.name.type",
    "variable": "variable",
    "variable.parameter": "variable.parameter",
    "variable.special": "variable.language",
    "variant": "variable.other.enummember",
    "diff.plus": "markup.inserted",
    "diff.minus": "markup.deleted",
}


def die(msg):
    sys.exit(f"extras.py: {msg}")


class Theme:
    def __init__(self, path):
        try:
            d = json.loads(path.read_text())
        except FileNotFoundError:
            die(f"{path} not found; run `make theme` first")
        self.colors = d["colors"]
        self.token_colors = d["tokenColors"]
        # (selector, rule settings, index) for every plain selector (no descendant/space).
        self.rules = []
        for i, rule in enumerate(d["tokenColors"]):
            scopes = rule.get("scope", [])
            if isinstance(scopes, str):
                scopes = scopes.split(",")
            for s in scopes:
                s = s.strip()
                if s and " " not in s:
                    self.rules.append((s, rule["settings"], i))

    def color(self, spec):
        """Resolve a UI spec: VS Code key, (key, alpha), or literal."""
        if spec is None or spec == TRANSPARENT:
            return spec
        key, alpha = spec if isinstance(spec, tuple) else (spec, None)
        if not self.colors.get(key):
            die(f"colour key '{key}' missing from {SRC}")
        c = self.colors[key].lower()
        return c[:7] + alpha if alpha else c

    def resolve(self, scope, attr):
        """VS Code semantics: longest matching selector wins, later rule on a tie."""
        best = None
        for sel, settings, i in self.rules:
            if attr in settings and (scope == sel or scope.startswith(sel + ".")):
                rank = (len(sel), i)
                if best is None or rank > best[0]:
                    best = (rank, settings[attr])
        return best and best[1]


def mix(c, d, t):
    c, d = ([int(x[k:k + 2], 16) for k in (1, 3, 5)] for x in (c, d))
    return "#" + "".join(f"{round(a * (1 - t) + b * t):02x}" for a, b in zip(c, d))


def contrast(c, d):
    """WCAG contrast ratio between two #rrggbb colours."""
    def lum(x):
        ch = [int(x[k:k + 2], 16) / 255 for k in (1, 3, 5)]
        ch = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in ch]
        return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]
    hi, lo = sorted((lum(c), lum(d)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def dim_to(fg, bg, ratio):
    """The least blend of fg towards bg whose contrast on bg is at most ratio."""
    lo, hi = 0.0, 1.0
    for _ in range(30):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if contrast(mix(fg, bg, m), bg) > ratio else (lo, m)
    return mix(fg, bg, hi)


def zed_style(fs):
    """Map a TextMate fontStyle to Zed's font_style / font_weight."""
    fs = (fs or "").split()
    return ("italic" if "italic" in fs else None), (700 if "bold" in fs else None)


def zed(t):
    style = {k: t.color(v) for k, v in UI.items()}
    tbg = t.color("terminal.background")
    for name in ANSI:
        k = name.lower()
        c = t.color(f"terminal.ansi{name}")
        style[f"terminal.ansi.{k}"] = c
        style[f"terminal.ansi.bright_{k}"] = t.color(f"terminal.ansiBright{name}")
        style[f"terminal.ansi.dim_{k}"] = mix(c, tbg, 0.35)
    for k, v in STATUS.items():
        c = t.color(v)
        style[k], style[f"{k}.background"], style[f"{k}.border"] = c, c + "19", c

    others = ["terminal.ansiRed", "terminal.ansiGreen", "terminal.ansiCyan", "terminal.ansiMagenta",
              "terminal.ansiBlue", "terminal.ansiYellow", "editorBracketHighlight.foreground1"]
    style["players"] = [{"cursor": t.color("editorCursor.foreground"),
                         "background": t.color("textLink.foreground"),
                         "selection": t.color("editor.selectionBackground")}]
    style["players"] += [{"cursor": t.color(k), "background": t.color(k), "selection": t.color((k, "26"))}
                         for k in others]
    # Rainbow brackets, shown when Zed's "colorize_brackets" setting is on.
    style["accents"] = [t.color(f"editorBracketHighlight.foreground{i}") for i in range(1, 7)]

    syntax = {}
    for key, spec in SYNTAX.items():
        if isinstance(spec, str):
            # As in VS Code, a scope no rule colours is drawn in the editor foreground.
            color = t.resolve(spec, "foreground") or t.color("editor.foreground")
            fs, fw = zed_style(t.resolve(spec, "fontStyle"))
            syntax[key] = {"color": color.lower(), "font_style": fs, "font_weight": fw}
        else:
            fs, fw = zed_style(t.resolve(spec["style_scope"], "fontStyle") if "style_scope" in spec else None)
            syntax[key] = {"color": t.color(spec["color"]) if "color" in spec else None,
                           "font_style": spec.get("font_style", fs), "font_weight": fw}
    style["syntax"] = syntax

    theme = {
        "$schema": "https://zed.dev/schema/themes/v0.2.0.json",
        "name": "Outback",
        "author": "Rob J Hyndman",
        "themes": [{"name": "Outback", "appearance": "dark", "style": style}],
    }
    return json.dumps(theme, indent=2) + "\n"


def konsole(t):
    def rgb(key):
        c = t.color(key)
        return ",".join(str(int(c[k:k + 2], 16)) for k in (1, 3, 5))

    out = [f"# {n}" for n in NOTE] + [""]
    sections = {"Background": "terminal.background", "Foreground": "terminal.foreground"}
    for i, name in enumerate(ANSI):
        sections[f"Color{i}"] = f"terminal.ansi{name}"
    for sec, key in sorted(sections.items()):
        intense = key.replace("terminal.ansi", "terminal.ansiBright") if sec.startswith("Color") else key
        out += [f"[{sec}]", f"Color={rgb(key)}", "",
                f"[{sec}Faint]", f"Color={rgb(key)}", "",
                f"[{sec}Intense]", f"Color={rgb(intense)}", ""]
    out += ["[General]", "Blur=false", "Description=Outback", "Opacity=1", "Wallpaper="]
    return "\n".join(out) + "\n"


# KDE colour sets: set -> (BackgroundNormal, BackgroundAlternate) as VS Code keys.
# Window is chrome (Dolphin's places panel, toolbars); View is content (the file list).
KDE_SETS = {
    "Window": ("sideBar.background", "titleBar.inactiveBackground"),
    "View": ("editor.background", "list.hoverBackground"),
    "Button": ("input.background", "checkbox.border"),
    "Tooltip": ("editorWidget.background", "menu.background"),
    "Header": ("titleBar.activeBackground", "sideBar.background"),
    "Complementary": ("sideBar.background", "editor.background"),
    # Solid ochre with dark text, like Positron's buttons. Breeze paints item-view
    # selections (Dolphin's file list) at about a third of this over the background, so
    # anything weaker all but disappears there. Alternate is Positron's menu highlight.
    "Selection": ("button.background", "menu.selectionBackground"),
}

# Body text is Positron's foreground dimmed towards the background until it reaches this
# contrast ratio on the file list (View); ghost-gum at full strength is about 15:1.
KDE_TEXT_CONTRAST = 10.0

# Foreground roles shared by every set (Selection overrides Normal).
KDE_FG = {
    "ForegroundNormal": "foreground",
    "ForegroundInactive": "descriptionForeground",
    "ForegroundActive": "list.highlightForeground",
    "ForegroundLink": "textLink.foreground",
    "ForegroundNegative": "errorForeground",
    "ForegroundNeutral": "editorWarning.foreground",
    "ForegroundPositive": "gitDecoration.addedResourceForeground",
}

# Breeze Dark's disabled/inactive effects: KDE derives these states from the colours above.
KDE_EFFECTS = """\
[ColorEffects:Disabled]
Color=56,56,56
ColorAmount=0
ColorEffect=0
ContrastAmount=0.65
ContrastEffect=1
IntensityAmount=0.1
IntensityEffect=2

[ColorEffects:Inactive]
ChangeSelectionColor=true
Color=112,111,110
ColorAmount=0.025
ColorEffect=2
ContrastAmount=0.1
ContrastEffect=2
Enable=false
IntensityAmount=0
IntensityEffect=0
"""


def kde(t, palette):
    """KDE colour scheme (~/.local/share/color-schemes): Dolphin, Plasma and other Qt apps."""
    def rgb(c):
        return ",".join(str(int(c[k:k + 2], 16)) for k in (1, 3, 5))

    def solid(key, over="menu.background"):
        """KDE ignores alpha, so blend a translucent colour onto what it sits on."""
        c = t.color(key)
        return c if len(c) == 7 else mix(t.color(over)[:7], c[:7], int(c[7:], 16) / 255)

    fg = {k: rgb(solid(v)) for k, v in KDE_FG.items()}
    view = solid("editor.background")
    fg["ForegroundNormal"] = rgb(dim_to(solid("foreground"), view, KDE_TEXT_CONTRAST))
    fg["ForegroundVisited"] = rgb(pick(palette, "dusk", "kde visited links"))
    focus = rgb(t.color("focusBorder"))

    out = [f"# {n}" for n in NOTE] + ["", KDE_EFFECTS]
    for name, (bg, alt) in sorted(KDE_SETS.items()):
        out.append(f"[Colors:{name}]")
        out += [f"BackgroundAlternate={rgb(solid(alt))}", f"BackgroundNormal={rgb(solid(bg))}",
                f"DecorationFocus={focus}", f"DecorationHover={focus}"]
        roles = dict(fg, ForegroundNormal=rgb(solid("button.foreground"))) \
            if name == "Selection" else fg
        out += [f"{k}={v}" for k, v in sorted(roles.items())] + [""]
    out += ["[Colors:Header][Inactive]",
            f"BackgroundAlternate={rgb(solid('sideBar.background'))}",
            f"BackgroundNormal={rgb(solid('titleBar.inactiveBackground'))}",
            f"DecorationFocus={focus}", f"DecorationHover={focus}"]
    out += [f"{k}={v}" for k, v in sorted(dict(
        fg, ForegroundNormal=rgb(solid("titleBar.inactiveForeground"))).items())] + [""]
    out += ["[General]", "ColorScheme=Outback", "Name=Outback", "shadeSortColumn=true", "",
            "[KDE]", "contrast=4", "",
            "[WM]",
            f"activeBackground={rgb(solid('titleBar.activeBackground'))}",
            f"activeBlend={rgb(solid('titleBar.activeForeground'))}",
            f"activeForeground={rgb(solid('titleBar.activeForeground'))}",
            f"inactiveBackground={rgb(solid('titleBar.inactiveBackground'))}",
            f"inactiveBlend={rgb(solid('titleBar.inactiveForeground'))}",
            f"inactiveForeground={rgb(solid('titleBar.inactiveForeground'))}"]
    return "\n".join(out) + "\n"


# tmTheme global setting -> VS Code colour key. bat uses gutterForeground for line
# numbers and the grid. lineHighlight (for --highlight-line) is set in bat(): bat
# ignores alpha, and Positron's opaque highlight equals Konsole's background.
BAT_GLOBAL = {
    "background": "editor.background",
    "foreground": "editor.foreground",
    "caret": "editorCursor.foreground",
    "selection": "editor.selectionBackground",
    "gutterForeground": "editorLineNumber.foreground",
    "invisibles": "editorWhitespace.foreground",
    "findHighlight": "editor.findMatchBorder",
}


def bat(t):
    """tmTheme for bat (syntect). VS Code tokenColors are TextMate rules, so copy them all."""
    glob = {k: t.color(v) for k, v in BAT_GLOBAL.items()}
    glob["lineHighlight"] = mix(t.color("terminal.background"), t.color("editor.foreground"), 0.1)
    rules = [{"settings": glob}]
    for rule in t.token_colors:
        settings = {k: v.lower() if k in ("foreground", "background") else v
                    for k, v in rule["settings"].items() if k != "name"}
        # "normal" is VS Code's way of clearing an inherited style; tmTheme uses "".
        if "fontStyle" in settings:
            settings["fontStyle"] = " ".join(w for w in settings["fontStyle"].split() if w != "normal")
        scope = rule["scope"]
        out = {"scope": scope if isinstance(scope, str) else ", ".join(scope), "settings": settings}
        if "name" in rule["settings"]:
            out = {"name": rule["settings"]["name"], **out}
        rules.append(out)
    theme = {"name": "Outback", "author": "Rob J Hyndman",
             "comment": " ".join(NOTE),
             "settings": rules}
    return plistlib.dumps(theme, sort_keys=False).decode()


def load_palette():
    return tomllib.loads(PALETTE.read_text())["colours"]


def pick(palette, name, where):
    if name not in palette:
        die(f"'{name}' ({where}) is not in {PALETTE.name}")
    return palette[name]


def main():
    check = "--check" in sys.argv[1:]
    t = Theme(SRC)
    pal = load_palette()
    stale = []
    outputs = ((ZED_OUT, zed(t)), (KONSOLE_OUT, konsole(t)), (KDE_OUT, kde(t, pal)), (BAT_OUT, bat(t)))
    for path, text in outputs:
        current = path.read_text() if path.exists() else None
        if current == text:
            continue
        stale.append(path.relative_to(ROOT))
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    verb = "out of date" if check else "updated"
    for p in stale:
        print(f"{verb}: {p}")
    if not stale:
        print("extras/ is up to date")
    sys.exit(1 if check and stale else 0)


if __name__ == "__main__":
    main()
