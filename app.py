import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Insurance Claims Fraud Analysis", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("data/fraud_oracle.csv")
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df["DayOfWeek"] = pd.Categorical(df["DayOfWeek"], categories=day_order, ordered=True)
    df["IsWeekend"] = df["DayOfWeek"].isin(["Saturday", "Sunday"])

    # Reporting delay in weeks
    month_map = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
                 "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
    valid = df["MonthClaimed"] != "0"
    df.loc[valid, "IncidentWeek"] = df.loc[valid, "Month"].map(month_map) * 4 + df.loc[valid, "WeekOfMonth"]
    df.loc[valid, "ClaimedWeek"]  = df.loc[valid, "MonthClaimed"].map(month_map) * 4 + df.loc[valid, "WeekOfMonthClaimed"]
    df.loc[valid, "ReportingDelay"] = df.loc[valid, "ClaimedWeek"] - df.loc[valid, "IncidentWeek"]
    df.loc[~valid, "ReportingDelay"] = None
    return df

df = load_data()

# ── Sidebar filters ──────────────────────────────────────────────────────────
st.sidebar.header("Filters")

fault_options = ["All"] + sorted(df["Fault"].dropna().unique().tolist())
fault_filter = st.sidebar.selectbox("Fault Type", fault_options)

vehicle_options = ["All"] + sorted(df["VehicleCategory"].dropna().unique().tolist())
vehicle_filter = st.sidebar.selectbox("Vehicle Category", vehicle_options)

age_min, age_max = int(df["Age"].min()), int(df["Age"].max())
age_range = st.sidebar.slider("Driver Age", age_min, age_max, (age_min, age_max))

base_policy_options = ["All"] + sorted(df["BasePolicy"].dropna().unique().tolist())
base_policy_filter = st.sidebar.selectbox("Base Policy", base_policy_options)

# Apply filters
filtered = df.copy()
if fault_filter != "All":
    filtered = filtered[filtered["Fault"] == fault_filter]
if vehicle_filter != "All":
    filtered = filtered[filtered["VehicleCategory"] == vehicle_filter]
if base_policy_filter != "All":
    filtered = filtered[filtered["BasePolicy"] == base_policy_filter]
filtered = filtered[(filtered["Age"] >= age_range[0]) & (filtered["Age"] <= age_range[1])]

# ── Header ───────────────────────────────────────────────────────────────────
st.title("Insurance Claims Fraud Analysis")
st.markdown(
    "Exploring when and why fraudulent claims occur in auto insurance data. "
    "Built by **Jess Chavda** — 7 years of claims processing experience at a major carrier, "
    "now applying that domain knowledge to data analytics."
)

# ── KPI row ──────────────────────────────────────────────────────────────────
total = len(filtered)
fraud_rate = filtered["FraudFound_P"].mean()
weekend_fraud = filtered[filtered["IsWeekend"]]["FraudFound_P"].mean()
weekday_fraud = filtered[~filtered["IsWeekend"]]["FraudFound_P"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Claims", f"{total:,}")
c2.metric("Overall Fraud Rate", f"{fraud_rate:.1%}")
c3.metric("Weekend Fraud Rate", f"{weekend_fraud:.1%}")
c4.metric("Weekday Fraud Rate", f"{weekday_fraud:.1%}",
          delta=f"{weekday_fraud - weekend_fraud:.1%} vs weekend",
          delta_color="inverse")

st.divider()

# ── Chart 1: Fraud rate by day ────────────────────────────────────────────────
st.subheader("Fraud Rate by Day of Incident")

day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
fraud_by_day = (
    filtered.groupby("DayOfWeek", observed=True)["FraudFound_P"]
    .mean()
    .reindex(day_order)
    .reset_index()
)
fraud_by_day.columns = ["Day", "FraudRate"]
fraud_by_day["Type"] = fraud_by_day["Day"].apply(
    lambda d: "Weekend" if d in ["Saturday", "Sunday"] else "Weekday"
)

fig1 = px.bar(
    fraud_by_day, x="Day", y="FraudRate", color="Type",
    color_discrete_map={"Weekend": "#e05252", "Weekday": "#4a90d9"},
    labels={"FraudRate": "Fraud Rate", "Day": "Day of Incident"},
    text=fraud_by_day["FraudRate"].apply(lambda x: f"{x:.1%}"),
)
fig1.add_hline(
    y=filtered["FraudFound_P"].mean(),
    line_dash="dash", line_color="gray",
    annotation_text="Overall avg", annotation_position="top right"
)
fig1.update_traces(textposition="outside")
fig1.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 0.12], showlegend=True)
st.plotly_chart(fig1, use_container_width=True)

# ── Chart 2: Incident day vs filed day ───────────────────────────────────────
st.subheader("When Incidents Happen vs When Claims Are Filed")
st.caption("Weekend incidents are rarely reported on the weekend — they pile up on Monday.")

incident_counts = filtered["DayOfWeek"].value_counts().reindex(day_order).fillna(0)

valid_days = [d for d in day_order if d in filtered["DayOfWeekClaimed"].values]
filed_counts = filtered["DayOfWeekClaimed"].value_counts().reindex(day_order).fillna(0)

fig2 = go.Figure()
fig2.add_trace(go.Bar(name="Incident Day", x=day_order, y=incident_counts.values, marker_color="#4a90d9"))
fig2.add_trace(go.Bar(name="Claim Filed Day", x=day_order, y=filed_counts.values, marker_color="#f0a050"))
fig2.update_layout(barmode="group", yaxis_title="Number of Claims", xaxis_title="Day of Week")
st.plotly_chart(fig2, use_container_width=True)

# ── Chart 3: Fraud by fault × weekend ────────────────────────────────────────
st.subheader("Fraud Rate by Fault Type and Weekend")
st.caption("Policy Holder fault on weekends carries the highest fraud rate.")

fault_weekend = (
    filtered.groupby(["Fault", "IsWeekend"])["FraudFound_P"]
    .mean()
    .reset_index()
)
fault_weekend["Weekend"] = fault_weekend["IsWeekend"].map({True: "Weekend", False: "Weekday"})

fig3 = px.bar(
    fault_weekend, x="Fault", y="FraudFound_P", color="Weekend", barmode="group",
    color_discrete_map={"Weekend": "#e05252", "Weekday": "#4a90d9"},
    labels={"FraudFound_P": "Fraud Rate", "Fault": "Fault Type"},
    text=fault_weekend["FraudFound_P"].apply(lambda x: f"{x:.1%}"),
)
fig3.update_traces(textposition="outside")
fig3.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 0.16])
st.plotly_chart(fig3, use_container_width=True)

# ── Chart 4: Weekend fraud by reporting timing ───────────────────────────────
st.divider()
st.subheader("Weekend Fraud: Same-Weekend Filers vs Monday Filers")
st.caption(
    "Among weekend incidents, claims filed immediately (Sat/Sun) have a far higher fraud rate "
    "than those reported the following Monday — the opposite of the intuitive assumption."
)

weekend_f = filtered[filtered["IsWeekend"]].copy()
weekend_f["ReportingGroup"] = "Other weekday"
weekend_f.loc[weekend_f["DayOfWeekClaimed"].isin(["Saturday", "Sunday"]), "ReportingGroup"] = "Filed same weekend"
weekend_f.loc[weekend_f["DayOfWeekClaimed"] == "Monday", "ReportingGroup"] = "Filed Monday"

timing = (
    weekend_f.groupby("ReportingGroup")["FraudFound_P"]
    .agg(FraudRate="mean", Count="count")
    .reset_index()
    .sort_values("FraudRate", ascending=False)
)
timing = timing[timing["Count"] >= 10]

color_map = {"Filed same weekend": "#e05252", "Filed Monday": "#4a90d9", "Other weekday": "#aaaaaa"}
fig4 = px.bar(
    timing, x="ReportingGroup", y="FraudRate",
    color="ReportingGroup", color_discrete_map=color_map,
    labels={"FraudRate": "Fraud Rate", "ReportingGroup": "When Claim Was Filed"},
    text=timing["FraudRate"].apply(lambda x: f"{x:.1%}"),
)
fig4.update_traces(textposition="outside", showlegend=False)
fig4.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 0.18])
st.plotly_chart(fig4, use_container_width=True)

col_a, col_b = st.columns(2)
col_a.metric("Same-weekend filers fraud rate", f"{timing.loc[timing['ReportingGroup']=='Filed same weekend','FraudRate'].values[0]:.1%}" if 'Filed same weekend' in timing['ReportingGroup'].values else "n/a")
col_b.metric("Monday filers fraud rate", f"{timing.loc[timing['ReportingGroup']=='Filed Monday','FraudRate'].values[0]:.1%}" if 'Filed Monday' in timing['ReportingGroup'].values else "n/a")

# ── Chart 5: Fraud rate by reporting delay ───────────────────────────────────
st.subheader("Fraud Rate by Reporting Delay (weeks)")
st.caption("Longer delays between incident and claim filing correlate with higher fraud — not lower.")

delay_data = (
    filtered[filtered["ReportingDelay"].notna() & (filtered["ReportingDelay"] >= 0)]
    .groupby("ReportingDelay")["FraudFound_P"]
    .agg(FraudRate="mean", Count="count")
    .reset_index()
)
delay_data = delay_data[delay_data["Count"] >= 30]

fig5 = px.bar(
    delay_data, x="ReportingDelay", y="FraudRate",
    labels={"FraudRate": "Fraud Rate", "ReportingDelay": "Reporting Delay (weeks)", "Count": "# Claims"},
    color="FraudRate", color_continuous_scale=["#4a90d9", "#e05252"],
    hover_data={"Count": True},
    text=delay_data["FraudRate"].apply(lambda x: f"{x:.1%}"),
)
fig5.update_traces(textposition="outside")
fig5.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 0.16], coloraxis_showscale=False)
st.plotly_chart(fig5, use_container_width=True)

# ── Key findings ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("Key Findings")
st.markdown("""
- **Weekend incidents have a ~25% higher fraud rate** than weekday incidents (Sunday peaks at ~7%, vs ~5% on Tuesday/Wednesday).
- **Same-weekend filers are the highest-risk group** — claims filed immediately on Saturday or Sunday after a weekend incident carry a ~12.8% fraud rate, more than double Monday filers (5.5%). Quick filing may indicate a prepared fraudulent claim.
- **Longer delays mean more fraud, not less** — fraud rate rises steadily with reporting delay weeks, peaking above 10% for claims filed 7+ weeks after the incident.
- **The highest-risk segment** is Policy Holder fault claims from weekend incidents (~9% fraud rate) — nearly double the rate of Third Party fault claims.
- **Practical implication:** Two separate flags are worth adding at intake — same-weekend filing and delays beyond 5 weeks — both signal elevated fraud risk independent of day of week alone.
""")
