import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="NC County Resilience Dashboard", layout="wide")


# -----------------------------
# Load Census API Income Data
# -----------------------------
@st.cache_data
def load_census_data():
    API_KEY = "c3b895c40dc66379b8b94a7716a0832ebea452d7"
    url = (
        "https://api.census.gov/data/2022/acs/acs5?"
        "get=NAME,B19013_001E&for=county:*&in=state:37&key=" + API_KEY
    )

    response = requests.get(url)
    if response.status_code != 200:
        st.error("Census API request failed.")
        st.text(response.text)
        st.stop()

    try:
        data = response.json()
    except Exception as e:
        st.error(f"Invalid JSON from Census API: {e}")
        st.stop()

    df = pd.DataFrame(data[1:], columns=data[0])
    df.rename(columns={"B19013_001E": "Median_Income"}, inplace=True)
    df["Median_Income"] = pd.to_numeric(df["Median_Income"], errors="coerce")

    # Clean county names
    df["County"] = df["NAME"].str.replace(" County, North Carolina", "", regex=False)

    return df


# -----------------------------
# Load GeoJSON for NC Counties
# -----------------------------
@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/sieger1010/NorthCarolina-GeoJson/main/NCCountiesComplete.geo.json"
    response = requests.get(url)

    if response.status_code != 200:
        st.error("GeoJSON download failed")
        st.stop()

    try:
        return response.json()
    except:
        st.error("Invalid GeoJSON data.")
        st.stop()


df = load_census_data()
geojson = load_geojson()


# -----------------------------
# Sidebar: Weight Sliders
# -----------------------------
st.sidebar.header("⚖️ Adjust Score Weights")
w_income = st.sidebar.slider("Weight: Income", 0.0, 1.0, 1.0, 0.05)
w_unemp = st.sidebar.slider("Weight: Unemployment", 0.0, 1.0, 0.0, 0.05)
w_cost = st.sidebar.slider("Weight: Cost of Living", 0.0, 1.0, 0.0, 0.05)

# Avoid divide-by-zero if all sliders = 0
if w_income + w_unemp + w_cost == 0:
    w_income = 1.0
    w_unemp = 0.0
    w_cost = 0.0

total = w_income + w_unemp + w_cost
w_income /= total
w_unemp /= total
w_cost /= total

st.sidebar.subheader("Normalized Weights")
st.sidebar.write(f"Income: **{w_income:.2f}**")
st.sidebar.write(f"Unemployment: **{w_unemp:.2f}**")
st.sidebar.write(f"Cost of Living: **{w_cost:.2f}**")


# -----------------------------
# AI Assistant (Simple Rules)
# -----------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("🧠 AI Assistant")

user_question = st.sidebar.text_area("Ask about future risks or interventions:")

if user_question:
    text = user_question.lower()
    st.sidebar.write("**AI Response:**")

    if "flood" in text:
        st.sidebar.write("Eastern counties like Craven and Pamlico have elevated flood risk next month.")
    elif "hurricane" in text:
        st.sidebar.write("Hurricane recovery resources should go to Robeson and Columbus first.")
    elif "low-income" in text:
        st.sidebar.write("Low-income counties should receive housing aid and mobile health units.")
    elif "intervention" in text:
        st.sidebar.write("Interventions should target counties with low resilience scores.")
    else:
        st.sidebar.write("Try asking about risks like flooding, hurricanes, or resource needs.")


# -----------------------------
# Compute Resilience Score
# -----------------------------
df["Income_Norm"] = (df["Median_Income"] - df["Median_Income"].min()) / (
    df["Median_Income"].max() - df["Median_Income"].min()
)

# Placeholder until real data is added
df["Unemployment_Norm"] = 0.5
df["Cost_Norm"] = 0.5

df["Resilience_Score"] = (
    w_income * df["Income_Norm"]
    + w_unemp * (1 - df["Unemployment_Norm"])
    + w_cost * (1 - df["Cost_Norm"])
).round(3)


# -----------------------------
# Header
# -----------------------------
st.title("🌎 North Carolina County Financial Resilience Dashboard")
st.markdown("Live Census income data + adjustable scoring model.")


# -----------------------------
# County Selector
# -----------------------------
selected_county = st.selectbox("Choose a County", df["County"].sort_values())
score = df[df["County"] == selected_county]["Resilience_Score"].values[0]
st.metric(f"{selected_county} Resilience Score", score)


# -----------------------------
# Ranking
# -----------------------------
rank_df = df.sort_values("Resilience_Score", ascending=False).reset_index(drop=True)
rank = rank_df[rank_df["County"] == selected_county].index[0] + 1
st.markdown(f"**Rank:** #{rank} out of {len(df)} counties")


# -----------------------------
# Insight Text
# -----------------------------
income_norm = df[df["County"] == selected_county]["Income_Norm"].values[0]

if income_norm > 0.75:
    insight = "This county has **strong income levels**."
elif income_norm < 0.4:
    insight = "This county has **low income levels**."
else:
    insight = "This county has **moderate, balanced income levels**."

st.markdown(f"**Insight:** {insight}")


# -----------------------------
# Bar Chart
# -----------------------------
st.subheader("📊 County Comparison")
fig = px.bar(
    df.sort_values("Resilience_Score", ascending=False),
    x="County",
    y="Resilience_Score",
    title="Financial Resilience by County",
)
st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------
# 🗺️ NC County Resilience Map (Dynamic Colors)
# ---------------------------------------------
st.subheader("🗺️ NC County Resilience Map")

fig_map = px.choropleth(
    df,
    geojson=geojson,
    locations="County",
    featureidkey="properties.NAME",
    color="Resilience_Score",
    hover_name="County",
    color_continuous_scale=[
        "#ff0000",  # low resilience (red)
        "#ffa500",  # medium low (orange)
        "#ffff00",  # medium (yellow)
        "#90ee90",  # medium high (light green)
        "#008000"   # high (green)
    ],
    range_color=(df["Resilience_Score"].min(), df["Resilience_Score"].max()),
)

# Make the map zoom correctly around NC
fig_map.update_geos(
    fitbounds="locations",
    visible=False
)

# Smooth color transitions
fig_map.update_layout(
    margin={"r": 0, "t": 30, "l": 0, "b": 0},
    transition_duration=600  # smooth animation
)

st.plotly_chart(fig_map, use_container_width=True)


# -----------------------------
# Table
# -----------------------------
st.subheader("Resilience Score Breakdown")
table = df[["County", "Median_Income", "Income_Norm", "Resilience_Score"]].round(3)
st.dataframe(table, use_container_width=True)


# -----------------------------
# Top / Bottom 5
# -----------------------------
st.subheader("County Resilience Rankings")
col1, col2 = st.columns(2)

with col1:
    st.write("### 🟢 Top 5 Counties")
    st.dataframe(rank_df.head(5)[["County", "Resilience_Score"]])

with col2:
    st.write("### 🔴 Bottom 5 Counties")
    st.dataframe(rank_df.tail(5)[["County", "Resilience_Score"]])


# -----------------------------
# Download Button
# -----------------------------
st.download_button(
    "Download NC Resilience Scores",
    data=df.to_csv(index=False),
    file_name="nc_resilience_scores.csv",
    mime="text/csv",
)


# -----------------------------
# Methodology
# -----------------------------
st.markdown("### 📘 Methodology & FAQ")
st.markdown("""
**Resilience Score Formula**  
Combines:
- Median Income (normalized)
- Unemployment (placeholder)
- Cost of Living (placeholder)

**Why?**  
Higher income → more financial buffer  
Lower unemployment → more stability  
Lower cost of living → more affordability  

Scores range from **0–1** and depend on slider weights.
""")
