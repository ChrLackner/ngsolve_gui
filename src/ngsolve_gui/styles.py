"""Centralized design tokens, reusable CSS classes, and composable styles.

Uses ``Style``, ``Theme``, ``StyleSheet``, and ``CssClass`` from :mod:`ngapp.style`.
Call ``css.inject(app)`` once (in ``NGSolveGui.__init__``) to activate all classes.
"""

from ngapp.style import CssClass, Style, StyleSheet, Theme

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
theme = Theme(
    primary="#164d7d",
    secondary="#93B1D4",
    accent="#14B8A6",
    dark="#0F172A",
    positive="#16A34A",
    negative="#DC2626",
    info="#0EA5E9",
    warning="#F59E0B",
    border="#e0e0e0",
    sidebar_bg="#f5f7fa",
    muted="#78909c",
    hint="#94a3b8",
)

# -- Section accent colors (left-border on headers) -------------------------
SECTION_COLORS = {
    "display": "#2196F3",       # blue
    "colormap": "#9C27B0",      # purple
    "colors": "#E91E63",        # pink
    "clipping": "#FF9800",      # orange
    "deformation": "#4CAF50",   # green
    "vectors": "#00BCD4",       # teal
    "complex": "#673AB7",       # deep purple
    "selection": "#FFC107",     # amber
    "meshing": "#795548",       # brown
    "numbers": "#607D8B",       # blue-grey
}

# ---------------------------------------------------------------------------
# StyleSheet — registered classes injected into the DOM once
# ---------------------------------------------------------------------------
css = StyleSheet()

# -- Sidebar ----------------------------------------------------------------
_sidebar_base = Style(height="100%", overflow_y="auto", background=theme.sidebar_bg)

sidebar_nav = css.add(
    _sidebar_base | Style(border_right=theme.border_line())
)
sidebar_props = css.add(
    _sidebar_base | Style(border_left=theme.border_line())
)

# -- Scoped rules: automatic compact styling for ALL widgets inside panel ---
sidebar_props.rule(".q-checkbox", padding="0", min_height="28px") \
             .rule(".q-checkbox__label", font_size="0.82rem", line_height="1.4") \
             .rule(".q-field--dense .q-field__control", min_height="32px") \
             .rule(".q-field--dense .q-field__label", font_size="0.72rem") \
             .rule(".q-field--dense .q-field__native", font_size="0.82rem", padding_top="12px") \
             .rule(".q-field--dense .q-field__marginal", height="32px") \
             .rule(".q-slider", margin="4px 0") \
             .rule(".q-expansion-item > .q-expansion-item__container > .q-item",
                   padding="8px 12px", min_height="38px", background="rgba(0,0,0,0.02)") \
             .rule(".q-expansion-item .q-item__section--avatar", min_width="28px", padding_right="8px") \
             .rule(".q-expansion-item .q-item__section--avatar .q-icon", font_size="1.1rem") \
             .rule(".q-btn--dense", font_size="0.78rem")

hidden = css.add(Style(display="none"))

# -- Page layout ------------------------------------------------------------
page_layout = css.add(
    Style(
        display="flex",
        flex_direction="row",
        height="calc(100vh - 60px)",
        width="100%",
    )
)
flex_fill = css.add(Style(flex="1", height="100%", overflow="hidden"))
panel_full = css.add(Style(width="100%", height="100%"))


# -- Navigator items --------------------------------------------------------
nav_item = css.add(Style(border_radius="6px", margin="1px 6px", padding="4px 8px"))
nav_number_hint = css.add(
    Style(font_size="0.65rem", color="#aaa", min_width="14px", text_align="center")
)
nav_group_header = css.add(
    Style(
        font_size="0.75rem",
        letter_spacing="0.05em",
        text_transform="uppercase",
        padding="12px 16px 4px",
    )
)

# -- Property panel ---------------------------------------------------------
prop_title = css.add(
    Style(
        font_size="0.75rem",
        letter_spacing="0.05em",
        text_transform="uppercase",
        font_weight="700",
        color=theme.muted,
        padding="8px 16px 6px",
        display="flex",
        align_items="center",
        gap="8px",
    )
)
prop_title_text = css.add(Style(flex="1"))
section_content = css.add(Style(padding="6px 12px 10px"))
section_border = css.add(Style(border_bottom="1px solid #ddd"))
