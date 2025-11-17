# Financial-Resilience
North Carolina County Resilience Dashboard

A real-time data dashboard using live U.S. Census income data + a high-resolution NC county map.

Project Preview

Overview

The NC County Resilience Dashboard visualizes financial resilience across all 100 North Carolina counties using real-time Census income data and a dynamic scoring model.

Users can:

Adjust weights (Income, Unemployment, Cost of Living)

Compare counties

Interact with a high-resolution NC map

Get AI-assisted insights on risks & interventions

This is designed for policy analysts, emergency planners, nonprofits, and researchers.

Features
Real-Time Resilience Scoring

The score blends:

Median Income (live from Census API)

Unemployment (placeholder, upgrade ready)

Cost of Living (placeholder, upgrade ready)

High-Resolution NC Map

A custom GeoJSON file renders all NC counties with:

Smooth borders

Dynamic coloring

Interactive hover tooltips

Visual Tools

Bar chart ranking counties

Detailed breakdown table

Selected-county insight summary

Export button for CSV scores

Sidebar AI Assistant

Rule-based assistant that gives suggestions for:

Flood risk

Hurricane preparation

Low-income resource allocation

County-level interventions

How the Resilience Score Works

Each factor is normalized to 0–1.
The formula:

Resilience Score =
   (Income Weight × Income_Norm)
 + (Unemployment Weight × (1 – Unemployment_Norm))
 + (Cost Weight × (1 – Cost_Norm))


Meaning:

Higher income → more resilience

Higher unemployment → less resilience

Higher cost of living → less resilience

Data Sources
Income Data (Live)

U.S. Census Bureau
ACS 2022 5-Year Estimates
Table B19013: Median Household Income

GeoJSON

High-resolution NC county boundaries.

Future Enhancements

Real unemployment + cost-of-living datasets

AI assistant powered by OpenAI

County economic history trends

Disaster vulnerability indicators

API endpoint for resilience exports
