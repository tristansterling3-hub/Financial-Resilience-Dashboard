import streamlit as st
import pandas as pd
import plotly.express as px

# Set page config
st.set_page_config(page_title="Financial Resilience Dashboard", layout="wide")

# Load data (no caching)
def load_data():
    return pd.read_csv("resilience_scores_full.csv")

df = load_data()

# Sidebar: Adjustable Weights
st.sidebar.header("⚖️ Adjust Score Weights")
w_income = st.sidebar.slider("Weight: Income", 0.0, 1.0, 0.4, 0.05)
w_unemp = st.sidebar.slider("Weight: Unemployment", 0.0, 1.0, 0.3, 0.05)
w_cost = st.sidebar.slider("Weight: Cost of Living", 0.0, 1.0, 0.3, 0.05)

# Normalize weights
total = w_income + w_unemp + w_cost
w_income, w_unemp, w_cost = w_income / total, w_unemp / total, w_cost / total

st.sidebar.markdown("**Normalized Weights**")
st.sidebar.write(f"- Income: `{w_income:.2f}`")
st.sidebar.write(f"- Unemployment: `{w_unemp:.2f}`")
st.sidebar.write(f"- Cost: `{w_cost:.2f}`")

# Recalculate Resilience Score
df["Resilience_Score"] = (
    w_income * df["Income_Norm"] +
    w_unemp * (1 - df["Unemployment_Norm"]) +
    w_cost * (1 - df["Cost_Norm"])
).round(3)

# App Header
st.title("💸 Financial Resilience Dashboard")
st.markdown("""
Use this dashboard to explore which U.S. states are most financially resilient — 
based on median income, unemployment rate, and cost of living.
""")

# State Selector
selected_state = st.selectbox("Select a State", df["State"].sort_values())
state_score = df[df["State"] == selected_state]["Resilience_Score"].values[0]
st.metric(label=f"{selected_state} Resilience Score", value=round(state_score, 3))

# Rank
rank = df.sort_values("Resilience_Score", ascending=False).reset_index(drop=True)
position = rank[rank["State"] == selected_state].index[0] + 1
st.markdown(f"**{selected_state}** ranks **#{position} out of {len(df)}** in overall financial resilience.")

# Insight
row = df[df["State"] == selected_state].iloc[0]
income, unemp, cost = row["Income_Norm"], row["Unemployment_Norm"], row["Cost_Norm"]
comment = []

if income > 0.75: comment.append("strong income levels")
elif income < 0.4: comment.append("low income levels")

if unemp < 0.3: comment.append("very low unemployment")
elif unemp > 0.7: comment.append("high unemployment")

if cost < 0.4: comment.append("affordable cost of living")
elif cost > 0.75: comment.append("high cost of living")

if comment:
    insight = "This score reflects " + ", ".join(comment[:-1])
    if len(comment) > 1:
        insight += ", and " + comment[-1] + "."
    else:
        insight += comment[-1] + "."
else:
    insight = "This state has balanced factors across income, unemployment, and cost."

st.markdown(f"_**Insight:** {insight}_")

# Bar Chart
st.subheader("📊 State Comparison")
fig = px.bar(
    df.sort_values("Resilience_Score", ascending=False),
    x="State", y="Resilience_Score",
    title="Financial Resilience by State",
    labels={"Resilience_Score": "Resilience Score"},
    height=500
)
st.plotly_chart(fig, use_container_width=True)

# Choropleth Map
st.subheader("🗺️ U.S. Resilience Map")
state_abbr = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
    'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
    'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
    'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
    'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
    'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
    'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
    'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
}
df["State_Abbr"] = df["State"].map(state_abbr)

fig_map = px.choropleth(
    df,
    locations="State_Abbr",
    locationmode="USA-states",
    color="Resilience_Score",
    scope="usa",
    color_continuous_scale="Viridis",
    labels={"Resilience_Score": "Resilience Score"},
    title="Financial Resilience Score by State"
)
st.plotly_chart(fig_map, use_container_width=True)

# Score Breakdown Table
st.subheader("🧮 Resilience Score Breakdown")
breakdown_df = df[[
    "State", "Income_Norm", "Unemployment_Norm", "Cost_Norm", "Resilience_Score"
]].copy()
breakdown_df.columns = [
    "State", "Income (Normalized)", "Unemployment (Normalized)",
    "Cost of Living (Normalized)", "Resilience Score"
]
st.dataframe(breakdown_df.round(3), use_container_width=True)

# Top & Bottom Rankings
st.subheader("📈 State Resilience Rankings")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🟢 Top 5 Most Resilient States")
    top5 = df.sort_values("Resilience_Score", ascending=False).head(5)[["State", "Resilience_Score"]]
    st.dataframe(top5, use_container_width=True)

with col2:
    st.markdown("### 🔴 Bottom 5 Least Resilient States")
    bottom5 = df.sort_values("Resilience_Score", ascending=True).head(5)[["State", "Resilience_Score"]]
    st.dataframe(bottom5, use_container_width=True)

# Download Button
st.download_button(
    label="📥 Download Resilience Scores (with current weights)",
    data=df.to_csv(index=False),
    file_name="resilience_scores_export.csv",
    mime="text/csv"
)

# Methodology & FAQ
st.markdown("### ℹ️ Methodology & FAQ")
st.markdown("""
**Q: What is the Resilience Score?**  
A data-driven estimate of how well a U.S. state could financially withstand a crisis.

**Q: What data is it based on?**  
- Median Income (normalized)  
- Unemployment Rate (normalized and inverted)  
- Cost of Living Index (normalized and inverted)

**Q: Why does this matter?**  
Helps identify vulnerable communities and guide equitable resource allocation.

**Q: Who could use this tool?**  
Nonprofits, insurers, governments, journalists, educators, and policy analysts.

**Q: Can I download the data?**  
Yes — use the button above to export the live dataset with your selected weights.
""")