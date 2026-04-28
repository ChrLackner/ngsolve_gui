SIDEBAR_BG = "#f5f7fa"
SIDEBAR_BORDER_COLOR = "#e0e0e0"


def sidebar_style(*, border_side="right", extra=""):
    return (
        f"height: 100%; overflow-y: auto;"
        f" background: {SIDEBAR_BG};"
        f" border-{border_side}: 1px solid {SIDEBAR_BORDER_COLOR};"
        f" {extra}"
    )
