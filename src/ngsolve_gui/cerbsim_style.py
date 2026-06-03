"""CerbSIM design system for ngapp.

Layers: raw palette (RAW) -> theme-aware semantic tokens (LIGHT/DARK) ->
spacing/type/etc (SCALE) -> named component classes. Tokens are emitted as CSS
custom properties on :root / [data-theme="dark"]; component classes reference
them via var(--...) so one definition works in both themes.

Usage::

    from . import cerbsim_style as cb
    cb.install(app)                  # call once after App.__init__
    bar.ui_class = cb.app_bar
"""

from ngapp.style import Style, StyleSheet, Theme

__all__ = ["theme", "css", "install", "set_theme", "is_dark", "VIEWPORT_CLEAR", "SECTION_COLORS"]

VIEWPORT_CLEAR = {
    "light": (0.933, 0.945, 0.961),
    "dark": (0.086, 0.106, 0.133),
}

VIEWPORT_TEXT = {
    "light": (0.0, 0.0, 0.0),
    "dark": (0.867, 0.886, 0.914),
}


RAW = {
    # Slate neutrals
    "--slate-50": "#f6f8fa",
    "--slate-100": "#eceff3",
    "--slate-200": "#dde2e9",
    "--slate-300": "#c3cad6",
    "--slate-400": "#9aa4b4",
    "--slate-500": "#6b7689",
    "--slate-600": "#4d5768",
    "--slate-700": "#38414f",
    "--slate-800": "#232a36",
    "--slate-900": "#161b24",
    "--slate-950": "#0d1117",
    "--ink": "#1b222d",  # logo navy
    # Accent blue
    "--blue-50": "#eef4ff",
    "--blue-100": "#d9e6ff",
    "--blue-200": "#b4ccff",
    "--blue-300": "#84a9fb",
    "--blue-400": "#5587f4",
    "--blue-500": "#2f6fe5",  # primary accent
    "--blue-600": "#1f57c9",
    "--blue-700": "#1b46a0",
    "--blue-800": "#1b3c80",
    "--blue-900": "#1a3466",
    # Semantic hues
    "--green-500": "#1f8a5b", "--green-400": "#2faa72", "--green-50": "#e7f6ee",
    "--amber-500": "#c77d12", "--amber-400": "#e0921a", "--amber-50": "#fbf1de",
    "--red-500": "#cf3a3a", "--red-400": "#e25555", "--red-50": "#fdecec",
    "--cyan-500": "#1597a6", "--cyan-400": "#21b3c2", "--cyan-50": "#e4f6f8",
    # Scientific colormaps for field legends
    "--viridis": "linear-gradient(90deg,#440154,#414487,#2a788e,#22a884,#7ad151,#fde725)",
    "--coolwarm": "linear-gradient(90deg,#3b4cc0,#6e90f0,#b4c8ec,#f1ccb6,#e0795c,#b40426)",
    "--cerb-seq": "linear-gradient(90deg,#11161e,#1b3c80,#2f6fe5,#5cc8e8,#dcf3fb)",
}


# Semantic tokens. Reference these in UI; light is the default theme.
LIGHT = {
    "color-scheme": "light",
    # Backgrounds & surfaces
    "--bg": "#ffffff",
    "--bg-subtle": "var(--slate-50)",
    "--bg-muted": "var(--slate-100)",
    "--surface": "#ffffff",
    "--panel": "var(--slate-50)",
    "--panel-header": "var(--slate-100)",
    "--viewport": "#eef1f5",
    "--overlay": "rgba(13,17,23,.45)",
    # Foreground / text
    "--fg": "var(--slate-900)",
    "--fg-muted": "var(--slate-600)",
    "--fg-subtle": "var(--slate-500)",
    "--fg-faint": "var(--slate-400)",
    "--fg-on-accent": "#ffffff",
    # Borders & dividers
    "--border": "var(--slate-200)",
    "--border-strong": "var(--slate-300)",
    "--border-faint": "var(--slate-100)",
    "--ring": "color-mix(in srgb, var(--blue-500) 45%, transparent)",
    # Accent / interactive
    "--accent": "var(--blue-500)",
    "--accent-hover": "var(--blue-600)",
    "--accent-active": "var(--blue-700)",
    "--accent-fg": "#ffffff",
    "--accent-subtle": "var(--blue-50)",
    "--accent-border": "var(--blue-200)",
    "--link": "var(--blue-600)",
    # Semantic states
    "--success": "#1f8a5b", "--success-bg": "var(--green-50)",
    "--warning": "#b56f0e", "--warning-bg": "var(--amber-50)",
    "--danger": "#cf3a3a", "--danger-bg": "var(--red-50)",
    "--info": "#1572a0", "--info-bg": "var(--cyan-50)",
    # Mesh/wireframe motif
    "--mesh-line": "color-mix(in srgb, var(--ink) 70%, transparent)",
    "--mesh-fill": "color-mix(in srgb, var(--blue-500) 12%, transparent)",
}

DARK = {
    "color-scheme": "dark",
    "--bg": "#1f262e",
    "--bg-subtle": "#252d36",
    "--bg-muted": "#333d48",
    "--surface": "#28313a",
    "--panel": "#222a32",
    "--panel-header": "#2c353f",
    "--viewport": "#161b22",
    "--overlay": "rgba(0,0,0,.5)",
    "--fg": "var(--slate-100)",
    "--fg-muted": "#aab3c0",
    "--fg-subtle": "#828d9c",
    "--fg-faint": "#66707e",
    "--fg-on-accent": "var(--slate-950)",
    "--border": "#3a4450",
    "--border-strong": "#4c5765",
    "--border-faint": "#2e3741",
    "--ring": "color-mix(in srgb, var(--blue-400) 55%, transparent)",
    "--accent": "var(--blue-400)",
    "--accent-hover": "var(--blue-300)",
    "--accent-active": "var(--blue-200)",
    "--accent-fg": "var(--slate-950)",
    "--accent-subtle": "color-mix(in srgb, var(--blue-500) 18%, transparent)",
    "--accent-border": "color-mix(in srgb, var(--blue-400) 40%, transparent)",
    "--link": "var(--blue-300)",
    "--success": "#2faa72", "--success-bg": "color-mix(in srgb,#2faa72 16%,transparent)",
    "--warning": "#e0921a", "--warning-bg": "color-mix(in srgb,#e0921a 16%,transparent)",
    "--danger": "#e25555", "--danger-bg": "color-mix(in srgb,#e25555 16%,transparent)",
    "--info": "#21b3c2", "--info-bg": "color-mix(in srgb,#21b3c2 16%,transparent)",
    "--mesh-line": "color-mix(in srgb, var(--blue-300) 60%, transparent)",
    "--mesh-fill": "color-mix(in srgb, var(--blue-400) 14%, transparent)",
}


# Theme-independent scale tokens.
SCALE = {
    # Fonts
    "--font-sans": "'IBM Plex Sans', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
    "--font-mono": "'IBM Plex Mono', ui-monospace, 'SF Mono', 'JetBrains Mono', 'Menlo', monospace",
    # Type scale (base 14px)
    "--t-h1": "1.875rem", "--t-h2": "1.5rem", "--t-h3": "1.1875rem", "--t-h4": "1rem",
    "--t-body": "0.875rem", "--t-small": "0.8125rem", "--t-micro": "0.6875rem",
    "--t-mono": "0.8125rem",
    "--ls-tight": "-0.02em", "--ls-snug": "-0.01em", "--ls-label": "0.06em",
    # Spacing (4px grid)
    "--sp-1": "2px", "--sp-2": "4px", "--sp-3": "8px", "--sp-4": "12px",
    "--sp-5": "16px", "--sp-6": "20px", "--sp-7": "24px", "--sp-8": "32px",
    # Radii
    "--r-xs": "3px", "--r-sm": "4px", "--r-md": "6px", "--r-lg": "8px",
    "--r-pill": "999px",
    # Elevation
    "--shadow-xs": "0 1px 1px rgba(13,17,23,.04), 0 1px 2px rgba(13,17,23,.06)",
    "--shadow-sm": "0 1px 2px rgba(13,17,23,.06), 0 2px 4px rgba(13,17,23,.06)",
    "--shadow-md": "0 2px 4px rgba(13,17,23,.06), 0 6px 16px rgba(13,17,23,.10)",
    "--shadow-pop": "0 12px 32px rgba(13,17,23,.18), 0 4px 10px rgba(13,17,23,.10)",
    # Motion
    "--ease": "cubic-bezier(.2,.6,.2,1)",
    "--dur-1": "90ms", "--dur-2": "140ms", "--dur-3": "220ms",
}


# Per-section accent color for property-panel header left-borders.
SECTION_COLORS = {
    "display": "var(--accent)",
    "colormap": "#9C27B0",
    "colors": "#E91E63",
    "clipping": "var(--warning)",
    "deformation": "var(--success)",
    "vectors": "var(--info)",
    "complex": "#673AB7",
    "selection": "#FFC107",
    "meshing": "#795548",
    "numbers": "var(--fg-subtle)",
}


# Maps the brand onto Quasar's color slots so Quasar components inherit it.
theme = Theme(
    primary="#2f6fe5",
    secondary="#4d5768",
    accent="#1597a6",
    dark="#1b222d",
    positive="#1f8a5b",
    negative="#cf3a3a",
    info="#1572a0",
    warning="#b56f0e",
    border="var(--border)",
)


# Component classes.
css = StyleSheet(prefix="cb")


def _cls(name, **props):
    """Register a named component class and return its CssClass handle."""
    return css.add(Style(**props), name=name)


# Top app bar
app_bar = _cls(
    "cb-app-bar",
    height="60px",
    background="var(--panel-header)",
    color="var(--fg)",
    border_bottom="1px solid var(--border)",
)
brand = _cls("cb-brand", display="flex", align_items="center", padding="0 8px")
brand_wordmark = _cls(
    "cb-brand-wordmark",
    font_family="var(--font-sans)", font_size="var(--t-h4)", font_weight="600",
    letter_spacing="var(--ls-snug)", color="var(--fg)", white_space="nowrap",
)
toolbar = _cls(
    "cb-toolbar", display="flex", align_items="center", gap="2px", color="var(--fg-muted)"
)

# Side panels
_panel = Style(
    height="100%",
    overflow_y="auto",
    background="var(--panel)",
    color="var(--fg)",
)
sidebar_nav = css.add(_panel | Style(border_right="1px solid var(--border)"), name="cb-sidebar-nav")
sidebar_props = css.add(_panel | Style(border_left="1px solid var(--border)"), name="cb-sidebar-props")

# Compact styling for Quasar controls inside the panels.
for _panel_cls in (sidebar_nav, sidebar_props):
    _panel_cls \
        .rule(".q-checkbox", padding="0", min_height="28px") \
        .rule(".q-checkbox__label", font_size="var(--t-small)", line_height="1.4", color="var(--fg)") \
        .rule(".q-field--dense .q-field__control", min_height="32px") \
        .rule(".q-field--dense .q-field__label", font_size="var(--t-micro)", color="var(--fg-subtle)") \
        .rule(".q-field--dense .q-field__native", font_size="var(--t-small)", padding_top="12px",
              font_family="var(--font-mono)", color="var(--fg)") \
        .rule(".q-field--dense .q-field__marginal", height="32px") \
        .rule(".q-slider", margin="4px 0") \
        .rule(".q-expansion-item > .q-expansion-item__container > .q-item",
              padding="8px 12px", min_height="38px", background="var(--bg-subtle)") \
        .rule(".q-expansion-item .q-item__section--avatar", min_width="28px", padding_right="8px") \
        .rule(".q-expansion-item .q-item__section--avatar .q-icon",
              font_size="1.1rem", color="var(--fg-muted)") \
        .rule(".q-btn--dense", font_size="var(--t-small)")

hidden = _cls("cb-hidden", display="none")

# Page layout
page_layout = _cls(
    "cb-page-layout", display="flex", flex_direction="row",
    height="calc(100vh - 60px)", width="100%",
)
flex_fill = _cls("cb-flex-fill", flex="1", height="100%", overflow="hidden")
panel_full = _cls("cb-panel-full", width="100%", height="100%")

# Navigator (model tree)
nav_item = _cls(
    "cb-nav-item",
    border_radius="var(--r-xs)", margin="1px 6px", padding="4px 8px",
    color="var(--fg)",
)
# Pseudo-classes attach with no separating space, so add the selector directly.
css.add_rule(".cb-nav-item:hover", Style(background="var(--bg-muted)"))
nav_item_active = _cls(
    "cb-nav-item-active",
    background="var(--accent-subtle)", color="var(--accent)", font_weight="600",
)
nav_number_hint = _cls(
    "cb-nav-number-hint",
    font_family="var(--font-mono)", font_size="var(--t-micro)",
    color="var(--fg-faint)", min_width="14px", text_align="center",
)
nav_side = _cls("cb-nav-side", min_width="14px", padding_right="0")
nav_group_header = _cls(
    "cb-nav-group-header",
    font_size="var(--t-micro)", font_weight="600", letter_spacing="var(--ls-label)",
    text_transform="uppercase", color="var(--fg-subtle)", padding="12px 16px 4px",
)

# Property panel
prop_title = _cls(
    "cb-prop-title",
    font_size="var(--t-micro)", letter_spacing="var(--ls-label)",
    text_transform="uppercase", font_weight="600", color="var(--fg-subtle)",
    padding="8px 16px 6px", display="flex", align_items="center", gap="8px",
)
prop_title_text = _cls("cb-prop-title-text", flex="1")
section_content = _cls("cb-section-content", padding="6px 12px 10px", color="var(--fg)")
section_border = _cls("cb-section-border", border_bottom="1px solid var(--border)")
section_header = _cls("cb-section-header", font_weight="600", font_size="var(--t-small)")
# Compact header for nested "Advanced" / "More" sub-expanders.
subexpander_header = _cls(
    "cb-subexpander-header",
    font_size="var(--t-small)", color="var(--fg-subtle)", min_height="28px", padding="0",
)

# Text helpers
# Uppercase micro label for section/inspector headers.
label = _cls(
    "cb-label",
    font_size="var(--t-micro)", font_weight="600", letter_spacing="var(--ls-label)",
    text_transform="uppercase", color="var(--fg-subtle)",
)
field_label = _cls(
    "cb-field-label", font_size="var(--t-small)", color="var(--fg-muted)",
)
# Tabular monospaced numerics.
mono = _cls(
    "cb-mono",
    font_family="var(--font-mono)", font_size="var(--t-mono)",
    font_variant_numeric="tabular-nums",
)
muted = _cls("cb-muted", color="var(--fg-muted)")
hint = _cls("cb-hint", color="var(--fg-subtle)")
# Fixed-width axis caption (x / y / z prefixes).
axis_label = _cls(
    "cb-axis-label",
    font_size="var(--t-small)", color="var(--fg-subtle)", min_width="14px",
)

# Layout utilities (compose with Quasar's row/column/items-center/no-wrap).
gap_xs = _cls("cb-gap-xs", gap="var(--sp-2)")   # 4px
gap_sm = _cls("cb-gap-sm", gap="var(--sp-3)")   # 8px
grow = _cls("cb-grow", flex="1", min_width="0")
nowrap = _cls("cb-nowrap", white_space="nowrap")
input_compact = _cls("cb-input-compact", max_width="88px")
input_tiny = _cls("cb-input-tiny", max_width="56px")
avatar_min = _cls("cb-avatar-min", min_width="32px")
overlay_tr = _cls("cb-overlay-tr", position="absolute", top="10px", right="10px")
body_height = _cls("cb-body-height", height="calc(100vh - 60px)")
# Responsive checkbox grid.
toggle_grid = _cls(
    "cb-toggle-grid",
    display="grid", grid_template_columns="repeat(auto-fill, minmax(110px, 1fr))",
)

# System-monitor widget (toolbar stats)
monitor = _cls(
    "cb-monitor",
    display="flex", align_items="center", gap="14px", padding="4px 14px",
    user_select="none", background="var(--bg-subtle)",
    border="1px solid var(--border)", border_radius="var(--r-md)",
)
monitor_label = _cls(
    "cb-monitor-label", font_size="var(--t-micro)", font_weight="600", color="var(--fg-muted)",
)
monitor_value = _cls(
    "cb-monitor-value",
    font_family="var(--font-mono)", font_size="var(--t-micro)",
    font_variant_numeric="tabular-nums", color="var(--fg)",
)
monitor_subvalue = _cls(
    "cb-monitor-subvalue",
    font_family="var(--font-mono)", font_size="10px", color="var(--fg-subtle)",
)
monitor_stat = _cls(
    "cb-monitor-stat",
    display="flex", flex_direction="column", gap="var(--sp-1)", min_width="80px",
)
monitor_stat_header = _cls(
    "cb-monitor-stat-header", display="flex", align_items="baseline", gap="var(--sp-2)",
)
monitor_bar = _cls("cb-monitor-bar", width="100%", height="3px")
monitor_subbar = _cls("cb-monitor-subbar", width="100%", height="2px")

# Floating status pill (loading progress)
status_pill = _cls(
    "cb-status-pill",
    position="fixed", bottom="24px", left="50%", transform="translateX(-50%)",
    z_index="1000", display="flex", flex_direction="column", align_items="stretch",
    background="color-mix(in srgb, var(--surface) 90%, transparent)",
    backdrop_filter="blur(8px)",
    border="1px solid var(--border)", border_radius="var(--r-md)",
    padding="10px 18px 12px", min_width="320px", max_width="480px",
    box_shadow="var(--shadow-pop)", color="var(--fg)", font_size="var(--t-small)",
)
status_track = _cls(
    "cb-status-track",
    height="6px", border_radius="var(--r-sm)", background="var(--bg-muted)",
    margin_top="8px", overflow="hidden",
)
status_fill = _cls(
    "cb-status-fill",
    height="100%", width="0%", border_radius="var(--r-sm)",
    background="var(--accent)", transition="width var(--dur-3) var(--ease)",
)
status_fill_indeterminate = _cls(
    "cb-status-fill-indeterminate",
    height="100%", width="100%", border_radius="var(--r-sm)",
    background="var(--accent)", animation="cb-indeterminate 1.4s ease infinite",
)

# Region-color editor
color_swatch = _cls(
    "cb-color-swatch",
    min_width="22px", max_width="22px", min_height="22px", max_height="22px",
    border_radius="var(--r-sm)", border="1px solid var(--border-strong)", padding="0",
)
region_item_row = _cls(
    "cb-region-item-row", padding="2px 4px 2px 20px", min_height="30px",
)
region_header = _cls(
    "cb-region-header",
    padding="3px 6px", border_radius="var(--r-md)", background="var(--bg-subtle)",
)
region_body = _cls(
    "cb-region-body",
    padding="2px 0", border_left="2px solid var(--border)", margin_left="14px",
)
region_toggle = _cls(
    "cb-region-toggle",
    padding="0", min_height="unset", user_select="none", flex="1",
)

# Floating viewport overlay (pick/hover read-out)
viewport_overlay = _cls(
    "cb-viewport-overlay",
    position="absolute", bottom="8px", right="8px",
    background="color-mix(in srgb, var(--surface) 85%, transparent)",
    backdrop_filter="blur(6px)",
    border="1px solid var(--border)", border_radius="var(--r-md)",
    box_shadow="var(--shadow-md)",
    color="var(--fg)", font_family="var(--font-mono)", font_size="var(--t-mono)",
    padding="5px 12px", pointer_events="none", white_space="pre",
    min_width="340px", transition="opacity var(--dur-2) var(--ease)", z_index="10",
    opacity="0",
)
viewport_overlay_visible = _cls("cb-viewport-overlay-visible", opacity="1")


# Token variables and base typography.
css.add_rule(":root", Style(**RAW, **SCALE, **LIGHT))
css.add_rule('[data-theme="dark"]', Style(**DARK))

css.add_rule("body", Style(
    font_family="var(--font-sans)", font_size="var(--t-body)", line_height="1.55",
    color="var(--fg)", background="var(--bg)",
    font_feature_settings="'cv05' 1, 'ss01' 1",
))
css.add_rule(".cb-h1", Style(
    font_size="var(--t-h1)", font_weight="600", letter_spacing="var(--ls-tight)",
    color="var(--fg)", margin="0",
))
css.add_rule(".cb-h2", Style(
    font_size="var(--t-h2)", font_weight="600", letter_spacing="var(--ls-snug)",
    color="var(--fg)", margin="0",
))
css.add_rule("code, kbd, samp", Style(
    font_family="var(--font-mono)", font_size="var(--t-mono)",
))

css.add_rule(".q-card, .q-menu, .q-dialog__inner > div", Style(
    background="var(--surface)", color="var(--fg)",
))
css.add_rule(".q-separator", Style(background="var(--border)"))
css.add_rule(".q-item__label--header", Style(color="var(--fg-subtle)"))
css.add_rule(
    ".q-field__native, .q-field__input, .q-field__prefix, .q-field__suffix",
    Style(color="var(--fg)"),
)
css.add_rule(".q-field__label", Style(color="var(--fg-subtle)"))
css.add_rule(".q-field__messages", Style(color="var(--fg-subtle)"))
css.add_rule(
    ".q-field--standard .q-field__control:before",
    Style(border_color="var(--border-strong)"),
)
css.add_rule(
    ".q-field--standard .q-field__control:hover:before",
    Style(border_color="var(--fg-subtle)"),
)
css.add_rule(
    ".q-checkbox__label, .q-toggle__label, .q-radio__label",
    Style(color="var(--fg)"),
)
css.add_rule(
    ".q-checkbox__inner--falsy, .q-radio__inner--falsy, .q-toggle__inner--falsy",
    Style(color="var(--fg-subtle)"),
)


_KEYFRAMES = (
    "@keyframes cb-indeterminate{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}"
    "@keyframes cb-spin{to{transform:rotate(360deg)}}"
)

_MEDIA_DARK = (
    '@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){'
    + str(Style(**DARK))
    + "}}"
)


def install(app, default_theme="system"):
    """Load fonts, set the theme, apply brand colors and inject all styles.

    *default_theme* is ``"light"``, ``"dark"`` or ``"system"`` (follow the OS).
    Call once, after ``super().__init__`` of your App.
    """
    theme.apply(app)
    global _active_theme
    resolved = _resolve(default_theme)
    _active_theme = resolved

    def _boot(js):
        pre = js.document.createElement("link")
        pre.rel = "preconnect"
        pre.href = "https://fonts.gstatic.com"
        pre.crossOrigin = "anonymous"
        js.document.head.appendChild(pre)
        font = js.document.createElement("link")
        font.rel = "stylesheet"
        font.href = (
            "https://fonts.googleapis.com/css2?"
            "family=IBM+Plex+Sans:wght@400;500;600;700&"
            "family=IBM+Plex+Mono:wght@400;500;600&display=swap"
        )
        js.document.head.appendChild(font)
        js.document.documentElement.setAttribute("data-theme", resolved)
        kf = js.document.createElement("style")
        kf.textContent = _KEYFRAMES + _MEDIA_DARK
        js.document.head.appendChild(kf)

    app.call_js(_boot)
    css.inject(app)


def set_theme(app, name):
    """Switch the active theme at runtime: ``"light"``, ``"dark"`` or ``"system"``."""
    global _active_theme
    resolved = _resolve(name)
    _active_theme = resolved

    def _set(js):
        js.document.documentElement.setAttribute("data-theme", resolved)

    app.call_js(_set)


def is_dark(js):
    """Whether the dark theme is currently effective, resolving ``"system"``.

    Reads the ``data-theme`` attribute set by :func:`set_theme`/:func:`install`
    and falls back to the OS ``prefers-color-scheme`` for ``"system"``.
    """
    attr = js.document.documentElement.getAttribute("data-theme")
    if attr == "dark":
        return True
    if attr == "light":
        return False
    return bool(js.window.matchMedia("(prefers-color-scheme: dark)").matches)


def detect_os_theme():
    """Best-effort OS appearance: ``"dark"``, ``"light"`` or ``None`` if unknown.

    Desktop browsers launched with an isolated profile often report
    ``prefers-color-scheme: light`` regardless of the OS, so for a local app we
    query the OS directly instead of relying on the frontend media query.
    """
    import sys
    import subprocess

    try:
        if sys.platform == "darwin":
            r = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True, timeout=2,
            )
            return "dark" if "Dark" in r.stdout else "light"
        if sys.platform.startswith("win"):
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if value else "dark"
        r = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True, text=True, timeout=2,
        )
        if r.returncode == 0:
            val = r.stdout.strip().strip("'").lower()
            if "dark" in val:
                return "dark"
            if "light" in val:
                return "light"
        r = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
            capture_output=True, text=True, timeout=2,
        )
        if r.returncode == 0 and "dark" in r.stdout.lower():
            return "dark"
    except Exception:
        pass
    return None


def _resolve(name):
    """Resolve ``"system"`` to a concrete ``"dark"``/``"light"`` via the OS.

    Falls back to ``"system"`` (CSS ``prefers-color-scheme``) if the OS theme
    can't be determined.
    """
    if name == "system":
        return detect_os_theme() or "system"
    return name


_active_theme = "system"


def default_colormap(usersettings):
    """Default field colormap: ``$NGAPP_DEFAULT_COLORMAP`` if set (used to make
    tests deterministic), else the ``default_colormap`` user setting, else
    theme-based — ``rainbow`` in light mode, ``turbo`` in dark mode."""
    import os

    forced = os.environ.get("NGAPP_DEFAULT_COLORMAP")
    if forced:
        return forced
    name = usersettings.get("default_colormap", None)
    if name:
        return name
    return "turbo" if _active_theme == "dark" else "rainbow"
