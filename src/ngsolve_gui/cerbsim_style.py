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

__all__ = ["theme", "kb_theme", "css", "install", "set_theme", "is_dark", "VIEWPORT_CLEAR", "SECTION_COLORS"]

VIEWPORT_CLEAR = {
    "light": (0.933, 0.945, 0.961),
    "dark": (0.290, 0.333, 0.400),  # #4a5566 slate
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
    "--fg": "#d3dae3",
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
    "lic": "#00838F",
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


# Theme tokens for the keybinding indicator / help overlay (ngapp.keybindings).
# These need the slots accent/hint/muted/border (different from the Quasar color
# theme above). The keybinding stylesheet is built at import time, so use concrete
# colors that read well on the indicator's dark background in both app themes.
kb_theme = Theme(
    accent="#5587f4",   # brand blue (--blue-400)
    hint="#94a3b8",
    muted="#cbd5e1",
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
    display="flex", align_items="center", gap="6px",
    height="48px", min_height="48px", padding="0 8px 0 12px",
    background="var(--panel-header)",
    color="var(--fg)",
    border_bottom="1px solid var(--border)",
)
brand = _cls(
    "cb-brand",
    display="flex", align_items="center", gap="10px", align_self="stretch",
    padding_right="14px", margin_right="2px",
    border_right="1px solid var(--border)",
)
# Designer template's `.tb-app b` (semibold, tight tracking), a touch larger.
brand_wordmark = _cls(
    "cb-brand-wordmark",
    font_family="var(--font-sans)", font_size="14px", font_weight="600",
    letter_spacing="var(--ls-snug)", color="var(--fg)", white_space="nowrap",
)
toolbar = _cls(
    "cb-toolbar", display="flex", align_items="center", gap="2px", color="var(--fg-muted)"
)
# Toolbar groups + separators (top app bar)
tb_group = _cls("cb-tb-group", display="flex", align_items="center", gap="2px")
tb_sep = _cls(
    "cb-tb-sep", width="1px", height="22px", background="var(--border)", margin="0 4px",
)
# Top-bar icon buttons: softer (muted) like the designer's `.ibtn`, full-strength
# on hover. Danger variant (quit) turns red on hover only.
topbar_icon = _cls("cb-topbar-icon", color="var(--fg-muted)")
css.add_rule(".cb-topbar-icon:hover", Style(color="var(--fg)"))
topbar_icon_danger = _cls("cb-topbar-icon-danger")
css.add_rule(".cb-topbar-icon-danger:hover", Style(color="var(--danger)"))

# ── Dropdown menus (settings) — designer ".menu" ─────────────────────────────
menu_card = _cls(
    "cb-menu", width="286px", background="var(--surface)",
    border="1px solid var(--border)", border_radius="var(--r-md)",
    box_shadow="var(--shadow-pop)", padding="6px",
)
menu_h = _cls(
    "cb-menu-h", font_size="10px", font_weight="600", letter_spacing="0.05em",
    text_transform="uppercase", color="var(--fg-subtle)", padding="6px 8px 4px",
)
menu_row = _cls(
    "cb-menu-row", display="flex", align_items="center", justify_content="space-between",
    gap="12px", padding="6px 8px", min_height="34px",
)
menu_label = _cls("cb-menu-label", font_size="12.5px", color="var(--fg)")
menu_sep = _cls("cb-menu-sep", height="1px", background="var(--border)", margin="5px 6px")
menu_item = _cls(
    "cb-menu-item", display="flex", align_items="center", gap="10px", min_height="32px",
    padding="5px 8px", border_radius="var(--r-sm)", font_size="12.5px",
    color="var(--fg)", cursor="pointer",
)
css.add_rule(".cb-menu-item:hover", Style(background="var(--bg-muted)"))
css.add_rule(".cb-menu-item .q-icon", Style(font_size="15px", color="var(--fg-subtle)"))
menu_item_meta = _cls(
    "cb-menu-item-meta", margin_left="auto", color="var(--fg-subtle)", font_size="11px",
)
# Style Quasar inputs/selects inside the menu as clean bordered boxes.
_M = ".cb-menu "
css.add_rule(_M + ".q-field__control", Style(
    background="var(--surface)", border="1px solid var(--border-strong)",
    border_radius="var(--r-sm)", min_height="28px", height="28px", padding="0 9px"))
css.add_rule(_M + ".q-field__control::before", Style(display="none"))
css.add_rule(_M + ".q-field__control::after", Style(display="none"))
css.add_rule(_M + ".q-field--focused .q-field__control", Style(
    border_color="var(--accent)", box_shadow="0 0 0 2px var(--ring)"))
css.add_rule(_M + ".q-field__native, " + _M + ".q-field__input", Style(
    font_family="var(--font-mono)", font_size="12px", color="var(--fg)", padding="0",
    min_height="28px"))
css.add_rule(_M + ".q-field__append .q-icon", Style(color="var(--fg-subtle)", font_size="18px"))
css.add_rule(_M + ".q-field", Style(max_width="146px"))

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
        .rule(".q-field--dense .q-field__native", font_size="var(--t-small)", padding_top="0",
              font_family="var(--font-mono)", color="var(--fg)") \
        .rule(".q-field--dense .q-field__marginal", height="32px") \
        .rule(".q-slider", margin="4px 0") \
        .rule(".q-expansion-item > .q-expansion-item__container > .q-item",
              padding="8px 12px", min_height="38px", background="var(--bg-subtle)") \
        .rule(".q-expansion-item .q-item__section--avatar", min_width="28px", padding_right="8px") \
        .rule(".q-expansion-item .q-item__section--avatar .q-icon",
              font_size="1.1rem", color="var(--fg-muted)") \
        .rule(".q-btn--dense", font_size="var(--t-small)")

# ── De-Quasar the panel controls: make Quasar inputs/selects/sliders read as
#    the designer's clean bordered ".control" boxes and slim sliders. ──────────
_P = ".cb-sidebar-props "
# Inputs & selects → bordered box, no underline, no floating-label chrome
# (applies to every Quasar field variant inside the panel).
css.add_rule(_P + ".q-field__control", Style(
    background="var(--surface)", border="1px solid var(--border-strong)",
    border_radius="var(--r-sm)", padding="0 9px", min_height="30px", height="30px",
))
css.add_rule(_P + ".q-field__control::before", Style(border="none", display="none"))
css.add_rule(_P + ".q-field__control::after", Style(display="none"))
css.add_rule(_P + ".q-field--focused .q-field__control", Style(
    border_color="var(--accent)", box_shadow="0 0 0 2px var(--ring)"))
css.add_rule(_P + ".q-field__marginal", Style(height="30px"))
css.add_rule(_P + ".q-field__native, " + _P + ".q-field__input", Style(
    color="var(--fg)", font_family="var(--font-mono)", font_size="12px",
    padding="0", line_height="30px"))
css.add_rule(_P + ".q-field__append .q-icon", Style(color="var(--fg-subtle)", font_size="18px"))
css.add_rule(_P + ".q-field--error .q-field__control", Style(border_color="var(--danger)"))
# Sliders → slim track, accent selection, ringed thumb.
css.add_rule(_P + ".q-slider__track", Style(background="var(--bg-muted)"))
css.add_rule(_P + ".q-slider__selection", Style(background="var(--accent)"))
css.add_rule(_P + ".q-slider__thumb", Style(color="var(--accent)"))
# Checkboxes (the few that remain) → compact, accent when checked.
css.add_rule(_P + ".q-checkbox__inner", Style(color="var(--border-strong)", font_size="34px"))
css.add_rule(_P + ".q-checkbox__inner--truthy", Style(color="var(--accent)"))

# Colormap gradient swatch (designer field-summary legend bar). Clicking it
# opens the colormap picker dropdown.
cmap_bar = _cls(
    "cb-cmap-bar",
    height="16px", border_radius="var(--r-xs)", border="1px solid var(--border)",
    cursor="pointer",
)
css.add_rule(".cb-cmap-bar:hover", Style(box_shadow="0 0 0 2px var(--ring)"))

# Colormap picker dropdown (opened from the bar).
cmap_menu = _cls("cb-cmap-menu", padding="4px", min_width="210px", background="var(--surface)")
cmap_opt = _cls(
    "cb-cmap-opt",
    display="flex", align_items="center", gap="9px", height="30px", padding="0 8px",
    border_radius="var(--r-sm)", cursor="pointer",
)
css.add_rule(".cb-cmap-opt:hover", Style(background="var(--bg-muted)"))
css.add_rule(".cb-cmap-opt .q-icon", Style(display="none", color="var(--accent)", font_size="15px"))
cmap_opt_on = _cls("cb-cmap-opt-on", background="var(--accent-subtle)")
css.add_rule(".cb-cmap-opt-on .q-icon", Style(display="flex"))
cmap_opt_name = _cls("cb-cmap-opt-name", flex="1", font_size="12.5px", color="var(--fg)")
css.add_rule(".cb-cmap-opt-on .cb-cmap-opt-name", Style(color="var(--accent)", font_weight="600"))
cmap_swatch = _cls(
    "cb-cmap-swatch",
    width="34px", height="13px", border_radius="2px", border="1px solid var(--border)", flex="none",
)

# Colormap gradients keyed by the app's colormap names (for the preview bar).
COLORMAP_GRADIENTS = {
    "rainbow": "linear-gradient(90deg,#0d3bdd,#00a6e6,#1fc46a,#e9d400,#ff8a00,#e21f1f)",
    "turbo": "linear-gradient(90deg,#30123b,#4669f2,#1ae4b6,#a4fc3c,#fb8022,#7a0403)",
    "viridis": "linear-gradient(90deg,#440154,#414487,#2a788e,#22a884,#7ad151,#fde725)",
    "plasma": "linear-gradient(90deg,#0d0887,#6a00a8,#b12a90,#e16462,#fca636,#f0f921)",
    "cet_l20": "linear-gradient(90deg,#440154,#414487,#2a788e,#22a884,#7ad151,#fde725)",
    "matlab:jet": "linear-gradient(90deg,#00007f,#0000ff,#00ffff,#ffff00,#ff0000,#7f0000)",
    "matplotlib:coolwarm": "linear-gradient(90deg,#3b4cc0,#6e90f0,#b4c8ec,#f1ccb6,#e0795c,#b40426)",
}


def colormap_gradient(name):
    """CSS gradient for a colormap name (falls back to viridis)."""
    return COLORMAP_GRADIENTS.get(name, COLORMAP_GRADIENTS["viridis"])


def colormap_gradient_vertical(name):
    """Vertical (bottom→top) gradient for the in-viewport colorbar legend."""
    return colormap_gradient(name).replace("90deg", "to top", 1)


# In-viewport colorbar legend — top-right corner; click the bar to edit.
vp_legend = _cls(
    "cb-vp-legend",
    position="absolute", top="14px", right="14px", z_index="10",
    width="max-content", min_width="142px", max_width="232px",
    background="color-mix(in srgb, var(--surface) 88%, transparent)",
    backdrop_filter="blur(8px)", border="1px solid var(--border)",
    border_radius="var(--r-md)", padding="9px 11px", box_shadow="var(--shadow-sm)",
)
legend_title = _cls(
    "cb-legend-title", display="flex", align_items="center", margin_bottom="7px",
)
legend_quantity = _cls(
    "cb-legend-quantity", flex="1", font_size="11.5px", font_weight="600", color="var(--fg)",
    overflow="hidden", text_overflow="ellipsis", white_space="nowrap",
)
# Component selector (|u| / ux / uy / uz) sitting beside the legend title.
legend_comp = _cls(
    "cb-legend-comp", display="flex", align_items="center", gap="4px", flex="none",
)
css.add_rule(".cb-legend-comp .cb-seg-btn",
             Style(height="19px", padding="0 5px", font_size="10.5px"))
# Standalone |u| pill (shown beside the component dropdown for >3-component fields).
legend_pill = _cls(
    "cb-legend-pill",
    display="flex", align_items="center", justify_content="center",
    height="19px", padding="0 6px", font_size="10.5px", font_weight="500",
    color="var(--fg-muted)", cursor="pointer", user_select="none",
    border="1px solid var(--border-strong)", border_radius="var(--r-sm)",
    background="var(--surface)", white_space="nowrap", flex="none",
)
css.add_rule(".cb-legend-pill.cb-seg-btn-on", Style(border_color="var(--accent)"))
# The component-number dropdown for >3-component fields.
legend_comp_select = _cls("cb-legend-comp-select", flex="none")
css.add_rule(".cb-legend-comp .cb-legend-comp-select.q-field",
             Style(max_width="46px", min_width="44px"))
# Editable min/max value boxes inside the legend ticks (borderless, mono).
css.add_rule(".cb-vp-legend .q-field__control", Style(
    background="transparent", border="none", min_height="18px", height="18px", padding="0"))
css.add_rule(".cb-vp-legend .q-field__control::before", Style(display="none"))
css.add_rule(".cb-vp-legend .q-field__control::after", Style(display="none"))
css.add_rule(".cb-vp-legend .q-field__native", Style(
    font_family="var(--font-mono)", font_size="11.5px", color="var(--fg)", padding="0",
    min_height="18px", line_height="18px"))
css.add_rule(".cb-vp-legend .q-field__control:hover",
             Style(box_shadow="inset 0 -1px 0 var(--border-strong)"))
css.add_rule(".cb-vp-legend .q-field--focused .q-field__control",
             Style(box_shadow="inset 0 -1px 0 var(--accent)"))
css.add_rule(".cb-vp-legend .q-field--focused .q-field__native", Style(color="var(--accent)"))
css.add_rule(".cb-vp-legend .q-field", Style(max_width="62px"))
# Click-to-edit controls popover, dropping below the legend (right-aligned).
legend_pop = _cls(
    "cb-legend-pop",
    position="absolute", top="calc(100% + 6px)", right="0", width="232px", z_index="20",
    background="var(--surface)", border="1px solid var(--border)",
    border_radius="var(--r-md)", box_shadow="var(--shadow-pop)", padding="11px 12px",
    display="flex", flex_direction="column", gap="11px",
)
legend_wrap = _cls("cb-legend-wrap", display="flex", gap="9px")
# The gradient bar is the click target for the colormap picker.
legend_bar = _cls(
    "cb-legend-bar", height="128px", width="16px", border_radius="3px", flex="none",
    border="1px solid var(--border)", cursor="pointer",
)
css.add_rule(".cb-legend-bar:hover", Style(box_shadow="0 0 0 2px var(--ring)"))
legend_ticks = _cls(
    "cb-legend-ticks", display="flex", flex_direction="column",
    justify_content="space-between", height="128px",
    font_family="var(--font-mono)", font_size="11.5px", color="var(--fg-muted)",
)


hidden = _cls("cb-hidden", display="none")

# Page layout
page_layout = _cls(
    "cb-page-layout", display="flex", flex_direction="row",
    height="calc(100vh - 60px)", width="100%",
)
flex_fill = _cls("cb-flex-fill", flex="1", height="100%", overflow="hidden")
panel_full = _cls("cb-panel-full", width="100%", height="100%")

# Navigator (grouped object browser)
# Root: a vertical column filling the panel (header / search / scroll).
nav_panel = _cls(
    "cb-nav-panel",
    display="flex", flex_direction="column", height="100%", min_height="0",
    background="var(--panel)", border_right="1px solid var(--border)",
    overflow="hidden",
)
# Shared panel header bar (also used by the property panel title row).
panel_header = _cls(
    "cb-panel-header",
    display="flex", align_items="center", justify_content="space-between",
    height="36px", min_height="36px", padding="0 6px 0 12px", flex="none",
    border_bottom="1px solid var(--border)", background="var(--panel-header)",
)
panel_header_title = _cls(
    "cb-panel-header-title",
    font_size="11px", font_weight="600", letter_spacing="var(--ls-label)",
    text_transform="uppercase", color="var(--fg-muted)",
)
# Scrollable body region of a side panel.
panel_scroll = _cls(
    "cb-panel-scroll", flex="1", min_height="0", overflow_y="auto", overflow_x="hidden",
)
# Search / filter field wrapper (the QInput inside is dense + borderless).
nav_search = _cls(
    "cb-nav-search",
    display="flex", align_items="center", gap="7px",
    margin="8px", padding="0 6px 0 9px", flex="none",
    border="1px solid var(--border-strong)", border_radius="var(--r-sm)",
    background="var(--surface)", color="var(--fg-subtle)",
)
css.add_rule(".cb-nav-search:focus-within", Style(
    border_color="var(--accent)", box_shadow="0 0 0 2px var(--ring)",
))
nav_search.rule(".q-field--dense .q-field__control", min_height="30px", height="30px")
nav_search.rule(".q-field__marginal", height="30px", color="var(--fg-subtle)")
nav_search.rule(".q-field__native", font_family="var(--font-sans)",
                font_size="12.5px", color="var(--fg)", padding="0")

# Group header row (clickable, with caret + icon + name + count badge).
nav_group_row = _cls(
    "cb-nav-group-row",
    display="flex", align_items="center", gap="7px",
    height="26px", padding="0 10px 0 9px", cursor="pointer",
    color="var(--fg-subtle)", user_select="none",
)
css.add_rule(".cb-nav-group-row:hover", Style(color="var(--fg-muted)"))
nav_group_caret = _cls(
    "cb-nav-group-caret",
    display="flex", transition="transform var(--dur-1) var(--ease)",
)
nav_group_caret_collapsed = _cls(
    "cb-nav-group-caret-collapsed", transform="rotate(-90deg)",
)
nav_group_name = _cls(
    "cb-nav-group-name",
    flex="1", font_size="10.5px", font_weight="600", letter_spacing="var(--ls-label)",
    text_transform="uppercase",
)
nav_count_badge = _cls(
    "cb-nav-count-badge",
    font_family="var(--font-mono)", font_size="10px", color="var(--fg-faint)",
    background="var(--bg-muted)", border_radius="var(--r-pill)",
    padding="1px 6px", min_width="18px", text_align="center",
)

nav_item = _cls(
    "cb-nav-item",
    border_radius="var(--r-sm)", margin="0 4px", padding="4px 8px",
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
nav_empty = _cls(
    "cb-nav-empty",
    padding="4px 12px 8px 30px", font_size="11.5px", color="var(--fg-faint)",
    font_style="italic",
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

# ── Property-panel section framework (designer "psec") ───────────────────────
# A custom collapsible section: banded header with a per-section colored icon
# box, a caret (or a switch for "switchable" sections), and a padded body.
psec = _cls("cb-psec", border_top="1px solid var(--border)")
css.add_rule(".cb-psec:first-of-type", Style(border_top="none"))

psec_head = _cls(
    "cb-psec-head",
    display="flex", align_items="center", gap="8px", height="40px",
    padding="0 12px", user_select="none",
    background="var(--panel-header)",
    transition="background var(--dur-1) var(--ease)",
)
css.add_rule(".cb-psec-head:hover", Style(background="var(--bg-muted)"))
# The clickable toggle area (caret + icon + title); actions sit beside it and
# handle their own clicks without opening/closing the section.
psec_head_main = _cls(
    "cb-psec-head-main",
    display="flex", align_items="center", gap="9px", flex="1", min_width="0",
    height="100%", cursor="pointer",
)
# Right-aligned header action buttons (e.g. vector target toggles).
psec_head_actions = _cls(
    "cb-psec-head-actions", display="flex", align_items="center", gap="4px", flex="none",
)
css.add_rule(".cb-psec-head.cb-open", Style(border_bottom="1px solid var(--border)"))

psec_caret = _cls(
    "cb-psec-caret",
    width="13px", height="13px", color="var(--fg-subtle)", display="flex",
    transition="transform var(--dur-1) var(--ease)",
)
css.add_rule(".cb-psec-head.cb-collapsed .cb-psec-caret", Style(transform="rotate(-90deg)"))

psec_ico = _cls(
    "cb-psec-ico",
    width="24px", height="24px", border_radius="var(--r-sm)", flex="none",
    display="flex", align_items="center", justify_content="center",
)
css.add_rule(".cb-psec-ico .q-icon", Style(font_size="15px"))
psec_title = _cls(
    "cb-psec-title", flex="1",
    font_size="12px", font_weight="600", letter_spacing="0.03em",
    text_transform="uppercase", color="var(--fg)",
)
psec_body = _cls(
    "cb-psec-body",
    padding="13px 12px 15px", display="flex", flex_direction="column", gap="11px",
    background="var(--panel)",
)
# Inline disclosure ("More options") inside a section body.
psec_more = _cls(
    "cb-psec-more",
    display="inline-flex", align_items="center", gap="6px", cursor="pointer",
    user_select="none", align_self="flex-start", color="var(--link)",
    font_size="10.5px", font_weight="600", letter_spacing="0.03em",
    text_transform="uppercase",
)
css.add_rule(".cb-psec-more .q-icon", Style(font_size="13px",
             transition="transform var(--dur-1) var(--ease)"))
css.add_rule(".cb-psec-more.cb-collapsed .q-icon", Style(transform="rotate(-90deg)"))

# Header info tooltip icon.
htip = _cls("cb-htip", display="inline-flex", align_items="center", color="var(--fg-faint)")
css.add_rule(".cb-htip:hover", Style(color="var(--accent)"))
css.add_rule(".cb-htip .q-icon", Style(font_size="13px"))


def sico_style(key=None, muted=False):
    """Inline style for a section's icon box (uniform accent, designer look)."""
    if muted:
        return "background: var(--bg-muted); color: var(--fg-subtle);"
    return "background: var(--accent-subtle); color: var(--accent);"


# Object identity card (icon + name + type) under the PROPERTIES header.
prop_identity = _cls(
    "cb-prop-identity",
    display="flex", align_items="center", gap="11px", padding="14px 16px 12px",
)
prop_identity_ico = _cls(
    "cb-prop-identity-ico",
    width="34px", height="34px", border_radius="var(--r-md)", flex="none",
    display="flex", align_items="center", justify_content="center",
    background="var(--accent-subtle)", color="var(--accent)",
)
css.add_rule(".cb-prop-identity-ico .q-icon", Style(font_size="20px"))
prop_identity_name = _cls(
    "cb-prop-identity-name",
    font_size="14px", font_weight="600", color="var(--fg)", line_height="1.2",
    overflow="hidden", text_overflow="ellipsis", white_space="nowrap",
)
prop_identity_sub = _cls(
    "cb-prop-identity-sub",
    font_size="10px", font_weight="600", letter_spacing="0.06em",
    text_transform="uppercase", color="var(--fg-subtle)", margin_top="2px",
)
# Cross-reference link row ("Open as mesh" / "Open geometry").
xref_row = _cls(
    "cb-xref-row",
    display="flex", align_items="center", gap="8px", height="32px",
    margin="0 12px 8px", padding="0 11px", border_radius="var(--r-sm)",
    color="var(--accent)", font_size="12.5px", cursor="pointer", user_select="none",
    background="var(--accent-subtle)",
)
css.add_rule(".cb-xref-row:hover", Style(background="var(--accent-border)"))
css.add_rule(".cb-xref-row .q-icon", Style(font_size="15px"))

# Segmented control (e.g. Showing |u| / u_x / …, scale presets).
seg = _cls(
    "cb-seg",
    display="flex", border="1px solid var(--border-strong)",
    border_radius="var(--r-sm)", overflow="hidden",
)
seg_btn = _cls(
    "cb-seg-btn",
    flex="1", display="flex", align_items="center", justify_content="center",
    height="28px", padding="0 8px", font_size="11.5px", font_weight="500",
    color="var(--fg-muted)", cursor="pointer", user_select="none",
    background="var(--surface)", white_space="nowrap",
)
css.add_rule(".cb-seg-btn + .cb-seg-btn", Style(border_left="1px solid var(--border)"))
seg_btn_on = _cls("cb-seg-btn-on", background="var(--accent-subtle)", color="var(--accent)")

# Function field summary (Showing + colorbar legend + range), always visible.
prop_summary = _cls(
    "cb-prop-summary",
    padding="2px 12px 14px", display="flex", flex_direction="column", gap="12px",
    border_bottom="1px solid var(--border)",
)
ps_row = _cls("cb-ps-row", display="flex", align_items="center", gap="10px")
ps_lab = _cls(
    "cb-ps-lab",
    font_size="10px", font_weight="600", letter_spacing="0.05em",
    text_transform="uppercase", color="var(--fg-subtle)", flex="none", min_width="54px",
)
ps_q = _cls("cb-ps-q", font_size="13px", font_weight="600", color="var(--fg)")
ps_scale = _cls(
    "cb-ps-scale",
    display="grid", grid_template_columns="1fr auto 1fr", align_items="center", gap="8px",
)
ps_end = _cls("cb-ps-end", font_family="var(--font-mono)", font_size="11.5px", color="var(--fg)")
ps_end_r = _cls("cb-ps-end-r", text_align="right")
ps_auto = _cls(
    "cb-ps-auto",
    display="inline-flex", align_items="center", gap="5px", height="24px",
    padding="0 10px", cursor="pointer", user_select="none",
    border="1px solid var(--border-strong)", border_radius="var(--r-pill)",
    background="var(--surface)", font_size="11px", color="var(--fg-muted)",
    white_space="nowrap",
)
css.add_rule(".cb-ps-auto .q-icon", Style(font_size="12px"))
ps_auto_on = _cls(
    "cb-ps-auto-on",
    background="var(--accent-subtle)", border_color="var(--accent-border)", color="var(--accent)",
)


# ── Option chips (replace stacked checkboxes) ────────────────────────────────
opt_chips = _cls("cb-opt-chips", display="flex", flex_wrap="wrap", gap="6px")
opt_chip = _cls(
    "cb-opt-chip",
    display="inline-flex", align_items="center", gap="6px", height="30px",
    padding="0 11px", cursor="pointer", user_select="none", white_space="nowrap",
    border="1px solid var(--border-strong)", border_radius="var(--r-sm)",
    background="var(--surface)", font_size="12px", color="var(--fg-muted)",
    transition="all var(--dur-1) var(--ease)",
)
css.add_rule(".cb-opt-chip:hover", Style(background="var(--bg-muted)", color="var(--fg)"))
css.add_rule(".cb-opt-chip .q-icon", Style(font_size="15px", color="var(--fg-subtle)"))
opt_chip_on = _cls(
    "cb-opt-chip-on",
    background="var(--accent-subtle)", border_color="var(--accent-border)",
    color="var(--accent)",
)
css.add_rule(".cb-opt-chip-on .q-icon", Style(color="var(--accent)"))
opt_chip_sm = _cls("cb-opt-chip-sm", height="26px", padding="0 9px", font_size="11.5px")

# ── Field (uppercase label over a control) + grids ───────────────────────────
prop_field = _cls("cb-field", display="flex", flex_direction="column", gap="5px")
prop_flab = _cls(
    "cb-flab",
    font_size="10.5px", font_weight="600", letter_spacing="0.04em",
    text_transform="uppercase", color="var(--fg-subtle)",
)
row2 = _cls("cb-row2", display="grid", grid_template_columns="1fr 1fr", gap="8px")

# ── Custom switch (section header + toggle rows) ─────────────────────────────
prop_switch = _cls(
    "cb-switch",
    width="32px", height="18px", border_radius="999px", flex="none",
    background="var(--border-strong)", position="relative", cursor="pointer",
    transition="background var(--dur-1) var(--ease)",
)
css.add_rule(".cb-switch::after", Style(
    content="''", position="absolute", top="2px", left="2px", width="14px", height="14px",
    border_radius="50%", background="#fff", box_shadow="var(--shadow-xs)",
    transition="transform var(--dur-1) var(--ease)",
))
prop_switch_on = _cls("cb-switch-on", background="var(--accent)")
css.add_rule(".cb-switch-on::after", Style(transform="translateX(14px)"))
prop_toggle = _cls(
    "cb-toggle",
    display="flex", align_items="center", justify_content="space-between",
    gap="10px", font_size="12.5px", color="var(--fg)", min_height="24px",
)

# ── Pick pills (S / F / E / V) ───────────────────────────────────────────────
chk_pill = _cls(
    "cb-chk-pill",
    display="inline-flex", align_items="center", justify_content="center",
    height="28px", min_width="34px", padding="0 11px",
    border="1px solid var(--border-strong)", border_radius="var(--r-pill)",
    font_size="12px", color="var(--fg-muted)", cursor="pointer", user_select="none",
)
chk_pill_on = _cls(
    "cb-chk-pill-on",
    background="var(--accent-subtle)", border_color="var(--accent-border)",
    color="var(--accent)",
)
chk_inline = _cls("cb-chk-inline", display="flex", flex_wrap="wrap", gap="6px")

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

# Quality histogram: a full-height clickable column (so even tiny bars are easy
# to hit); the colored bar sits at the bottom inside it.
qhist_col = _cls(
    "cb-qhist-col",
    flex="1", height="100%", display="flex", align_items="flex-end",
    cursor="pointer", border_radius="2px",
    transition="background var(--dur-1) var(--ease)",
)
css.add_rule(".cb-qhist-col:hover", Style(
    background="color-mix(in srgb, var(--fg) 9%, transparent)"))

# ── Viewport overlays (designer): floating tool dock + inline clipping bar ────
_glass = "color-mix(in srgb, var(--surface) 88%, transparent)"
vp_dock = _cls(
    "cb-vp-dock",
    position="absolute", top="12px", left="50%", transform="translateX(-50%)",
    display="flex", align_items="center", gap="2px", z_index="10",
    background=_glass, backdrop_filter="blur(10px)",
    border="1px solid var(--border)", border_radius="var(--r-md)",
    padding="4px", box_shadow="var(--shadow-md)",
)
vp_tool = _cls(
    "cb-vp-tool",
    width="30px", height="30px", display="flex", align_items="center",
    justify_content="center", border_radius="var(--r-sm)",
    color="var(--fg-muted)", cursor="pointer",
)
css.add_rule(".cb-vp-tool:hover", Style(background="var(--bg-muted)", color="var(--fg)"))
css.add_rule(".cb-vp-tool .q-icon", Style(font_size="18px"))
vp_tool_on = _cls("cb-vp-tool-on", background="var(--accent-subtle)", color="var(--accent)")
vp_sep = _cls("cb-vp-sep", width="1px", height="18px", background="var(--border)", margin="0 3px")

vp_clip = _cls(
    "cb-vp-clip",
    position="absolute", top="54px", left="50%", transform="translateX(-50%)",
    display="flex", align_items="center", gap="10px", z_index="10",
    background="color-mix(in srgb, var(--surface) 92%, transparent)",
    backdrop_filter="blur(10px)", border="1px solid var(--border)",
    border_radius="var(--r-md)", padding="5px 8px 5px 12px",
    box_shadow="var(--shadow-md)", white_space="nowrap",
)
vc_lab = _cls(
    "cb-vc-lab", display="inline-flex", align_items="center", gap="7px",
    font_size="12px", font_weight="600", color="var(--fg)",
)
css.add_rule(".cb-vc-lab .q-icon", Style(font_size="15px", color="var(--accent)"))
vc_offset = _cls(
    "cb-vc-offset", display="flex", align_items="center", gap="8px", padding="0 6px",
    border_left="1px solid var(--border)", border_right="1px solid var(--border)",
)
vc_o_val = _cls(
    "cb-vc-o-val", font_family="var(--font-mono)", font_size="11px",
    color="var(--fg)", min_width="40px", text_align="right",
)
vc_axis = _cls("cb-vc-axis", width="108px")
vc_slider = _cls("cb-vc-slider", width="110px")
# Top-right camera cluster.
vp_cam = _cls(
    "cb-vp-cam",
    position="absolute", top="12px", right="12px", display="flex",
    flex_direction="column", align_items="flex-end", gap="8px", z_index="10",
)
vp_cam_row = _cls(
    "cb-vp-cam-row",
    display="flex", gap="2px", background=_glass, backdrop_filter="blur(10px)",
    border="1px solid var(--border)", border_radius="var(--r-md)", padding="4px",
    box_shadow="var(--shadow-md)",
)
# View-bookmarks popover (custom, anchored under its tool-dock button).
bm_pop = _cls(
    "cb-bm-pop",
    position="absolute", top="calc(100% + 8px)", right="0", width="194px", z_index="20",
    background="var(--surface)", border="1px solid var(--border)",
    border_radius="var(--r-md)", box_shadow="var(--shadow-pop)", padding="5px",
)
bm_menu = _cls("cb-bm-menu", padding="5px", min_width="190px", background="var(--surface)")
bm_title = _cls(
    "cb-bm-title", font_size="10px", font_weight="600", letter_spacing="0.05em",
    text_transform="uppercase", color="var(--fg-subtle)", padding="5px 7px 6px",
)
bm_row = _cls(
    "cb-bm-row", display="flex", align_items="center", gap="8px", height="28px",
    padding="0 7px", border_radius="var(--r-sm)", cursor="pointer",
    font_size="12px", color="var(--fg)",
)
css.add_rule(".cb-bm-row:hover", Style(background="var(--bg-muted)"))
css.add_rule(".cb-bm-row .q-icon", Style(font_size="14px", color="var(--fg-subtle)"))
bm_add = _cls(
    "cb-bm-add", display="flex", align_items="center", gap="7px", height="28px",
    padding="0 7px", border_radius="var(--r-sm)", cursor="pointer", font_size="12px",
    color="var(--accent)", margin_top="2px", border_top="1px solid var(--border-faint)",
)
css.add_rule(".cb-bm-add:hover", Style(background="var(--accent-subtle)"))
css.add_rule(".cb-bm-add .q-icon", Style(font_size="14px"))
bm_empty = _cls(
    "cb-bm-empty", font_size="11.5px", color="var(--fg-faint)", font_style="italic",
    padding="6px 8px",
)

# Line/point probe panel (bottom-left).
vp_probe = _cls(
    "cb-vp-probe",
    position="absolute", left="14px", bottom="14px", width="256px", z_index="10",
    background=_glass, backdrop_filter="blur(8px)", border="1px solid var(--border)",
    border_radius="var(--r-md)", padding="10px 12px 11px", box_shadow="var(--shadow-md)",
    display="flex", flex_direction="column", gap="9px",
)
vp_probe_head = _cls(
    "cb-vp-probe-head", display="flex", align_items="center", gap="7px",
    font_size="11px", font_weight="600", letter_spacing="0.03em",
    text_transform="uppercase", color="var(--accent)",
)
css.add_rule(".cb-vp-probe-head .q-icon", Style(font_size="14px"))
vp_probe_pt = _cls(
    "cb-vp-probe-pt", display="flex", align_items="baseline", justify_content="space-between",
    gap="10px", font_family="var(--font-mono)", font_size="11px", color="var(--fg-muted)",
)
vp_probe_val = _cls("cb-vp-probe-val", color="var(--accent)", font_weight="600", flex="none")
vp_probe_hint = _cls(
    "cb-vp-probe-hint", font_size="11.5px", color="var(--fg-subtle)", line_height="1.45",
)
# Screen-space line/point preview (markers + connecting segment). Children use
# position:fixed at the click's CSS client coords (no devicePixelRatio math).
vp_preview = _cls(
    "cb-vp-preview", position="absolute", top="0", left="0", right="0", bottom="0",
    pointer_events="none", z_index="9",
)
vp_preview_dot = _cls(
    "cb-vp-preview-dot", position="fixed", width="10px", height="10px",
    border_radius="50%", background="var(--accent)", border="2px solid #fff",
    transform="translate(-50%, -50%)", box_shadow="var(--shadow-sm)", z_index="9",
)
vp_preview_line = _cls(
    "cb-vp-preview-line", position="fixed", height="2px",
    background="var(--accent)", transform_origin="left center", z_index="9",
)
# Small delete (×) affordance for a probe point row.
probe_del = _cls(
    "cb-probe-del", display="inline-flex", align_items="center", justify_content="center",
    width="16px", height="16px", border_radius="var(--r-xs)", cursor="pointer",
    color="var(--fg-faint)", flex="none",
)
css.add_rule(".cb-probe-del:hover", Style(color="var(--danger)", background="var(--danger-bg)"))
css.add_rule(".cb-probe-del .q-icon", Style(font_size="13px"))
# Body height = viewport minus top app bar (48px) and bottom status bar (28px).
body_height = _cls("cb-body-height", height="calc(100vh - 76px)")
# Responsive checkbox grid.
toggle_grid = _cls(
    "cb-toggle-grid",
    display="grid", grid_template_columns="repeat(auto-fill, minmax(110px, 1fr))",
)

# System-monitor widget (toolbar stats) — bordered pill with per-meter dividers.
monitor = _cls(
    "cb-monitor",
    display="flex", align_items="stretch", height="32px",
    user_select="none", background="var(--surface)",
    border="1px solid var(--border)", border_radius="var(--r-md)", overflow="hidden",
)
# One meter: icon + body (label/value on top, bars below). Divided by a hairline.
monitor_stat = _cls(
    "cb-monitor-stat",
    display="flex", align_items="center", gap="7px",
    padding="0 10px", min_width="96px",
    border_right="1px solid var(--border-faint)",
)
css.add_rule(".cb-monitor-stat:last-child", Style(border_right="none"))
monitor_icon = _cls(
    "cb-monitor-icon", color="var(--fg-subtle)", display="flex", flex="none",
)
monitor_body = _cls(
    "cb-monitor-body",
    display="flex", flex_direction="column", gap="3px", flex="1", min_width="0",
)
monitor_stat_header = _cls(
    "cb-monitor-stat-header",
    display="flex", justify_content="space-between", align_items="baseline",
    gap="6px", line_height="1",
)
monitor_label = _cls(
    "cb-monitor-label", font_size="9px", font_weight="600",
    letter_spacing="var(--ls-label)", text_transform="uppercase", color="var(--fg-subtle)",
)
monitor_value = _cls(
    "cb-monitor-value",
    font_family="var(--font-mono)", font_size="10.5px",
    font_variant_numeric="tabular-nums", color="var(--fg)",
)
monitor_subvalue = _cls(
    "cb-monitor-subvalue",
    font_family="var(--font-mono)", font_size="10px", color="var(--fg-faint)",
)
monitor_bars = _cls(
    "cb-monitor-bars", display="flex", flex_direction="column", gap="1.5px",
)
monitor_bar = _cls("cb-monitor-bar", width="100%", height="3px")
monitor_subbar = _cls("cb-monitor-subbar", width="100%", height="2px")

# Run-progress bar fill (used inline in the footer status indicator).
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

# Bottom status bar (footer) — object info, stats, mode indicator, ready chip.
statusbar = _cls(
    "cb-statusbar",
    display="flex", align_items="center", height="28px", min_height="28px",
    padding="0 12px", background="var(--panel-header)",
    border_top="1px solid var(--border)",
    font_size="11.5px", color="var(--fg-muted)",
)
status_item = _cls(
    "cb-status-item",
    display="flex", align_items="center", gap="6px",
    padding="0 12px", height="15px", border_right="1px solid var(--border)",
)
css.add_rule(".cb-status-item:first-child", Style(padding_left="0"))
status_num = _cls(
    "cb-status-num", color="var(--fg)", font_family="var(--font-mono)",
    font_variant_numeric="tabular-nums",
)
status_spacer = _cls("cb-status-spacer", flex="1")
status_mode = _cls(
    "cb-status-mode",
    display="flex", align_items="center", gap="5px",
    font_family="var(--font-mono)", font_size="10.5px", color="var(--accent)",
)
status_chip = _cls(
    "cb-status-chip",
    display="inline-flex", align_items="center", gap="6px",
    height="18px", padding="0 9px", border_radius="var(--r-pill)",
    font_size="11px", font_weight="600",
)
status_chip_ready = _cls(
    "cb-status-chip-ready",
    background="var(--success-bg)", color="var(--success-fg)",
)
status_chip_busy = _cls(
    "cb-status-chip-busy",
    background="var(--warning-bg)", color="var(--warning-fg)",
)
status_dot = _cls(
    "cb-status-dot", width="6px", height="6px", border_radius="50%",
)
status_dot_ready = _cls("cb-status-dot-ready", background="var(--success)")
status_dot_busy = _cls("cb-status-dot-busy", background="var(--warning)")
# Inline progress bar embedded in the footer status (busy state).
status_track_inline = _cls(
    "cb-status-track-inline",
    width="96px", height="5px", border_radius="var(--r-sm)",
    background="var(--bg-muted)", overflow="hidden", flex="none",
)
status_text = _cls(
    "cb-status-text",
    max_width="260px", overflow="hidden", text_overflow="ellipsis",
    white_space="nowrap", color="var(--fg)",
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

# Designer pick-info card (hover/click), bottom-right.
vp_pick = _cls(
    "cb-vp-pick",
    position="absolute", right="14px", bottom="14px", min_width="200px", z_index="10",
    font_family="var(--font-mono)", font_size="11px", color="var(--fg-muted)",
    background=_glass, backdrop_filter="blur(8px)", border="1px solid var(--border)",
    border_radius="var(--r-md)", padding="9px 11px", box_shadow="var(--shadow-md)",
    line_height="1.65", pointer_events="none", opacity="0",
    transition="opacity var(--dur-2) var(--ease)",
)
vp_pick_visible = _cls("cb-vp-pick-visible", opacity="1")
pk_h = _cls(
    "cb-pk-h", display="flex", align_items="center", gap="6px", margin_bottom="4px",
    font_family="var(--font-sans)", font_size="11px", font_weight="600",
    letter_spacing="0.03em", text_transform="uppercase", color="var(--accent)",
)
css.add_rule(".cb-pk-h .q-icon", Style(font_size="13px"))
pk_r = _cls("cb-pk-r", display="flex", justify_content="space-between", gap="14px")
pk_v = _cls("cb-pk-v", color="var(--fg)", font_weight="500")
pk_v_accent = _cls("cb-pk-v-accent", color="var(--accent)", font_weight="600")


# Tables (QTable / QMarkupTable) — follow the theme tokens so they look right
# in both light and dark mode (Quasar's defaults are light-only).
for _table in (".q-table", ".q-markup-table"):
    css.add_rule(_table, Style(color="var(--fg)", background="var(--panel)"))
css.add_rule(".q-table__card", Style(color="var(--fg)", background="var(--panel)"))
css.add_rule(".q-table thead th", Style(
    color="var(--fg-muted)", background="var(--panel-header)",
    border_bottom="1px solid var(--border)"))
css.add_rule(".q-table tbody td", Style(
    color="var(--fg)", border_bottom="1px solid var(--border-faint)"))
css.add_rule(".q-table tbody tr:hover td", Style(background="var(--bg-muted)"))
css.add_rule(".q-table__bottom", Style(
    color="var(--fg-muted)", border_top="1px solid var(--border)"))
css.add_rule(".q-table--bordered", Style(border="1px solid var(--border)"))


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
