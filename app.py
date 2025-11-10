import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import folium
from streamlit_folium import folium_static

# -------------------------------
# Page setup
# -------------------------------
st.set_page_config(page_title="NC County Resilience Dashboard", layout="wide")

# -------------------------------
# Load Census data
# -------------------------------
@st.cache_data
def load_census_data():
    API_KEY = "c3b895c40dc66379b8b94a7716a0832ebea452d7"
    url = f"https://api.census.gov/data/2022/acs/acs5?get=NAME,B19013_001E&for=county:*&in=state:37&key={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        st.error("Failed to fetch data from the Census API. Please check your API key or network connection.")
        st.stop()

    try:
        data = response.json()
    except Exception as e:
        st.error(f"Failed to parse Census API response: {e}")
        st.stop()

    df = pd.DataFrame(data[1:], columns=data[0])
    df.rename(columns={"B19013_001E": "Median_Income"}, inplace=True)
    df["Median_Income"] = pd.to_numeric(df["Median_Income"], errors="coerce")
    df["County"] = df["NAME"].str.replace(" County, North Carolina", "", regex=False)
    return df

@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/sieger1010/NorthCarolina-GeoJson/main/NCCountiesComplete.geo.json"
    response = requests.get(url)

    if response.status_code != 200:
        st.error("Failed to fetch GeoJSON data. Please check the URL or network connection.")
        st.stop()

    try:
        geojson = response.json()
    except Exception as e:
        st.error(f"Failed to parse GeoJSON data: {e}")
        st.stop()

    return geojson

df = load_census_data()
geojson = load_geojson()

# -------------------------------
# Sidebar: Weights
# -------------------------------
st.sidebar.header("Adjust Score Weights")
w_income = st.sidebar.slider("Weight: Income", 0.0, 1.0, 1.0, 0.05)
w_unemp = st.sidebar.slider("Weight: Unemployment", 0.0, 1.0, 0.0, 0.05)
w_cost = st.sidebar.slider("Weight: Cost of Living", 0.0, 1.0, 0.0, 0.05)

total = w_income + w_unemp + w_cost
w_income, w_unemp, w_cost = w_income / total, w_unemp / total, w_cost / total

st.sidebar.markdown("**Normalized Weights**")
st.sidebar.write(f"- Income: {w_income:.2f}")
st.sidebar.write(f"- Unemployment: {w_unemp:.2f}")
st.sidebar.write(f"- Cost: {w_cost:.2f}")

# -------------------------------
# Normalize values
# -------------------------------
df["Income_Norm"] = (df["Median_Income"] - df["Median_Income"].min()) / (df["Median_Income"].max() - df["Median_Income"].min())
df["Unemployment_Norm"] = 0.5   # placeholder
df["Cost_Norm"] = 0.5           # placeholder

df["Resilience_Score"] = (
    w_income * df["Income_Norm"] +
    w_unemp * (1 - df["Unemployment_Norm"]) +
    w_cost * (1 - df["Cost_Norm"])
).round(3)

# -------------------------------
# Header
# -------------------------------
st.title("North Carolina County Financial Resilience Dashboard")
st.markdown("Explore financial resilience across NC counties using live Census data.")

# -------------------------------
# County Selector
# -------------------------------
selected_county = st.selectbox("Select a County", df["County"].sort_values())
score = df[df["County"] == selected_county]["Resilience_Score"].values[0]
st.metric(label=f"{selected_county} Resilience Score", value=round(score, 3))

rank = df.sort_values("Resilience_Score", ascending=False).reset_index(drop=True)
position = rank[rank["County"] == selected_county].index[0] + 1
st.markdown(f"{selected_county} ranks #{position} out of {len(df)} counties.")

# -------------------------------
# Bar Chart
# -------------------------------
st.subheader("County Comparison")
fig_bar = px.bar(
    df.sort_values("Resilience_Score", ascending=False),
    x="County", y="Resilience_Score",
    title="Financial Resilience by County",
    labels={"Resilience_Score": "Resilience Score"},
    height=500
)
st.plotly_chart(fig_bar, use_container_width=True)

# -------------------------------
# Choropleth Map
# -------------------------------
st.subheader("North Carolina County Resilience Map")
fig_map = px.choropleth(
    df,
    geojson=geojson,
    locations="County",
    featureidkey="properties.NAME",
    color="Resilience_Score",
    color_continuous_scale="Viridis",
    range_color=[df["Resilience_Score"].min(), df["Resilience_Score"].max()],
    labels={"Resilience_Score": "Resilience Score"},
    title="Resilience Score by County",
)
fig_map.update_geos(fitbounds="locations", visible=False)
st.plotly_chart(fig_map, use_container_width=True)

# -------------------------------
# Folium Map (optional WMS overlay)
# -------------------------------
st.subheader("Interactive Map with WMS Layer")
m = folium.Map(location=[35.7596, -79.0193], zoom_start=7)
wms_url = "https://gis11.services.ncdot.gov/arcgis/services/NCDOT_CountyBdy_Poly/MapServer/WMSServer"
folium.raster_layers.WmsTileLayer(
    url=wms_url,
    name="NCDOT County Boundaries",
    layers="0",
    format="image/png",
    transparent=True
).add_to(m)
folium_static(m)

# -------------------------------
# AI Assistant (basic Q&A)
# -------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("🧠 AI Assistant")
user_question = st.sidebar.text_area("Ask about counties or resilience")

if user_question:
    st.sidebar.markdown("**AI Response:**")
    if "lowest" in user_question.lower():
        low = df.sort_values("Resilience_Score").head(5)[["County","Resilience_Score"]]
        st.sidebar.write("Lowest resilience counties:")
        st.sidebar.write(low)
    elif "highest" in user_question.lower():
        high = df.sort_values("Resilience_Score", ascending=False).head(5)[["County","Resilience_Score"]]
        st.sidebar.write("Highest resilience counties:")
        st.sidebar.write(high)
    else:
        st.sidebar.write("Try asking about 'highest' or 'lowest' resilience counties.")

# -------------------------------
# Download Button
# -------------------------------
st.download_button(
    label="Download County Resilience Scores",
    data=df.to_csv(index=False),
    file_name="nc_county_resilience_scores.csv",
    mime="text/csv"
)

# -------------------------------
# Methodology
# -------------------------------
st.markdown("### Methodology & FAQ")
st.markdown("""
**Resilience Score** = Weighted combination of normalized income, unemployment, and cost of living.  
Currently, unemployment and cost of living are placeholders.  
This helps identify vulnerable communities and guide equitable resource allocation.
""")

st.title("Test App")
st.write("If you see this, Streamlit is working!")