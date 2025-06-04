import streamlit as st
import numpy as np
import pandas as pd
from energy_sim.simulation import simulate_day, GridTier

st.title("Residential Energy Deployment Simulator")

st.sidebar.header("Configuration")

# Default hourly curves
hours = np.arange(24)
base_usage = st.sidebar.slider("Average Hourly Usage (kWh)", 0.5, 5.0, 1.5, step=0.1)
usage_curve = base_usage + 0.5 * np.sin((hours - 7) / 24 * 2 * np.pi) + 0.3 * np.sin((hours - 17)/24*2*np.pi)

solar_size = st.sidebar.slider("Solar Array Size (kW)", 0.0, 10.0, 4.0, step=0.5)
# simple bell curve for solar generation
solar_curve = solar_size * np.exp(-0.5 * ((hours - 12)/3)**2)

battery_capacity = st.sidebar.slider("Battery Capacity (kWh)", 0.0, 20.0, 5.0, step=1.0)

# Grid pricing tiers
tier1_threshold = st.sidebar.number_input("Tier1 Threshold (kWh)", value=500.0)
tier1_price = st.sidebar.number_input("Tier1 Price ($/kWh)", value=0.15)
tier2_price = st.sidebar.number_input("Tier2 Price ($/kWh)", value=0.25)

tiers = [GridTier(threshold=tier1_threshold, price=tier1_price),
         GridTier(threshold=float('inf'), price=tier2_price)]

results = simulate_day(usage_curve, solar_curve, battery_capacity, tiers)

# Prepare dataframe for plotting
plot_df = pd.DataFrame({
    'Hour': hours,
    'Usage': usage_curve,
    'Solar': solar_curve,
    'Solar Used': results['solar_used'],
    'Battery Used': results['battery_used'],
    'Grid Used': results['grid_used'],
    'Battery Level': results['battery_level'],
})

st.subheader("Energy Usage vs Solar Generation")
st.line_chart(plot_df.set_index('Hour')[['Usage', 'Solar']])

st.subheader("Energy Source Breakdown")
source_df = plot_df[['Hour', 'Solar Used', 'Battery Used', 'Grid Used']].set_index('Hour')
st.area_chart(source_df)

st.subheader("Battery State of Charge")
st.line_chart(plot_df.set_index('Hour')[['Battery Level']])

solar_coverage = 100 * (results['solar_used'].sum() + results['battery_used'].sum()) / usage_curve.sum()
cost_without = tier1_price * usage_curve.sum()  # simple baseline

st.metric("Percent Covered by Solar/Battery", f"{solar_coverage:.1f}%")
st.metric("Estimated Grid Cost", f"${results['cost']:.2f}")
st.metric("Baseline Grid Cost", f"${cost_without:.2f}")
st.metric("Estimated Savings", f"${cost_without - results['cost']:.2f}")
