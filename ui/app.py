import ast
import json
import os
import sys
import time
from datetime import datetime

import pandas as pd
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from state_manager import StateManager

st.set_page_config(
    page_title="Desktop Tutorial — Trading Terminal Monitor",
    page_icon="📊",
    layout="wide",
)

MARKET_EVENT = "market_event"
TRIBUNAL = "tribunal"
EDGE = "edge"
ORDER = "order"

DEFAULT_DB = os.environ.get(
    "WORLD_STATE_DB", os.path.join(PROJECT_ROOT, "world_state.db")
)


def open_manager(db_path: str):
    return StateManager(db_path)


def parse_payload(raw):
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    text = str(raw)
    try:
        return json.loads(text)
    except Exception:
        pass
    try:
        return ast.literal_eval(text)
    except Exception:
        return {"raw": text}


def load_events(manager, event_type=None, limit=500):
    try:
        rows = manager.get_events(event_type)
    except Exception:
        return []
    if not rows:
        return []
    rows = list(reversed(rows))
    return rows[:limit]


def events_dataframe(events):
    records = []
    for ev in events:
        payload = parse_payload(ev.get("data"))
        if not isinstance(payload, dict):
            payload = {"value": payload}
        row = {
            "id": ev.get("id"),
            "timestamp": ev.get("timestamp"),
            "event_type": ev.get("event_type"),
        }
        row.update(payload)
        records.append(row)
    return pd.DataFrame(records)


def status_color(status: str) -> str:
    s = (status or "").lower()
    if s in ("filled", "executed", "completed", "done"):
        return "🟢"
    if s in ("pending", "open", "working", "submitted"):
        return "🟡"
    if s in ("rejected", "failed", "cancelled", "canceled", "error"):
        return "🔴"
    return "⚪"


def render_market_events(events):
    if not events:
        st.info("Нет рыночных событий в World State. Запустите сканирование или сгенерируйте демо-данные.")
        return
    st.subheader("Текущие рыночные события (World State)")
    df = events_dataframe(events)
    if "timestamp" in df.columns:
        df = df.sort_values("timestamp", ascending=False)
    st.dataframe(df, use_container_width=True, height=360)


def render_tribunal(events):
    st.subheader("Логи дебатов LLM-агентов (Tribunal)")
    if not events:
        st.info("Нет записей дебатов Tribunal.")
        return
    for ev in events:
        payload = parse_payload(ev.get("data"))
        if not isinstance(payload, dict):
            payload = {"raw": payload}
        topic = payload.get("topic") or payload.get("question") or f"Debate #{ev.get('id')}"
        verdict = payload.get("verdict", "—")
        confidence = payload.get("confidence", payload.get("confidence_score", "—"))
        with st.expander(f"⚖️ {topic}  ·  confidence={confidence}", expanded=False):
            agents = payload.get("agents") or payload.get("arguments") or []
            if isinstance(agents, list) and agents:
                for agent in agents:
                    if isinstance(agent, dict):
                        name = agent.get("name", agent.get("agent", "agent"))
                        role = agent.get("role", "")
                        argument = agent.get("argument", agent.get("text", ""))
                        st.markdown(f"**{name}** _{role}_")
                        st.write(argument)
                    else:
                        st.write(agent)
            else:
                st.write(payload.get("summary", payload.get("raw", "—")))
            st.divider()
            st.markdown(f"**Verdict:** {verdict}")
            if confidence != "—":
                try:
                    st.progress(min(max(float(confidence), 0.0), 1.0))
                except Exception:
                    pass


def render_edge(events):
    st.subheader("Рассчитанный Edge")
    if not events:
        st.info("Нет рассчитанных значений Edge.")
        return
    rows = []
    for ev in events:
        payload = parse_payload(ev.get("data"))
        if not isinstance(payload, dict):
            payload = {"raw": payload}
        rows.append({
            "timestamp": ev.get("timestamp"),
            "market_id": payload.get("market_id", payload.get("id", "—")),
            "question": payload.get("question", "—"),
            "edge": payload.get("edge", payload.get("edge_value", "—")),
            "direction": payload.get("direction", "—"),
            "confidence": payload.get("confidence", "—"),
        })
    df = pd.DataFrame(rows)
    df = df.sort_values("timestamp", ascending=False) if "timestamp" in df.columns else df
    st.dataframe(df, use_container_width=True, height=300)
    numeric = pd.to_numeric(df["edge"], errors="coerce").dropna()
    if not numeric.empty:
        st.bar_chart(numeric.rename("edge"))


def render_orders(events):
    st.subheader("Статусы исполнения ордеров")
    if not events:
        st.info("Нет ордеров на исполнение.")
        return
    rows = []
    for ev in events:
        payload = parse_payload(ev.get("data"))
        if not isinstance(payload, dict):
            payload = {"raw": payload}
        status = str(payload.get("status", payload.get("state", "—")))
        rows.append({
            "marker": status_color(status),
            "order_id": payload.get("order_id", payload.get("id", "—")),
            "market_id": payload.get("market_id", "—"),
            "question": payload.get("question", "—"),
            "side": payload.get("side", "—"),
            "size": payload.get("size", payload.get("amount", "—")),
            "price": payload.get("price", "—"),
            "status": status,
            "timestamp": ev.get("timestamp"),
        })
    df = pd.DataFrame(rows)
    df = df.sort_values("timestamp", ascending=False) if "timestamp" in df.columns else df
    st.dataframe(df, use_container_width=True, height=300)


def seed_demo_data(manager):
    base = datetime.now()
    manager.save_event(MARKET_EVENT, {
        "market_id": "m-1001",
        "question": "Will the Fed cut rates in September?",
        "probability": 0.62,
        "liquidity": 14500.0,
        "spread": 0.01,
    })
    manager.save_event(MARKET_EVENT, {
        "market_id": "m-1002",
        "question": "Will ETH close above $4000 this month?",
        "probability": 0.41,
        "liquidity": 8200.0,
        "spread": 0.02,
    })
    manager.save_event(TRIBUNAL, {
        "topic": "Should we open a long on m-1001?",
        "agents": [
            {"name": "Bull", "role": "pro", "argument": "Probability 0.62 with strong liquidity favors entry."},
            {"name": "Bear", "role": "con", "argument": "Macro uncertainty implies tail risk not priced in."},
            {"name": "Judge", "role": "moderator", "argument": "Edge positive but thin; size small."},
        ],
        "verdict": "APPROVE small size",
        "confidence": 0.71,
    })
    manager.save_event(EDGE, {
        "market_id": "m-1001",
        "question": "Will the Fed cut rates in September?",
        "edge": 0.08,
        "direction": "long",
        "confidence": 0.71,
    })
    manager.save_event(EDGE, {
        "market_id": "m-1002",
        "question": "Will ETH close above $4000 this month?",
        "edge": -0.03,
        "direction": "short",
        "confidence": 0.55,
    })
    manager.save_event(ORDER, {
        "order_id": "o-5001",
        "market_id": "m-1001",
        "question": "Will the Fed cut rates in September?",
        "side": "buy",
        "size": 50.0,
        "price": 0.62,
        "status": "filled",
    })
    manager.save_event(ORDER, {
        "order_id": "o-5002",
        "market_id": "m-1002",
        "question": "Will ETH close above $4000 this month?",
        "side": "sell",
        "size": 20.0,
        "price": 0.41,
        "status": "pending",
    })


def main():
    st.title("📊 Desktop Tutorial — Trading Terminal Monitor")

    with st.sidebar:
        st.header("Настройки")
        db_path = st.text_input("Путь к БД World State", value=DEFAULT_DB)
        auto_refresh = st.checkbox("Авто-обновление", value=True)
        refresh_interval = st.slider("Интервал (сек)", 1, 30, 5)
        if st.button("🔄 Обновить сейчас"):
            st.rerun()
        st.divider()
        if st.button("Сгенерировать демо-данные"):
            with st.spinner("Запись демо-данных в World State..."):
                mgr = open_manager(db_path)
                seed_demo_data(mgr)
                mgr.close()
            st.success("Демо-данные записаны.")
            st.rerun()

    try:
        manager = open_manager(db_path)
        conn_ok = True
    except Exception as exc:
        st.error(f"Не удалось открыть БД World State: {exc}")
        return

    market_events = load_events(manager, MARKET_EVENT)
    tribunal_events = load_events(manager, TRIBUNAL)
    edge_events = load_events(manager, EDGE)
    order_events = load_events(manager, ORDER)
    manager.close()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Рыночные события", len(market_events))
    c2.metric("Дебаты Tribunal", len(tribunal_events))
    c3.metric("Edge сигналы", len(edge_events))
    c4.metric("Ордера", len(order_events))

    tab1, tab2, tab3, tab4 = st.tabs(
        ["World State", "Tribunal", "Edge", "Order Execution"]
    )
    with tab1:
        render_market_events(market_events)
    with tab2:
        render_tribunal(tribunal_events)
    with tab3:
        render_edge(edge_events)
    with tab4:
        render_orders(order_events)

    st.caption(f"Источник: `{db_path}` · обновлено {datetime.now().strftime('%H:%M:%S')}")

    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
