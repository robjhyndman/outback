#!/usr/bin/env python3
"""Build the Outback themes for other apps from themes/outback.json and palette.toml.

The Zed theme, Konsole colour scheme, KDE colour scheme and bat (tmTheme) theme map
Positron colour keys and TextMate scopes, so they are generated from the Positron theme.
The RStudio theme maps RStudio's own (Ace) token classes onto TextMate scopes.
The eza theme picks colours by palette name. The Zen userChrome.css sets the
browser's CSS colour variables from Positron colour keys. The Sublime Merge theme
sets Merge Dark's colour variables by palette name, and its colour scheme copies the
token rules. All are written to extras/.

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
EZA_OUT = ROOT / "extras/eza/theme.yml"
RSTUDIO_OUT = ROOT / "extras/rstudio/Outback.rstheme"
ZEN_OUT = ROOT / "extras/zen/userChrome.css"
ZEN_PREFS_OUT = ROOT / "extras/zen/user.js"

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


# eza: theme.yml key -> (palette name, bold). Styles merge with eza's defaults, which
# make some of these bold or underlined, so every entry sets bold and underline.
# Anything not listed keeps eza's default, coloured through the ANSI palette.
SIZE = [f"{part}_{unit}" for part in ("number", "unit") for unit in ("byte", "kilo", "mega", "giga", "huge")]
EZA = {
    "filekinds": {"directory": ("ochre", True), "symlink": ("eucalyptus", False)},
    "symlink_path": ("eucalyptus", False),
    "size": {k: ("saltpan", False) for k in SIZE},
    "date": ("sky", False),
    "file_type": {"build": ("spinifex", False)},  # Makefile, README, ...
}


def eza(palette):
    """eza's theme.yml. eza's ANSI-palette defaults look like a coral reef in Outback."""
    def style(name, bold, where):
        c = pick(palette, name, f"eza {where}")
        b = "true" if bold else "false"
        return f'{{foreground: "{c}", is_bold: {b}, is_underline: false}} # {name}'

    out = [f"# {n}" for n in [NOTE[0].replace("themes/outback.json", "palette.toml"), *NOTE[1:]]]
    for key, val in EZA.items():
        if isinstance(val, tuple):
            out.append(f"{key}: {style(*val, key)}")
        else:
            out.append(f"{key}:")
            out += [f"  {k}: {style(*v, k)}" for k, v in val.items()]
    return "\n".join(out) + "\n"


# RStudio's Ace modes use their own token names, so each rule maps CSS selectors to the
# TextMate scope whose Positron colour and style it should copy. Ace gives each dotted
# part of a token its own class ("constant.numeric.text" -> .ace_constant.ace_numeric.ace_text),
# so the more specific selectors later on override the general ones.
RSTUDIO_TOKENS = [
    ([".ace_keyword", ".ace_meta", ".ace_storage", ".ace_storage.ace_type"], "keyword.control"),
    ([".ace_keyword.ace_operator", ".ace_paren"], "keyword.operator"),
    # Commas and semicolons when "Highlight R function calls" is on.
    ([".ace_punctuation", ".ace_punctuation.ace_keyword.ace_operator"], "punctuation.separator"),
    ([".ace_constant.ace_language", ".ace_constant.ace_numeric", ".ace_constant.ace_character",
      ".ace_support.ace_constant", ".ace_variable.ace_language"], "constant.numeric"),
    ([".ace_constant.ace_language.ace_escape"], "constant.character.escape"),
    ([".ace_string"], "string"),
    ([".ace_string.ace_regexp"], "string.regexp"),
    ([".ace_comment", ".ace_comment.ace_keyword.ace_operator"], "comment"),
    ([".ace_identifier", ".ace_variable"], "variable"),
    ([".ace_entity.ace_name.ace_function", ".ace_identifier.ace_support.ace_function"],
     "entity.name.function"),
    # Package names before :: when "Highlight R function calls" is on.
    ([".ace_support.ace_class", ".ace_support.ace_type", ".ace_entity.ace_name.ace_type",
      ".ace_identifier.ace_support.ace_class"], "entity.name.namespace"),
    ([".ace_entity.ace_other.ace_attribute-name"], "entity.other.attribute-name"),
    ([".ace_entity.ace_name.ace_tag"], "entity.name.tag"),
    ([".ace_meta.ace_tag.ace_punctuation"], "punctuation.definition.tag"),
    # YAML keys, in the front matter and in #| chunk options.
    ([".ace_meta.ace_tag"], "entity.name.tag.yaml"),
    ([".ace_list.ace_markup.ace_keyword.ace_operator"], "punctuation.definition.list.begin.markdown"),
    # Markdown: inline code, including `r ...`; code chunks and front matter fences.
    ([".ace_support.ace_function"], "markup.inline.raw"),
    ([".ace_support.ace_function.ace_codebegin", ".ace_support.ace_function.ace_codeend"],
     "punctuation.definition.quarto"),
    ([".ace_markup.ace_heading"], "punctuation.definition.heading"),
    ([".ace_heading"], "entity.name.section"),
    ([".ace_constant.ace_numeric.ace_text"], "markup.bold"),
    ([".ace_constant.ace_language.ace_boolean.ace_text"], "markup.italic"),
    ([".ace_markup.ace_href"], "markup.underline.link"),
    # Cross-references such as @fig-beer, and citations.
    ([".ace_markup.ace_list"], "keyword.control.import.reference"),
    ([".ace_latex", ".ace_latex.ace_support.ace_function", ".ace_latex.ace_markup.ace_list.ace_string"],
     "markup.math.inline.markdown"),
    ([".ace_string.ace_blockquote"], "markup.quote"),
    ([".ace_constant.ace_hr"], "meta.separator"),
    # Link text is a "keyword" token, as R's `if` is, so pick it out by what follows:
    # the URL in [text](url), or the label in [text][label].
    ([".ace_keyword:has(+ .ace_markup.ace_href)",
      ".ace_keyword:has(+ .ace_constant:not(.ace_language):not(.ace_numeric))"],
     "string.other.link.title"),
    # Quarto ::: divs, which RStudio colours by nesting depth unless that option is off.
    ([f".ace_editor .ace_fenced_div{s}_{i}" for i in range(7) for s in ("", "_text")],
     "markup.heading.div.quarto"),
    # Unquoted YAML values are plain text, so colour the text on a line that has a YAML key.
    ([".ace_line:has(> .ace_meta.ace_tag:not(.ace_xml))"], "string.unquoted.plain.out.yaml"),
]


def css_style(t, scope):
    """CSS declarations for the colour and font style VS Code would give scope."""
    color = (t.resolve(scope, "foreground") or t.color("editor.foreground")).lower()
    fs = (t.resolve(scope, "fontStyle") or "").split()
    out = [f"color: {color}"]
    out.append("font-weight: bold" if "bold" in fs else "font-weight: normal")
    if "italic" in fs:
        out.append("font-style: italic")
    return out


def css_rule(selectors, decls):
    return ",\n".join(selectors) + " {\n" + "".join(f"  {d};\n" for d in decls) + "}"


def xterm256():
    """The standard xterm colours 16-255: a 6x6x6 cube, then 24 greys."""
    levels = [0, 95, 135, 175, 215, 255]
    cube = [f"#{levels[r]:02x}{levels[g]:02x}{levels[b]:02x}"
            for r in range(6) for g in range(6) for b in range(6)]
    return cube + [f"#{8 + 10 * i:02x}" * 3 for i in range(24)]


def rstudio(t, palette):
    """RStudio editor theme (.rstheme): CSS for Ace, RStudio's editor and console."""
    c = t.color
    bg, fg = c("editor.background"), c("editor.foreground")
    line = c("editor.lineHighlightBackground")
    # Code chunks get a faint lift, like Positron's range highlight.
    hl = c("editor.rangeHighlightBackground")
    chunk = mix(bg, hl[:7], int(hl[7:], 16) / 255)
    guide = c("editorIndentGuide.background")

    rules = [
        css_rule([".ace_editor", ".ace_editor_theme .profvis-flamegraph", ".ace_editor_theme"],
                 [f"background-color: {bg}", f"color: {fg}"]),
        css_rule([".ace_gutter"], [f"background: {c('editorGutter.background')}",
                                   f"color: {c('editorLineNumber.foreground')}"]),
        css_rule([".ace_gutter-active-line"], [f"background-color: {line}",
                                               f"color: {c('editorLineNumber.activeForeground')}"]),
        css_rule([".ace_print-margin"], ["width: 1px", f"background: {guide}"]),
        css_rule([".ace_cursor"], [f"color: {c('editorCursor.foreground')}"]),
        css_rule([".ace_marker-layer .ace_selection"], [f"background: {c('editor.selectionBackground')}"]),
        css_rule([".ace_selection.ace_start"], [f"box-shadow: 0 0 3px 0px {bg}", "border-radius: 2px"]),
        css_rule([".ace_marker-layer .ace_step"], [f"background: {c('editor.stackFrameHighlightBackground')}"]),
        css_rule([".ace_marker-layer .ace_bracket"],
                 ["margin: -1px 0 0 -1px", f"border: 1px solid {c('editorBracketMatch.border')}",
                  f"background: {c('editorBracketMatch.background')}"]),
        css_rule([".ace_marker-layer .ace_active-line"], [f"background: {line}"]),
        css_rule([".ace_marker-layer .ace_selected-word"],
                 [f"background: {c('editor.wordHighlightBackground')}", "border: none"]),
        css_rule([".ace_invisible"], [f"color: {c('editorWhitespace.foreground')}"]),
        css_rule([".ace_indent-guide"], [f"background: linear-gradient(to left, {guide} 1px, transparent 1px)"]),
        css_rule([".ace_fold"], [f"background-color: {c('textLink.foreground')}", f"border-color: {fg}"]),
        css_rule([".ace_invalid"], [f"color: {c('errorForeground')}"]),
        css_rule([".ace_invalid.ace_deprecated"], [f"color: {c('errorForeground')}", "text-decoration: line-through"]),
        css_rule([".ace_marker-layer .ace_foreign_line"],
                 ["position: absolute", "z-index: -1", f"background-color: {chunk}"]),
        css_rule([".ace_node-selector"], [f"background-color: {c('focusBorder')}"]),
        css_rule([".ace_comment-highlight"], [f"color: {bg}", f"background-color: {c('editorWarning.foreground')}"]),
        css_rule([".ace_marker-layer .ace_active_debug_line"],
                 ["position: absolute", "z-index: -1", f"background-color: {c('editor.stackFrameHighlightBackground')}"]),
        css_rule([".ace_marker-layer .ace_find_line"],
                 ["position: absolute", "z-index: -1", f"background-color: {c('editor.findMatchHighlightBackground')}"]),
        css_rule([".ace_console_error"], [f"background-color: {mix(bg, c('errorForeground'), 0.12)}"]),
    ]
    rules += [css_rule(sels, css_style(t, scope)) for sels, scope in RSTUDIO_TOKENS]

    # Rainbow parentheses (an RStudio option) cycle through Positron's bracket colours.
    rules += [css_rule([f".ace_editor .ace_paren.ace_paren_color_{i}"],
                       [f"color: {c(f'editorBracketHighlight.foreground{i % 6 + 1}')}"])
              for i in range(7)]
    # Rainbow indent guides and fills (also options), in seven Outback hues.
    hues = [pick(palette, n, "rstudio indent guides")
            for n in ("ochre", "spinifex", "new-growth", "waterhole", "sky", "mulla-mulla", "desert-rose")]
    for i, h in enumerate(hues, 1):
        rules.append(css_rule([f".rstudio_rainbow_indent_guides .ace_line .ace_indent-guide:nth-child(7n+{i})"],
                              [f"background: linear-gradient(to left, {h}bb 1px, transparent 1px, transparent)"]))
    for i, h in enumerate(hues, 1):
        rules.append(css_rule([f".rstudio_rainbow_indent_fills .ace_line .ace_indent-guide:nth-child(7n+{i})"],
                              [f"background: linear-gradient(to left, {h}bb 1px, {h}33 1px, {h}33)"]))

    # Autocompletion popup, like Positron's suggestion widget.
    rules += [
        css_rule([".rstudio-themes-dark-menus .ace_editor.ace_autocomplete"],
                 [f"background: {c('editorWidget.background')}",
                  f"border: solid 1px {c('editorWidget.border')} !important", f"color: {fg}"]),
        css_rule([".rstudio-themes-dark-menus .ace_editor.ace_autocomplete .ace_marker-layer .ace_active-line",
                  ".rstudio-themes-dark-menus .ace_editor.ace_autocomplete .ace_marker-layer .ace_line-hover"],
                 [f"background: {c('editorSuggestWidget.selectedBackground')}", "border: none"]),
        css_rule([".editor_dark.ace_editor_theme a"], [f"color: {c('textLink.foreground')} !important"]),
        # Layer order RStudio adds to every theme, so the margin line shows over chunks.
        css_rule([".ace_layer"], ["z-index: 3"]),
        css_rule([".ace_layer.ace_print-margin-layer"], ["z-index: 2"]),
        css_rule([".ace_layer.ace_marker-layer"], ["z-index: 1"]),
    ]

    # Terminal, as in Positron.
    tbg, tfg, cursor = c("terminal.background"), c("terminal.foreground"), c("terminalCursor.foreground")
    rules += [
        css_rule([".terminal"], [f"background-color: {tbg}", f"color: {tfg}", 'font-feature-settings: "liga" 0',
                                 "position: relative", "user-select: none", "-ms-user-select: none",
                                 "-webkit-user-select: none"]),
        css_rule([".terminal.xterm-cursor-style-block.focus:not(.xterm-cursor-blink-on) .terminal-cursor"],
                 [f"background-color: {cursor}", f"color: {tbg}"]),
        css_rule([".terminal.focus.xterm-cursor-style-bar:not(.xterm-cursor-blink-on) .terminal-cursor::before",
                  ".terminal.focus.xterm-cursor-style-underline:not(.xterm-cursor-blink-on) .terminal-cursor::before"],
                 ["content: ''", "position: absolute", f"background-color: {cursor}"]),
        css_rule([".terminal:not(.focus) .terminal-cursor"], [f"outline: 1px solid {cursor}", "outline-offset: -1px"]),
        css_rule([".terminal .xterm-selection div"],
                 ["position: absolute", f"background-color: {c('terminal.selectionBackground')}"]),
        css_rule([".terminal .xterm-viewport"], [f"background-color: {tbg}", "overflow-y: scroll"]),
    ]
    xterm = [
        f".xtermInvertColor {{ color: {tbg}; }}",
        f".xtermInvertBgColor {{ background-color: {tfg}; }}",
        ".xtermBold { font-weight: bold; }",
        ".xtermBlur { filter: brightness(75%); }",
        ".xtermUnderline { text-decoration: underline; }",
        ".xtermBlink { text-decoration: blink; }",
        ".xtermHidden { visibility: hidden; }",
        ".xtermItalic { font-style: italic; }",
        ".xtermStrike { text-decoration: line-through; }",
    ]
    colours = [c(f"terminal.ansi{n}") for n in ANSI] + [c(f"terminal.ansiBright{n}") for n in ANSI] + xterm256()
    for i, col in enumerate(colours):
        xterm += [f".xtermColor{i} {{ color: {col} !important; }}",
                  f".xtermBgColor{i} {{ background-color: {col}; }}"]

    head = ["/* rs-theme-name: Outback */", "/* rs-theme-is-dark: TRUE */"] + [f"/* {n} */" for n in NOTE]
    return "\n".join(head + rules + xterm) + "\n"


# Zen (a Firefox-based browser) colours its UI with CSS variables, many of which it sets as
# inline styles from the workspace gradient, so every value here is !important to win over
# those. Each table maps a variable to a VS Code key, (key, alpha), or a Raw CSS value.
# Variables Zen derives from these (--zen-colors-*) follow them.
class Raw(str):
    """A CSS value written as is, not a VS Code colour key."""


ZEN_ROOT = {
    "--zen-primary-color": "focusBorder",
    "--zen-branding-dark": "sideBar.background",
    "--zen-branding-bg": "sideBar.background",
    "--zen-branding-bg-reverse": "foreground",
    "--zen-colors-tertiary": "editor.background",
    "--zen-colors-border": "sideBar.border",
    "--zen-colors-input-bg": "input.background",
    "--zen-input-border-color": "input.border",
    "--zen-dialog-background": "editorWidget.background",
    "--zen-urlbar-background": "editorWidget.background",
    "--zen-themed-toolbar-bg-transparent": "sideBar.background",
    "--toolbar-color-scheme": Raw("dark"),
    "--toolbox-textcolor": "foreground",
    "--toolbar-text-color": "foreground",
    "--zen-toolbar-element-bg": "list.hoverBackground",
    "--zen-toolbar-element-bg-hover": ("foreground", "19"),
    "--toolbarbutton-background-color-hover": "list.hoverBackground",
    "--toolbarbutton-background-color-active": ("foreground", "19"),
    "--urlbar-box-hover-bgcolor": "list.hoverBackground",
    "--urlbar-box-active-bgcolor": ("foreground", "19"),
    "--toolbar-field-background-color": "input.background",
    "--toolbar-field-focus-background-color": "input.background",
    "--toolbar-field-border-color": "input.border",
    "--toolbar-field-color": "foreground",
    "--input-background-color": "input.background",
    "--input-border-color": "input.border",
    "--background-color-box": "editorWidget.background",
    "--text-color": "foreground",
    "--text-color-deemphasized": "descriptionForeground",
    "--border-color": "editorWidget.border",
    "--focus-outline-color": "focusBorder",
    "--color-accent-primary": "button.background",
    "--color-accent-primary-hover": "button.hoverBackground",
    "--color-accent-primary-active": "button.background",
    "--button-background-color-primary": "button.background",
    "--button-primary-hover-bgcolor": "button.hoverBackground",
    "--button-primary-active-bgcolor": "button.background",
    "--button-text-color-primary": "button.foreground",
    "--button-primary-color": "button.foreground",
    "--in-content-primary-button-text-color": "button.foreground",
    "--link-color": "textLink.foreground",
    "--link-color-hover": "editorLink.activeForeground",
    "--tab-attention-dot-color": "badge.background",
}

# Menus and panels redefine these on themselves, so they are also set there.
ZEN_PANEL = {
    "--panel-background-color": "menu.background",
    "--panel-text-color": "menu.foreground",
    "--panel-border-color": "menu.border",
    "--arrowpanel-background": "menu.background",
    "--arrowpanel-color": "menu.foreground",
    "--arrowpanel-border-color": "menu.border",
}

# Zen's essentials (pinned tab tiles) set the selected colour on the tab itself.
ZEN_TAB = {
    "--tab-background-color-hover": "list.hoverBackground",
    "--tab-background-color-selected": ("foreground", "19"),
}

# The workspace gradient behind the sidebar and toolbar, set inline on these two elements.
# The -old copies are what Zen fades from when switching workspaces.
ZEN_BACKGROUND = {
    "--zen-main-browser-background": "sideBar.background",
    "--zen-main-browser-background-toolbar": "sideBar.background",
    "--zen-main-browser-background-old": "sideBar.background",
    "--zen-main-browser-background-toolbar-old": "sideBar.background",
    "--zen-grainy-background-opacity": Raw("0"),
}


def zen(t):
    """userChrome.css for Zen: dark only, so it also forces Zen's dark colour scheme."""
    def decls(table):
        return [f"{var}: {spec if isinstance(spec, Raw) else t.color(spec)} !important"
                for var, spec in table.items()]

    rules = [
        css_rule([":root"], ["color-scheme: dark !important", *decls(ZEN_ROOT)]),
        css_rule([":root", "menupopup", "panel"], decls(ZEN_PANEL)),
        css_rule([".tabbrowser-tab"], decls(ZEN_TAB)),
        css_rule([":root", "#zen-browser-background", "#zen-toolbar-background"], decls(ZEN_BACKGROUND)),
        # Context menu highlights otherwise come from the GTK theme.
        css_rule(["menupopup > :is(menu, menuitem)[_moz-menuactive]:not([disabled])"],
                 [f"background-color: {t.color('menu.selectionBackground')} !important",
                  f"color: {t.color('menu.foreground')} !important"]),
        css_rule(["::selection"], [f"background-color: {t.color('editor.selectionBackground')} !important"]),
    ]
    return "\n".join([f"/* {n} */" for n in NOTE] + rules) + "\n"


def zen_prefs():
    """user.js turning on userChrome.css, which Zen ignores by default."""
    return "\n".join([f"// {n}" for n in NOTE] + [
        'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);']) + "\n"


# Sublime Merge colour scheme: global -> VS Code colour key.
SM_GLOBAL = {
    "background": "editor.background",
    "foreground": "editor.foreground",
    "caret": "editorCursor.foreground",
    "line_highlight": "editor.lineHighlightBackground",
    "selection": "editor.selectionBackground",
    "inactive_selection": "editor.selectionHighlightBackground",
    "gutter_foreground": "editorLineNumber.foreground",
    "gutter_foreground_highlight": "editorLineNumber.activeForeground",
    "invisibles": "editorWhitespace.foreground",
    "find_highlight": "editor.findMatchBorder",
    "accent": "focusBorder",
}

# The text-entry widgets (commit summary, search, filters) sit on the input colours.
SM_WIDGET_GLOBAL = {**SM_GLOBAL, "background": "input.background",
                    "line_highlight": "input.background", "selection_border": "input.border"}

# Diff backgrounds: (palette name, alpha). The faint line tint marks a line with
# some changes; the strong .char tint marks the changed words, and also whole added
# or deleted lines. Ochre is darker than new-growth, so it needs more alpha.
SM_DIFF = {
    "diff.inserted": ("new-growth", "14"),
    "diff.inserted.char": ("new-growth", "59"),
    "diff.deleted": ("ochre", "14"),
    "diff.deleted.char": ("ochre", "73"),
}

SM_FONT_STYLES = {"bold", "italic", "underline"}

# Sublime Merge theme variables -> palette name, or (palette name, alpha). The theme
# extends Merge Dark, so these replace its hues and greys; most of its other variables
# are derived from them. The rest are colours Merge Dark writes as literals.
SM_VARS = {
    # Hues
    "red": "ochre",
    "orange": "sunset",
    "yellow": "spinifex",
    "green": "new-growth",
    "teal": "waterhole",
    "blue": "sky",
    "purple": "mulla-mulla",
    "magenta": "desert-rose",
    # Greys: header, side bar and dialogs are night, like Positron's panels;
    # the commit list and diff are charcoal, like its editor.
    "text-heading": "ghost-gum",
    "text": "saltpan",
    "medium_gray-light": "saltpan",
    "medium_gray": "mulga",
    "medium_gray-dark": "ash",
    "dark_gray-lightest": "charcoal",
    "dark_gray-light": "night",
    "dark_gray-medium": "night",
    "dark_gray": "night",
    # Commit graph lanes, and the branch labels that share their colours
    "commit_edge_0": "ochre",
    "commit_edge_1": "sky",
    "commit_edge_2": "mulla-mulla",
    "commit_edge_3": "desert-rose",
    "commit_edge_4": "spinifex",
    "commit_edge_5": "waterhole",
    "commit_annotation_fg_inverted": "night",
    # Despite its name, this is also the selected commit's background.
    "commit_row_bg-hover": ("ochre", "33"),
    # Literals in Merge Dark
    "icon_button_fg": "ghost-gum",
    "disclosure_fg": "ghost-gum",
    "hunk_button_fg": "ghost-gum",
    "preview_fg": "ghost-gum",
    "welcome_bg": "night",
    "repository_tab_bar_bg": "night",
    "toggle_button_bg": "embers",
    "toggle_button_bg-details": "burnt",
    "tool_tip_bg": "embers",
    "tool_tip_fg": "ghost-gum",
    "tool_tip_border": "ash",
    "file_badge_unmerged_fg": "night",
    "tag_ann_bg": ("spinifex", "cc"),
    # Primary buttons (Commit, Stage) are ochre with dark text, as in Positron.
    "highlighted_button_light_bg": "ochre",
    "highlighted_button_dark_bg": "ochre",
    "highlighted_button_light_fg": "night",
    "highlighted_button_dark_fg": "night",
    "radio_selected": "ochre",
    "radio_border-selected": "ochre",
    "checkbox_selected": "ochre",
    "checkbox_border-selected": "ochre",
    "loading_ball_2": "ochre",
    # Literals in the light Merge theme that Merge Dark keeps
    "radio_border-unselected": "mulga",
    "checkbox_border-unselected": "mulga",
    "checkbox-disabled": "ash",
    "hint_fg": "night",
    "info-progress_bar_bg": "burnt",
    "info-progress_bar_fg": "mulga",
}

SM_DIR = ROOT / "extras/sublime-merge"
# Merge reads "<context> - <theme name>.sublime-settings" for each kind of text view.
SM_CONTEXTS = ["Diff", "Commit Message", "File Mode", "Git Output"]


def sublime_json(d):
    return "\n".join([f"// {n}" for n in NOTE] + [json.dumps(d, indent="\t")]) + "\n"


def sublime_merge_scheme(t, palette, name, glob):
    """Sublime colour scheme: VS Code tokenColors as rules, plus the diff backgrounds."""
    rules = []
    for rule in t.token_colors:
        out = {}
        if "name" in rule["settings"]:
            out["name"] = rule["settings"]["name"]
        scope = rule["scope"]
        out["scope"] = scope if isinstance(scope, str) else ", ".join(scope)
        for k in ("foreground", "background"):
            if k in rule["settings"]:
                out[k] = rule["settings"][k].lower()
        if "fontStyle" in rule["settings"]:
            out["font_style"] = " ".join(w for w in rule["settings"]["fontStyle"].split()
                                         if w in SM_FONT_STYLES)
        rules.append(out)
    for scope, (colour, alpha) in SM_DIFF.items():
        rules.append({"scope": scope, "background": pick(palette, colour, scope) + alpha})
    return sublime_json({"name": name, "author": "Rob J Hyndman",
                         "globals": {k: t.color(v) for k, v in glob.items()},
                         "rules": rules})


def sublime_merge_theme(palette):
    def colour(spec, var):
        name, alpha = spec if isinstance(spec, tuple) else (spec, "")
        return pick(palette, name, var) + alpha
    return sublime_json({"extends": "Merge Dark.sublime-theme",
                         "variables": {k: colour(v, k) for k, v in SM_VARS.items()}})


def sublime_merge(t, palette):
    """Files for ~/.config/sublime-merge/Packages/User, keyed by output path."""
    out = {
        SM_DIR / "Outback.sublime-theme": sublime_merge_theme(palette),
        SM_DIR / "Outback.sublime-color-scheme": sublime_merge_scheme(t, palette, "Outback", SM_GLOBAL),
        SM_DIR / "Widget - Outback.hidden-color-scheme":
            sublime_merge_scheme(t, palette, "Outback Widgets", SM_WIDGET_GLOBAL),
        SM_DIR / "Widget - Outback.sublime-settings":
            sublime_json({"color_scheme": "Widget - Outback.hidden-color-scheme", "draw_shadows": False}),
    }
    for c in SM_CONTEXTS:
        out[SM_DIR / f"{c} - Outback.sublime-settings"] = sublime_json(
            {"color_scheme": "Outback.sublime-color-scheme"})
    return out


def main():
    check = "--check" in sys.argv[1:]
    t = Theme(SRC)
    pal = load_palette()
    stale = []
    outputs = ((ZED_OUT, zed(t)), (KONSOLE_OUT, konsole(t)), (KDE_OUT, kde(t, pal)), (BAT_OUT, bat(t)),
               (EZA_OUT, eza(pal)), (RSTUDIO_OUT, rstudio(t, pal)),
               (ZEN_OUT, zen(t)), (ZEN_PREFS_OUT, zen_prefs()),
               *sublime_merge(t, pal).items())
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
