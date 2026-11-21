# Working on Outback

## Build from source

You need `git`, `make`, `python3` (3.11 or later, for `tomllib`) and `zip`.

```bash
git clone https://github.com/robjhyndman/outback.git
cd outback
make install                    # Positron
make install EDITOR_CLI=code    # VS Code, or another VS Code-based editor's command
```

Then run **Developer: Reload Window**.
Positron runs the installed copy of the extension, so run `make install` and reload the window after every edit, and after every `git pull`.

| Command               | What it does                                                         |
| ---                   | ---                                                                  |
| `make install`        | Build and install into Positron (`EDITOR_CLI=code` for VS Code)      |
| `make package`        | Build `build/outback-<version>.vsix` without installing it          |
| `make theme`          | Rebuild `themes/outback.json` and `extras/` from the sources         |
| `make check`          | Fail if any generated file is out of date                            |
| `make install-extras` | Symlink the `extras/` themes into place and rebuild bat's cache      |
| `make install-zen`    | Symlink the Zen theme into Zen's default profile (run by `install-extras`) |
| `make clean`          | Remove `build/`                                                      |

## How the theme is built

Every Outback colour is named once, in `palette.toml`: hues such as ochre `#ee7a3c`, spinifex `#ffc852` and eucalyptus `#abc4b8`, and greys from night `#1a1513` to ghost gum `#fff2f0`.
`src/outback.json` is the theme with colours written by name: `"$ochre"`, or `"$ochre/59"` for ochre with alpha `59` (hex).
`make theme` (run by `make package` and `make install`) builds `themes/outback.json` from the two, and then `extras/` from that, so don't edit those files by hand.
`make check` fails if any of them is out of date; GitHub runs it on every push and pull request.
The build also fails on a name that isn't in the palette, a palette colour the theme never uses, or a raw hex colour in `src/outback.json`.

## Change a colour

- **Everywhere it's used:** change its hex value in `palette.toml`.
- **Syntax colours:** edit the rules at the end of `tokenColors` in `src/outback.json`.
  To find the scope for some text, put the cursor on it and run **Developer: Inspect Editor Tokens and Scopes**.
- **Editor colours:** edit `colors` in the same file.
  For example, `editorBracketHighlight.foreground1` sets the outermost bracket colour.
- **A new colour:** add it to `palette.toml` first, then refer to it by name.

Syntax rules match scopes, so the operator and keyword colours apply in every language.
Other `keyword.control` scopes, such as shortcode markers, are also mulla-mulla.

## Grammar additions

Two small grammars in `syntaxes/` add scopes for heading labels and hidden content, and the theme colours those scopes.

### R Markdown

Some extensions (such as panache) register `.Rmd` files as the `rmarkdown` language without a grammar.
`syntaxes/rmarkdown.tmLanguage.json` gives that language a grammar, `text.html.rmarkdown`, that includes the Quarto grammar, so R Markdown files get the same scopes as Quarto files.
Its `embeddedLanguages` in `package.json` copy the Quarto extension's, and both grammar additions below are also injected into it.

### Heading labels

The Quarto grammar treats `{#sec-intro}` as part of the heading text.
`syntaxes/heading-attributes.injection.json` gives a `{...}` at the end of a heading in Quarto and Markdown files its own scope, `meta.heading-attributes`, and the theme turns off bold for that scope.
Any literal `{...}` at the very end of a heading is treated the same way.

### Hidden content

The Quarto grammar gives every `:::` div the same scope, whatever its class.
`syntaxes/content-hidden.injection.json` gives a div whose attributes include `.content-hidden`, from its opening fence to the matching closing fence, the single scope `meta.content-hidden`, and the theme colours that scope grey.
Everything inside, including headings, maths, links and code chunks, takes that one scope, so it is all grey.
Nested divs inside are handled, including ones that use the same number of colons.

## Other apps

`build.py` also builds the themes in `extras/` from `themes/outback.json` and the palette.
Zed maps Positron's colour keys and TextMate scopes onto its own theme keys, Konsole uses the terminal colours, KDE uses the window and list colours, bat copies the token rules as they are, and eza takes its file colours from the palette.
To try your changes, run `make install-extras` once; the symlinks then pick up each `make theme`.

Zen's `userChrome.css` sets the browser's CSS colour variables from Positron colour keys (the `ZEN_*` tables in `build.py`). Zen sets many of them inline from the workspace gradient, so each value is `!important`. The variable names come from Zen's stylesheets (`zen-styles/zen-theme.css` in `browser/omni.ja`) and change between Zen releases.

Sublime Merge's theme extends its built-in Merge Dark theme and sets Merge Dark's colour variables (`SM_VARS` in `build.py`) to palette colours.
The diffs, commit messages and text fields use a Sublime colour scheme built from the token rules, as bat's is.
Merge Dark's variables are in `Merge Dark.sublime-theme` inside `Packages/Theme - Merge.sublime-package` (a zip) in a Sublime Merge install.
Sublime Merge does not notice changes to the files its symlinks point to, so `make theme` touches the symlinks to make it reload them.

RStudio's editor (Ace) has its own token names, so `RSTUDIO_TOKENS` in `build.py` maps CSS selectors for them to the TextMate scope whose Positron colour each should copy.
Two cases need `:has()`: link text is a `keyword` token, as R's `if` is, so it is picked out by the URL that follows it; and unquoted YAML values are plain text, so they take their colour from a line that has a YAML key.
The token names come from RStudio's mode files (`mode/*_highlight_rules`), bundled in `www/rstudio/*.cache.js` in an RStudio install.

The Quarto and Pandoc theme is light, for rendered documents: `PANDOC` in `build.py` maps Pandoc's token types to TextMate scopes, or to palette colours where the Positron colour doesn't work on a light background, and `darken_to()` lowers each colour's OKLCH lightness, keeping its hue, until it has 4.5:1 contrast on `LIGHT_BG`.
To see which token types a language produces, render a sample and look at the `<span class>` names in the HTML (`fu` is Function, `sc` SpecialChar, and so on).

### Add an app

1. In `build.py`, write a function that returns the new theme file as text.
   Take colours from the Positron theme with `t.color("<colour key>")` and `t.resolve("<scope>", "foreground")`, or from the palette with `pick(palette, "<name>", "<where>")`.
   Start the file with the `NOTE` lines as comments.
2. Add an output path constant next to the others, and add `(path, function(...))` to `outputs` in `main()`.
3. Add a line for the app to the docstring at the top of `build.py`.
4. Add `<app>/<file>:<where the app looks for it>` to `LINKS` in the `Makefile`.
5. Run `make theme`, then `make install-extras`, and check the result in the app.
6. In `README.md`, add the app to the list at the top and give it an install section.
   Add a paragraph on how its theme is mapped to the "Other apps" section above.

## Make a release

The other apps' themes are downloaded from `main`, so pushing updates them.
A release publishes the `.vsix` for Positron and VS Code.

1. Bump `version` in `package.json`.
2. Run `make check`, then `make package`, which builds `build/outback-<version>.vsix`.
3. Commit and push.
4. Publish the release, with the `.vsix` attached:

   ```bash
   v=$(python3 -c "import json; print(json.load(open('package.json'))['version'])")
   gh release create "v$v" "build/outback-$v.vsix" --target main --title "Outback $v" --notes "..."
   ```

The README's install link goes to the latest release, so it picks up the new one.
