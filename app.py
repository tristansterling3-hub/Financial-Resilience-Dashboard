import streamlit as st
import pandas as pd
import requests
import json
import plotly.express as px

# ---------------------------------------------
# PAGE CONFIG
# ---------------------------------------------
st.set_page_config(page_title="NC County Resilience Dashboard", layout="wide")


# ---------------------------------------------
# LOAD CENSUS INCOME DATA
# ---------------------------------------------
@st.cache_data
def load_census_data():
    API_KEY = "c3b895c40dc66379b8b94a7716a0832ebea452d7"
    url = (
        "https://api.census.gov/data/2022/acs/acs5?"
        "get=NAME,B19013_001E&for=county:*&in=state:37&key=" + API_KEY
    )

    response = requests.get(url)

    if response.status_code != 200:
        st.error(f"Census API request failed ({response.status_code})")
        st.stop()

    data = response.json()
    df = pd.DataFrame(data[1:], columns=data[0])
    df.rename(columns={"B19013_001E": "Median_Income"}, inplace=True)
    df["Median_Income"] = pd.to_numeric(df["Median_Income"], errors="coerce")

    # Clean county names from API response
    df["County"] = df["NAME"].str.replace(" County, North Carolina", "", regex=False)

    return df


# ---------------------------------------------
# LOAD HIGH-RES GEOJSON
# ---------------------------------------------
@st.cache_data
def load_geojson():
    with open("North_Carolina_State_and_County_Boundary_Polygons.geojson", "r") as f:
        return json.load(f)


df = load_census_data()
geojson = load_geojson()


# ---------------------------------------------
# SIDEBAR WEIGHT SLIDERS
# ---------------------------------------------
st.sidebar.header("⚖️ Adjust Score Weights")

w_income = st.sidebar.slider("Income Weight", 0.0, 1.0, 1.0, 0.05)
w_unemp = st.sidebar.slider("Unemployment Weight", 0.0, 1.0, 0.0, 0.05)
w_cost = st.sidebar.slider("Cost of Living Weight", 0.0, 1.0, 0.0, 0.05)

# Prevent divide by zero
if w_income + w_unemp + w_cost == 0:
    w_income = 1.0

total = w_income + w_unemp + w_cost

w_income /= total
w_unemp /= total
w_cost /= total

st.sidebar.subheader("Normalized")
st.sidebar.write(f"Income: **{w_income:.2f}**")
st.sidebar.write(f"Unemployment: **{w_unemp:.2f}**")
st.sidebar.write(f"Cost: **{w_cost:.2f}**")


# ---------------------------------------------
# SIMPLE AI ASSISTANT
# ---------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("🧠 AI Assistant")

question = st.sidebar.text_area("Ask about risks or county issues")

if question:
    q = question.lower()
    st.sidebar.write("**AI Response:**")

    if "flood" in q:
        st.sidebar.write("Counties in eastern NC such as Craven and Pamlico face flood risks.")
    elif "hurricane" in q:
        st.sidebar.write("Hurricane recovery resources should prioritize Robeson and Columbus.")
    elif "income" in q:
        st.sidebar.write("Low-income counties may need long-term aid programs.")
    elif "help" in q:
        st.sidebar.write("Use resilience scores to distribute resources efficiently.")
    else:
        st.sidebar.write("Try asking about floods, hurricanes, or income issues.")


# ---------------------------------------------
# NORMALIZATION + RESILIENCE SCORE
# ---------------------------------------------
df["Income_Norm"] = (df["Median_Income"] - df["Median_Income"].min()) / (
    df["Median_Income"].max() - df["Median_Income"].min()
)

# Placeholder values until you add real data
df["Unemployment_Norm"] = 0.5
df["Cost_Norm"] = 0.5

df["Resilience_Score"] = (
    w_income * df["Income_Norm"]
    + w_unemp * (1 - df["Unemployment_Norm"])
    + w_cost * (1 - df["Cost_Norm"])
).round(3)


# ---------------------------------------------
# HEADER
# ---------------------------------------------
st.title("🌎 North Carolina County Resilience Dashboard")
st.markdown("Live Census income data + dynamic scoring model + high-res map.")


# ---------------------------------------------
# SELECT COUNTY
# ---------------------------------------------
selected = st.selectbox("Choose a County", df["County"].sort_values())
selected_score = df[df["County"] == selected]["Resilience_Score"].values[0]

st.metric(f"{selected} Resilience Score", selected_score)


# ---------------------------------------------
# RANK
# ---------------------------------------------
rankdf = df.sort_values("Resilience_Score", ascending=False).reset_index(drop=True)
position = rankdf[rankdf["County"] == selected].index[0] + 1

st.markdown(f"**Rank:** #{position} out of {len(df)} counties")


# ---------------------------------------------
# INSIGHT
# ---------------------------------------------
income_norm = df[df["County"] == selected]["Income_Norm"].values[0]

if income_norm > 0.75:
    insight = "High income levels"
elif income_norm < 0.40:
    insight = "Low income levels"
else:
    insight = "Moderate income levels"

st.markdown(f"**Insight:** {insight}")


# ---------------------------------------------
# BAR CHART
# ---------------------------------------------
st.subheader("📊 County Comparison")

fig_bar = px.bar(
    df.sort_values("Resilience_Score", ascending=False),
    x="County", y="Resilience_Score",
    title="Financial Resilience by County",
)

st.plotly_chart(fig_bar, use_container_width=True)


# ---------------------------------------------
# NC RESILIENCE CHOROPLETH (HIGH RES)
# ---------------------------------------------
st.subheader("🗺️ High-Resolution NC County Map")

fig_map = px.choropleth(
    df,
    geojson=geojson,
    locations="County",
    featureidkey="properties.County",   # ← IMPORTANT FIX
    color="Resilience_Score",
    color_continuous_scale="Viridis",
    labels={"Resilience_Score": "Resilience Score"},
    title="Resilience Score by County",
)

# ⭐ Fix blank map: hide global map + fit to NC boundaries
fig_map.update_geos(
    fitbounds="locations",
    visible=False
)

# ⭐ Clean layout + smooth transitions
fig_map.update_layout(
    margin={"r": 0, "t": 30, "l": 0, "b": 0},
    transition_duration=600
)

st.plotly_chart(fig_map, use_container_width=True)

# ---------------------------------------------
# DATA TABLE
# ---------------------------------------------
st.subheader("📋 Resilience Score Breakdown")

st.dataframe(
    df[["County", "Median_Income", "Income_Norm", "Resilience_Score"]].round(3),
    use_container_width=True
)


# ---------------------------------------------
# TOP/BOTTOM 5
# ---------------------------------------------
st.subheader("🏆 Rankings")

col1, col2 = st.columns(2)

with col1:
    st.write("### 🟢 Top 5 Counties")
    st.dataframe(rankdf.head(5))

with col2:
    st.write("### 🔴 Bottom 5 Counties")
    st.dataframe(rankdf.tail(5))


# ---------------------------------------------
# DOWNLOAD BUTTON
# ---------------------------------------------
st.download_button(
    "Download Resilience Scores",
    data=df.to_csv(index=False),
    file_name="nc_resilience_scores.csv",
    mime="text/csv"
)


# ---------------------------------------------
# METHODOLOGY
# ---------------------------------------------
st.markdown("### 📘 Methodology")
st.markdown("""
**Resilience Score = Weighted Blend of:**
- Median Income (normalized)
- Unemployment (placeholder)
- Cost of Living (placeholder)

**Scores range 0–1.**  
All weights are user-adjustable.
""")
