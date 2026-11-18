# Outback

A warm dark theme for Positron and VS Code, with colours inspired by Central Australia: red earth, ochre, spinifex gold and a clear desert sky.
It is built on Positron's default dark theme, with its own palette and extra rules for reading and writing Quarto documents and R code.
Matching themes for Zed, Konsole, KDE Plasma and bat are generated from it (see [Other apps](#other-apps)).

## Colours

| Element                                              | Colour                         |
| ---                                                  | ---                            |
| Heading text                                         | spinifex `#ffc852`, bold       |
| Heading `#` markers and labels such as `{#sec-intro}` | spinifex `#ffc852`, not bold   |
| Strings                                              | spinifex `#ffc852`             |
| Inline code (its backticks are smoke)               | desert rose `#eaa6c6`          |
| Link text in `[text](url)`                           | sunset `#f48d6e`               |
| Link URLs, function names and inserted text          | sage `#8cc496`                 |
| YAML keys and cross-references such as `@fig-beer`   | ochre `#ee7a3c`                |
| Maths, including `$` delimiters                      | eucalyptus `#abc4b8`           |
| `::: {.content-hidden}` divs and comments            | smoke `#736968`                |
| Operators such as `\|>`, `<-` and `+`                | sky `#94c8f0`                  |
| Keywords such as `if`, `for`, `function`          | mulla-mulla `#c9a8f0`          |
| Bold and italic text (their `**` and `*` markers are smoke) | wattle seed `#d9a93c`       |
| Numbers and constants such as `TRUE` and `NULL`      | dusk `#a9a9e9`                 |
| Types, classes and attribute names                   | waterhole `#86daca`            |
| Variables and other text                             | ghost gum `#fff2f0`            |
| Brackets, by nesting level                           | sky, wattle seed, desert rose  |

In the UI, ochre marks buttons, focus, the active tab and errors; badges are spinifex; added lines in diffs and git decorations are new growth `#aeda76`.

The operator and keyword colours apply in every language, not only in Quarto code chunks.
Other `keyword.control` scopes, such as shortcode markers, are also mulla-mulla.

## Install

You need `make`, `python3`, `zip` and the `positron` command.
Node isn't needed, because the Makefile builds the `.vsix` directly.

```bash
make install
```

Then run **Developer: Reload Window**, followed by **Preferences: Color Theme**, and choose **Outback**.

Positron runs the installed copy of the extension, not this checkout, so run `make install` and reload the window after every pull or edit.

To install into another VS Code-based editor:

```bash
make install EDITOR_CLI=code
```

`make package` builds the `.vsix` in `build/` without installing it, and `make clean` removes `build/`.

## Other apps

`extras/` holds Outback for other apps, generated from the Positron theme by `extras.py`:

| App       | File                                 | Where it goes                                  |
| ---       | ---                                  | ---                                            |
| Zed       | `extras/zed/outback.json`            | `~/.config/zed/themes/outback.json`            |
| Konsole   | `extras/konsole/Outback.colorscheme` | `~/.local/share/konsole/Outback.colorscheme`   |
| KDE Plasma (Dolphin and other Qt apps) | `extras/kde/Outback.colors` | `~/.local/share/color-schemes/Outback.colors` |
| bat       | `extras/bat/Outback.tmTheme`         | `~/.config/bat/themes/Outback.tmTheme`         |

To symlink them all into place (and rebuild bat's theme cache):

```bash
make install-extras
```

Because they are symlinks, a `git pull` updates them.
Then pick Outback in each app:

- **Zed:** set `"theme": "Outback"` in `settings.json`, or run **theme selector: toggle**.
- **Konsole:** Settings → Edit Current Profile → Appearance → Outback.
- **KDE Plasma:** `plasma-apply-colorscheme Outback`, or System Settings → Colors.
  Leave the accent colour set to "from colour scheme", as a custom accent overrides the scheme's selection colours.
- **bat:** pass `--theme=Outback`, or put that line in `~/.config/bat/config`.

Zed maps Positron's colour keys and TextMate scopes onto its own theme keys, Konsole uses the terminal colours, KDE uses the window and list colours, and bat copies the token rules as they are.
The mappings are in `extras.py`.
I maintain these because I use them; other apps aren't planned.

## Palette

Every Outback colour is named once, in `palette.toml`: hues such as ochre `#ee7a3c`, spinifex `#ffc852` and eucalyptus `#abc4b8`, and greys from night `#1a1513` to ghost gum `#fff2f0`.
`src/outback.json` is the theme with colours written by name: `"$ochre"`, or `"$ochre/59"` for ochre with alpha `59` (hex).
`make theme` (run by `make package` and `make install`) builds `themes/outback.json` from the two, and then `extras/` from that, so don't edit those files by hand.
`make check` fails if any of them is out of date.
The build also fails on a name that isn't in the palette, a palette colour the theme never uses, or a raw hex colour in `src/outback.json`.

## Change a colour

- **Everywhere it's used:** change its hex value in `palette.toml`.
- **Syntax colours:** edit the rules at the end of `tokenColors` in `src/outback.json`.
  To find the scope for some text, put the cursor on it and run **Developer: Inspect Editor Tokens and Scopes**.
- **Editor colours:** edit `colors` in the same file.
  For example, `editorBracketHighlight.foreground1` sets the outermost bracket colour.
  Keys the theme doesn't set fall back to Positron's defaults.
- **A new colour:** add it to `palette.toml` first, then refer to it by name.

Theme rules can only set the foreground colour and font style, so they can't give inline code a background.

## Heading labels

The Quarto grammar treats `{#sec-intro}` as part of the heading text, so a theme rule alone can't style it separately.
`syntaxes/heading-attributes.injection.json` gives a `{...}` at the end of a heading in Quarto and Markdown files its own scope, `meta.heading-attributes`, and the theme turns off bold for that scope.
Any literal `{...}` at the very end of a heading is treated the same way.

## Hidden content

The Quarto grammar gives every `:::` div the same scope, whatever its class, so a theme rule alone can't grey out hidden content.
`syntaxes/content-hidden.injection.json` gives a div whose attributes include `.content-hidden`, from its opening fence to the matching closing fence, the single scope `meta.content-hidden`, and the theme colours that scope grey.
The contents aren't parsed further, so headings, maths, links and code chunks inside are all grey.
Nested divs inside are handled, including ones that use the same number of colons.

## Licence

Outback's own work is released under the [MIT licence](LICENSE).
Parts of `src/outback.json` (and so of `themes/outback.json`) derive from Positron's Default Positron Dark theme, under the Elastic License 2.0, and from VS Code's Dark Modern, Dark+ and Dark VS themes, under the MIT licence.
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
