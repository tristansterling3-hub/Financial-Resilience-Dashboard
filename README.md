# Financial-Resilience
![Dashboard Preview](Screenshot_2025-11-16_dashboard.png)

North Carolina County Resilience Dashboard

A real-time data dashboard using live U.S. Census income data and a high-resolution North Carolina county map.

Overview

The NC County Resilience Dashboard visualizes financial resilience across all 100 North Carolina counties using real-time Census income data and an adjustable scoring model.

Users can:

Adjust weighting for Income, Unemployment, and Cost of Living

Compare counties using interactive charts

Explore a high-resolution geographic map

Receive basic rule-based insights regarding county risks and resource needs

This dashboard is intended for policy analysts, emergency planners, nonprofits, researchers, or anyone needing a clear overview of financial resilience across NC counties.

Features
Real-Time Resilience Scoring

The score incorporates:

Median Income (via live Census API)

Unemployment (placeholder for future upgrade)

Cost of Living (placeholder for future upgrade)

High-Resolution NC Map

A custom GeoJSON file provides:

Detailed county borders

Dynamic coloring based on resilience

Interactive hover information

Visual Tools

Bar chart ranking counties by resilience

Detailed breakdown table

Insight summary for selected counties

CSV export of resilience scores

Sidebar AI Assistant

A simple rule-based assistant offering suggestions related to:

Flood risk

Hurricane preparation

Low-income county support

County-level resource planning

How the Resilience Score Works

Each factor is normalized to a value between 0 and 1.

Formula:

Resilience Score =
   (Income Weight × Income_Norm)
 + (Unemployment Weight × (1 – Unemployment_Norm))
 + (Cost Weight × (1 – Cost_Norm))


Meaning:

Higher income increases resilience

Higher unemployment reduces resilience

Higher cost of living reduces resilience

Data Sources
Income Data (Live)

U.S. Census Bureau

ACS 2022 5-Year Estimates

Table B19013: Median Household Income

Geographic Data

High-resolution NC county boundary polygons (GeoJSON)

Future Enhancements

Integration of real unemployment and cost-of-living datasets

AI assistant using a large language model

County economic trend visualizations

Disaster vulnerability indicators

REST API for resilience score querying
