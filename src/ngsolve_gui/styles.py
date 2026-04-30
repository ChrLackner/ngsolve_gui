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
        padding="12px 16px 8px",
    )
)
section_content = css.add(Style(padding="8px 12px"))
section_border = css.add(Style(border_bottom="1px solid #eee"))
