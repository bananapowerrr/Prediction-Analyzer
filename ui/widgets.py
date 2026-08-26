"""Кастомные переиспользуемые виджеты интерфейса Streamlit.

Содержит стилизованную кнопку и статус-бар, пригодные для повторного
использования в окнах терминала.
"""

import os
import sys

import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ui.theme import load_theme  # noqa: E402


def styled_button(
    label: str,
    *,
    key: str | None = None,
    variant: str = "primary",
    disabled: bool = False,
    use_container_width: bool = False,
    help: str | None = None,
) -> bool:
    """Стилизованная кнопка с вариантами оформления.

    Варианты ``variant``: ``primary``, ``secondary``, ``danger``.
    Возвращает ``True`` при нажатии (как стандартная ``st.button``).
    """
    palette = {
        "primary": ("#2e7d32", "#ffffff"),
        "secondary": ("#1565c0", "#ffffff"),
        "danger": ("#c62828", "#ffffff"),
    }
    bg, fg = palette.get(variant, palette["primary"])

    load_theme()

    if key is not None:
        css = f"""
        <style>
            div[data-testid="stButton"] > button[key="{key}"] {{
                background-color: {bg};
                color: {fg};
                border: none;
                border-radius: 8px;
                padding: 0.5rem 1rem;
                font-weight: 600;
                transition: opacity 0.2s ease;
            }}
            div[data-testid="stButton"] > button[key="{key}"]:hover {{
                opacity: 0.85;
            }}
            div[data-testid="stButton"] > button[key="{key}"]:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
            }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)

    return st.button(
        label,
        key=key,
        disabled=disabled,
        use_container_width=use_container_width,
        help=help,
    )


def status_bar(
    *,
    status: str = "idle",
    message: str = "",
    key: str | None = None,
) -> None:
    """Статус-бар с цветовой индикацией состояния.

    Допустимые значения ``status``: ``idle``, ``running``, ``success``,
    ``warning``, ``error``.
    """
    colors = {
        "idle": ("#9e9e9e", "⚪"),
        "running": ("#1565c0", "🔵"),
        "success": ("#2e7d32", "🟢"),
        "warning": ("#f9a825", "🟡"),
        "error": ("#c62828", "🔴"),
    }
    color, icon = colors.get(status, colors["idle"])

    bar = f"""
    <div style="
        display: flex; align-items: center; gap: 0.5rem;
        padding: 0.5rem 0.75rem; margin: 0.5rem 0;
        background-color: {color}1a; border-left: 4px solid {color};
        border-radius: 4px; color: {color}; font-weight: 600;
    ">
        <span>{icon}</span>
        <span>{message}</span>
    </div>
    """
    st.markdown(bar, unsafe_allow_html=True)
