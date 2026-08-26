"""Theme management and switcher for the Streamlit trading terminal UI."""

import json
import os
import sys

import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

THEMES = ["light", "dark"]

THEME_FILE = os.path.join(PROJECT_ROOT, ".ui_theme.json")

DEFAULT_THEME = "light"


def get_available_themes() -> list:
    return list(THEMES)


def load_theme() -> str:
    try:
        with open(THEME_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        theme = data.get("theme")
        if theme in THEMES:
            return theme
    except Exception:
        pass
    return DEFAULT_THEME


def save_theme(theme: str) -> None:
    if theme not in THEMES:
        return
    try:
        with open(THEME_FILE, "w", encoding="utf-8") as fh:
            json.dump({"theme": theme}, fh)
    except Exception:
        pass


def apply_theme(theme: str) -> None:
    """Inject minimal light/dark styling via CSS."""
    if theme == "dark":
        bg, fg, panel = "#0e1117", "#fafafa", "#161b22"
    else:
        bg, fg, panel = "#ffffff", "#0e1117", "#f0f2f6"
    css = f"""
    <style>
        .stApp {{ background-color: {bg}; color: {fg}; }}
        .stApp header, .stApp .css-18e3h3g {{ background-color: {bg}; }}
        .stSidebar, section[data-testid="stSidebar"] {{
            background-color: {panel}; color: {fg};
        }}
        .stDataFrame {{ background-color: {panel}; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def theme_switcher(key: str = "theme_select") -> str:
    """Render a theme selector in the sidebar and persist the choice.

    Returns the currently active theme.
    """
    current_theme = load_theme()
    apply_theme(current_theme)

    theme = st.selectbox(
        "Тема оформления",
        THEMES,
        index=THEMES.index(current_theme),
        key=key,
    )
    if theme != current_theme:
        save_theme(theme)
        apply_theme(theme)
        try:
            st.toast(f"Тема оформления изменена: {theme}", icon="🎨")
        except Exception:
            pass
        st.rerun()
    return theme
