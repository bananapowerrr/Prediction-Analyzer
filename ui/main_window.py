import os
import sys

import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ui.theme import theme_switcher  # noqa: E402

APP_TITLE = "Desktop Tutorial — Trading Terminal"
DEFAULT_DB = os.environ.get(
    "WORLD_STATE_DB", os.path.join(PROJECT_ROOT, "world_state.db")
)

import logging
from pathlib import Path

def render_sidebar() -> dict:
    """Отрисовывает боковую панель и возвращает выбранные настройки."""
    with st.sidebar:
        st.header("Настройки")

        theme = theme_switcher(key="main_window_theme")
        st.divider()

        db_path = st.text_input("Путь к БД World State", value=DEFAULT_DB)
        auto_refresh = st.checkbox("Авто-обновление", value=True)
        refresh_interval = st.slider("Интервал (сек)", 1, 30, 5)

        if st.button("🔄 Обновить сейчас"):
            st.rerun()

    return {
        "theme": theme,
        "db_path": db_path,
        "auto_refresh": auto_refresh,
        "refresh_interval": refresh_interval,
    }

def render_main_area() -> None:
    """Отрисовывает основную область главного окна."""
    st.subheader("Обзор терминала")
    st.info(
        "Главное окно инициализировано. Подключите источники данных "
        "(World State, Tribunal, Edge, Order Execution) через боковую панель."
    )

    tab_overview, tab_logs = st.tabs(["Сводка", "Логи"])
    with tab_overview:
        st.write("Здесь отображаются сводные метрики терминала.")
    with tab_logs:
        st.write("Здесь отображаются логи событий терминала.")

def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🖥️",
        layout="wide",
    )

    st.title(f"🖥️ {APP_TITLE}")
    try:
        sidebar_settings = render_sidebar()
    except Exception as e:
        logging.error(f"Error rendering sidebar: {e}")
        Path("errors").mkdir(parents=True, exist_ok=True)
        with open("errors/sidebar_error.log", "w") as f:
            f.write(f"Error rendering sidebar: {e}")
        return

    try:
        render_main_area()
    except Exception as e:
        logging.error(f"Error rendering main area: {e}")
        Path("errors").mkdir(parents=True, exist_ok=True)
        with open("errors/main_area_error.log", "w") as f:
            f.write(f"Error rendering main area: {e}")
        return

if __name__ == "__main__":
    main()
