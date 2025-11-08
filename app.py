import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import openai

# Page setup
st.set_page_config(page_title="NC County Resilience Dashboard", layout="wide")

# Load Census data
@st.cache_data
def load_census_data():
    API_KEY = "c3b895c40dc66379b8b94a7716a0832ebea452d7"
    url = f"https://api.census.gov/data/2022/acs/acs5?get=NAME,B19013_001E&for=county:*&in=state:37&key={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        st.error(f"Census API request failed with status code {response.status_code}")
        st.text(response.text)
        st.stop()

    try:
        data = response.json()
    except Exception as e:
        st.error(f"Failed to parse JSON: {e}")
        st.text(response.text)
        st.stop()

    df = pd.DataFrame(data[1:], columns=data[0])
    df.rename(columns={"B19013_001E": "Median_Income"}, inplace=True)
    df["Median_Income"] = pd.to_numeric(df["Median_Income"], errors="coerce")
    df["County"] = df["NAME"].str.replace(" County, North Carolina", "", regex=False)
    return df

# Load hosted GeoJSON
@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/sieger1010/NorthCarolina-GeoJson/main/NCCountiesComplete.geo.json"
    response = requests.get(url)

    if response.status_code != 200:
        st.error(f"GeoJSON request failed with status code {response.status_code}")
        st.text(response.text)
        st.stop()

    try:
        geojson = response.json()
    except Exception as e:
        st.error(f"Failed to parse GeoJSON: {e}")
        st.text(response.text)
        st.stop()

    return geojson

df = load_census_data()
geojson = load_geojson()

# Sidebar: Weight sliders
st.sidebar.header("Adjust Score Weights")
w_income = st.sidebar.slider("Weight: Income", 0.0, 1.0, 1.0, 0.05)
w_unemp = st.sidebar.slider("Weight: Unemployment", 0.0, 1.0, 0.0, 0.05)
w_cost = st.sidebar.slider("Weight: Cost of Living", 0.0, 1.0, 0.0, 0.05)

# Normalize weights
total = w_income + w_unemp + w_cost
w_income, w_unemp, w_cost = w_income / total, w_unemp / total, w_cost / total

st.sidebar.markdown("Normalized Weights")
st.sidebar.write(f"- Income: {w_income:.2f}")
st.sidebar.write(f"- Unemployment: {w_unemp:.2f}")
st.sidebar.write(f"- Cost: {w_cost:.2f}")

# -------------------------------
# Calculate Resilience Score FIRST
# -------------------------------
df["Income_Norm"] = (df["Median_Income"] - df["Median_Income"].min()) / (df["Median_Income"].max() - df["Median_Income"].min())
df["Unemployment_Norm"] = 0.5  # placeholder
df["Cost_Norm"] = 0.5          # placeholder

df["Resilience_Score"] = (
    w_income * df["Income_Norm"] +
    w_unemp * (1 - df["Unemployment_Norm"]) +
    w_cost * (1 - df["Cost_Norm"])
).round(3)

# -------------------------------
# 🧠 AI Assistant (RAG)
# -------------------------------
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.docstore.document import Document

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Build documents from dataframe
docs = []
for _, row in df.iterrows():
    text = f"County: {row['County']}, Median Income: {row['Median_Income']}, Resilience Score: {row['Resilience_Score']}"
    docs.append(Document(page_content=text))

embeddings = OpenAIEmbeddings(openai_api_key=st.secrets["OPENAI_API_KEY"])
vectorstore = FAISS.from_documents(docs, embeddings)

retriever = vectorstore.as_retriever()
qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model="gpt-4", temperature=0.2, openai_api_key=st.secrets["OPENAI_API_KEY"]),
    retriever=retriever,
    return_source_documents=True
)

st.sidebar.markdown("---")
st.sidebar.subheader("🧠 AI Assistant (RAG)")
user_question = st.sidebar.text_area("Ask about county resilience")

if user_question:
    result = qa_chain({"query": user_question})
    st.sidebar.markdown("**AI Response:**")
    st.sidebar.write(result["result"])

    with st.sidebar.expander("Sources"):
        for doc in result["source_documents"]:
            st.sidebar.write(doc.page_content)

# -------------------------------
# Dashboard Visualizations
# -------------------------------
st.title("North Carolina County Financial Resilience Dashboard")
st.markdown("Explore financial resilience across NC counties using live Census data.")

# County Selector
selected_county = st.selectbox("Select a County", df["County"].sort_values())
score = df[df["County"] == selected_county]["Resilience_Score"].values[0]
st.metric(label=f"{selected_county} Resilience Score", value=round(score, 3))

# Rank
rank = df.sort_values("Resilience_Score", ascending=False).reset_index(drop=True)
position = rank[rank["County"] == selected_county].index[0] + 1
st.markdown(f"{selected_county} ranks #{position} out of {len(df)} counties.")

# Insight
income = df[df["County"] == selected_county]["Income_Norm"].values[0]
comment = []
if income > 0.75: comment.append("strong income levels")
elif income < 0.4: comment.append("low income levels")
insight = "This score reflects " + ", ".join(comment) + "." if comment else "This county has balanced income levels."
st.markdown(f"Insight: {insight}")

# Bar Chart
st.subheader("County Comparison")
fig_bar = px.bar(
    df.sort_values("Resilience_Score", ascending=False),
    x="County", y="Resilience_Score",
    title="Financial Resilience by County",
    labels={"Resilience_Score": "Resilience Score"},
    height=500
)
st.plotly_chart(fig_bar, use_container_width=True)

# Choropleth Map
st.subheader("North Carolina County Resilience Map")
fig_map = px.choropleth(
    df,
    geojson=geojson,
    locations="County",
    featureidkey="properties.NAME",
    color="Resilience_Score",
    color_continuous_scale="Viridis",
    labels={"Resilience_Score": "Resilience Score"},
    title="Resilience Score by County",
)
fig_map.update_geos(fitbounds="locations", visible=False)
st.plotly_chart(fig_map, use_container_width=True)

# Score Breakdown Table
st.subheader("Resilience Score Breakdown")
breakdown_df = df[[
    "County", "Median_Income", "Income_Norm", "Resilience_Score"
]].copy()
breakdown_df.columns = [
    "County", "Median Income", "Income (Normalized)", "Resilience Score"
]
st.dataframe(breakdown_df.round(3), use_container_width=True)

# Top & Bottom Rankings
st.subheader("County Resilience Rankings")
col1, col2 = st.columns(2)

with col1:
    st.markdown("Top 5 Most Resilient Counties")
    top5 = df.sort_values("Resilience_Score", ascending=False).head(5)[["County", "Resilience_Score"]]
    st.dataframe(top5, use_container_width=True)

with col2:
    st.markdown("Bottom 5 Least Resilient Counties")
    bottom5 = df.sort_values("Resilience_Score", ascending=True).head(5)[["County", "Resilience_Score"]]
    st.dataframe(bottom5, use_container_width=True)

# Download Button
st.download_button(
    label="Download County Resilience Scores",
    data=df.to_csv(index=False),
    file_name="nc_county_resilience_scores.csv",
    mime="text/csv"
)

# Methodology
st.markdown("Methodology & FAQ")
st.markdown("""
**What is the Resilience Score?**  
A data-driven estimate of how well a county could financially withstand a crisis.

**What data is it based on?**  
- Median Income (live from Census API)  
- Placeholder values for Unemployment and Cost of Living (to be added)

**Why does this matter?**  
Helps identify vulnerable communities and guide equitable resource allocation.

**Can I download the data?**  
Yes — use the button above to export the live dataset with your selected weights.
""")