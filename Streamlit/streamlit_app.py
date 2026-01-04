import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import _snowflake
from snowflake.snowpark.context import get_active_session

# =========================
# 🔧 CONFIG
# =========================
DB = "SUPPLY_CHAIN_ASSISTANT_DB"
SCHEMA = "ENTITIES"

CORTEX_AGENT_ENDPOINT = "/api/v2/cortex/agent:run"
WAREHOUSE = "SUPPLY_CHAIN_ASSISTANT_WH"

session = get_active_session()

st.set_page_config(
    page_title="Supply Chain Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# 🎛️ SIDEBAR CONTROLS
# =========================
st.sidebar.title("📦 Supply Chain Control Center")

page = st.sidebar.selectbox(
    "Navigate",
    ["📊 Dashboard", "🚨 Alerts", "📦 Optimization"]
)

LOW_DAYS = st.sidebar.slider(
    "Low Stock Threshold (Days)",
    1, 60, 22
)

EXCESS_MULT = st.sidebar.slider(
    "Excess Threshold (× Safety Stock)",
    1.5, 5.0, 3.0, 0.1
)

st.sidebar.markdown("---")
st.sidebar.caption("Powered by Snowflake Cortex ❄️")

# =========================
# 📥 DATA LOADERS
# =========================
@st.cache_data(ttl=300)
def load_inventory():
    return session.sql(f"""
        SELECT
            i.MFG_PLANT_ID,
            p.MFG_PLANT_NAME,
            i.MATERIAL_ID,
            r.MATERIAL_NAME,
            i.QUANTITY_ON_HAND,
            i.SAFETY_STOCK_LEVEL,
            i.DAYS_FORWARD_COVERAGE,
            r.MATERIAL_COST,
            i.QUANTITY_ON_HAND * r.MATERIAL_COST AS INVENTORY_VALUE
        FROM {DB}.{SCHEMA}.MFG_INVENTORY i
        JOIN {DB}.{SCHEMA}.MFG_PLANT p ON i.MFG_PLANT_ID = p.MFG_PLANT_ID
        JOIN {DB}.{SCHEMA}.RAW_MATERIAL r ON i.MATERIAL_ID = r.MATERIAL_ID
    """).to_pandas()

def classify_inventory(df):
    df = df.copy()
    df["INVENTORY_STATUS"] = np.where(
        df["DAYS_FORWARD_COVERAGE"] < LOW_DAYS,
        "LOW",
        np.where(
            df["QUANTITY_ON_HAND"] > df["SAFETY_STOCK_LEVEL"] * EXCESS_MULT,
            "EXCESS",
            "NORMAL"
        )
    )
    return df

API_ENDPOINT = "/api/v2/cortex/agent:run"
API_TIMEOUT = 60000  # ms

# =========================
# 📊 DASHBOARD
# =========================
if page == "📊 Dashboard":
    st.title("📊 Supply Chain Dashboard")

    df = classify_inventory(load_inventory())

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Inventory Value", f"${df['INVENTORY_VALUE'].sum():,.0f}")
    col2.metric("Low Stock Items", (df["INVENTORY_STATUS"] == "LOW").sum())
    col3.metric("Excess Stock Items", (df["INVENTORY_STATUS"] == "EXCESS").sum())
    col4.metric("Plants", df["MFG_PLANT_ID"].nunique())

    st.markdown("---")

    # Inventory Value by Plant
    plant_df = df.groupby(
        ["MFG_PLANT_NAME", "INVENTORY_STATUS"],
        as_index=False
    )["INVENTORY_VALUE"].sum()

    fig = px.bar(
        plant_df,
        x="MFG_PLANT_NAME",
        y="INVENTORY_VALUE",
        color="INVENTORY_STATUS",
        color_discrete_map={
            "LOW": "#e11d48",
            "EXCESS": "#facc15",
            "NORMAL": "#22c55e"
        },
        title="Inventory Value by Plant"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Inventory Details")
    st.dataframe(df, use_container_width=True)

# =========================
# 🚨 ALERTS
# =========================
elif page == "🚨 Alerts":
    st.title("🚨 Supply Chain Alerts")

    df = classify_inventory(load_inventory())

    alerts = []

    low_count = (df["INVENTORY_STATUS"] == "LOW").sum()
    excess_count = (df["INVENTORY_STATUS"] == "EXCESS").sum()
    low_items = df[df["INVENTORY_STATUS"] == "LOW"]
    excess_items = df[df["INVENTORY_STATUS"] == "EXCESS"]

    if low_count:
        alerts.append(("error", f"{low_count} materials are below threshold"))
        with st.expander(f"🔴 Low Inventory Materials ({len(low_items)})", expanded=False):
            st.dataframe(
                low_items[
                    [
                        "MFG_PLANT_NAME",
                        "MATERIAL_NAME",
                        "QUANTITY_ON_HAND",
                        "SAFETY_STOCK_LEVEL",
                        "DAYS_FORWARD_COVERAGE",
                        "INVENTORY_VALUE"
                    ]
                ].sort_values("DAYS_FORWARD_COVERAGE"),
                use_container_width=True
            )
    if excess_count:
        alerts.append(("warning", f"{excess_count} materials are overstocked"))
        with st.expander(f"🟡 Overstocked Materials ({len(excess_items)})", expanded=False):
            st.dataframe(
                excess_items[
                    [
                        "MFG_PLANT_NAME",
                        "MATERIAL_NAME",
                        "QUANTITY_ON_HAND",
                        "SAFETY_STOCK_LEVEL",
                        "DAYS_FORWARD_COVERAGE",
                        "INVENTORY_VALUE"
                    ]
                ].sort_values("QUANTITY_ON_HAND", ascending=False),
                use_container_width=True
            )


    if not alerts:
        st.success("✅ No active alerts. Supply chain is healthy.")
    else:
        for level, msg in alerts:
            getattr(st, level)(msg)

    # 📧 Email Alerts
    if st.button("📧 Send Alert Email"):
        session.sql(f"""
            CALL SEND_MAIL(
                'supplychain@company.com',
                'Supply Chain Alerts',
                'Low items: {low_count}, Excess items: {excess_count}'
            )
        """).collect()
        st.success("Email sent successfully")
  
# =========================
# 📦 OPTIMIZATION
# =========================
elif page == "📦 Optimization":
    st.title("📦 Inventory Optimization")

    df = classify_inventory(load_inventory())

    low_df = df[df["INVENTORY_STATUS"] == "LOW"]
    excess_df = df[df["INVENTORY_STATUS"] == "EXCESS"]

    if low_df.empty or excess_df.empty:
        st.info("No optimization needed.")
    else:
        comparison = pd.merge(
            low_df,
            excess_df,
            on="MATERIAL_ID",
            suffixes=("_LOW", "_EXCESS")
        )

        comparison["TRANSFER_COST"] = comparison["INVENTORY_VALUE_LOW"] * 0.3
        comparison["PURCHASE_COST"] = comparison["INVENTORY_VALUE_LOW"]

        fig = go.Figure()
        fig.add_bar(name="Transfer", x=comparison["MATERIAL_NAME_LOW"], y=comparison["TRANSFER_COST"])
        fig.add_bar(name="Purchase", x=comparison["MATERIAL_NAME_LOW"], y=comparison["PURCHASE_COST"])

        fig.update_layout(
            barmode="group",
            title="Transfer vs Purchase Cost Comparison"
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(comparison, use_container_width=True)
