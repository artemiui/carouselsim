"""
Diagnostic analysis script for SM North EDSA 12 PM Clogging Phenomenon.

Simulates and analyzes the midday bottleneck (11:00 - 13:30) where buses stack up
in the dedicated busway lane directly behind the SM North EDSA station, causing
passengers on arriving buses to wait 10+ minutes in line just meters from the platform.
"""

import sys
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from edsa_carousel_sim.config import get_default_config, SimulationConfig
from edsa_carousel_sim.osm_network import build_network
from edsa_carousel_sim.engine import run_simulation
from edsa_carousel_sim.metrics import compute_metrics

def run_midday_analysis(output_dir: str = "output"):
    os.makedirs(output_dir, exist_ok=True)
    config = get_default_config()
    
    # Run full 24h cycle with SM North configured
    config.simulation_duration_hours = 24.0
    config.random_seed = 42
    
    network = build_network(config)
    sim_state = run_simulation(config, network)
    metrics = compute_metrics(sim_state)
    
    sm_north = sim_state.stations.get("SM North EDSA")
    if not sm_north:
        print("Error: SM North EDSA not found in simulation state.")
        return

    # Extract all bus arrivals at SM North EDSA
    bus_events = []
    for bus_id, bus in sim_state.buses.items():
        for event in bus.event_log:
            if event.get("station") == "SM North EDSA":
                bus_events.append({
                    "bus_id": bus_id,
                    "time_sec": event["time"],
                    "time_hour": event["time"] / 3600.0,
                    "event_type": event["event_type"],
                    "details": event.get("details", {})
                })
                
    df_events = pd.DataFrame(bus_events)
    
    # Filter for midday window (11:00 - 13:30)
    midday_events = df_events[
        (df_events["time_hour"] >= 11.0) & (df_events["time_hour"] <= 13.5)
    ].copy()
    
    print("\n" + "=" * 70)
    print("  DIAGNOSTIC REPORT: SM NORTH EDSA 12:00 PM CLOGGING PHENOMENON")
    print("=" * 70)
    print(f"Station Berth Capacity: {sm_north.station_def.berth_capacity} berths")
    print(f"Total Buses Served at SM North (24h): {len(sm_north.bus_arrival_times)}")
    print(f"Cumulative Bus Queue Delay: {sm_north.cumulative_bus_delay_sec / 60:.1f} minutes")
    print(f"Peak Buses in Queue Behind Station: {sm_north.max_bus_queue_count} buses")
    print(f"Max Physical Backup: {sm_north.max_bus_queue_count * 12:.0f} meters of busway blocked")
    print(f"Worst-case Single Bus Queue Wait: {sm_north.max_bus_queue_delay_sec / 60:.1f} minutes")
    
    # Analyze delays during 11:30 - 13:00 specifically
    # Extract queue delays from sim_state event log
    delays_at_sm_north = []
    for ev in sim_state.event_log:
        if ev["event_type"] == "BUS_DEPART_STATION" and ev.get("details", {}).get("station") == "SM North EDSA":
            t_hour = ev["time"] / 3600.0
            delay_sec = ev["details"].get("delay_sec", 0.0)
            delays_at_sm_north.append({
                "time_hour": t_hour,
                "delay_min": delay_sec / 60.0,
                "delay_sec": delay_sec,
                "bus_id": ev["entity_id"]
            })
            
    df_delays = pd.DataFrame(delays_at_sm_north)
    if not df_delays.empty:
        midday_delays = df_delays[(df_delays["time_hour"] >= 11.5) & (df_delays["time_hour"] <= 13.0)]
        if not midday_delays.empty:
            avg_midday_delay = midday_delays["delay_min"].mean()
            p90_midday_delay = midday_delays["delay_min"].quantile(0.90)
            max_midday_delay = midday_delays["delay_min"].max()
            print("\n--- Midday Peak Window (11:30 AM - 1:00 PM) Metrics ---")
            print(f"Average Bus Queue Wait: {avg_midday_delay:.2f} minutes")
            print(f"90th Percentile Bus Queue Wait: {p90_midday_delay:.2f} minutes")
            print(f"Maximum Bus Queue Wait: {max_midday_delay:.2f} minutes")
            
            # Count buses delayed > 5 mins and > 10 mins
            delayed_gt_5 = (midday_delays["delay_min"] >= 5.0).sum()
            delayed_gt_10 = (midday_delays["delay_min"] >= 10.0).sum()
            print(f"Buses stuck in line >= 5 minutes: {delayed_gt_5} buses")
            print(f"Buses stuck in line >= 10 minutes: {delayed_gt_10} buses")
    
    # Generate targeted visualization
    plt.figure(figsize=(14, 8))
    
    # Subplot 1: Bus Queue Delay over the 24h day at SM North EDSA
    plt.subplot(2, 1, 1)
    if not df_delays.empty:
        plt.scatter(df_delays["time_hour"], df_delays["delay_min"], alpha=0.6, color="crimson", s=30, label="Bus Queue Delay")
        plt.axhline(10.0, color="darkred", linestyle="--", linewidth=1.5, label="10-minute Delay Threshold (User Experience)")
        plt.axvspan(11.0, 13.5, color="orange", alpha=0.2, label="Midday Peak Window (11:00 - 13:30)")
        plt.axvspan(7.0, 9.5, color="blue", alpha=0.1, label="AM Peak (7:00 - 9:30)")
        plt.axvspan(17.0, 20.0, color="purple", alpha=0.1, label="PM Peak (17:00 - 20:00)")
        plt.title("SM North EDSA: Individual Bus Queue Delay Before Berth Entry (24-Hour Profile)", fontsize=13, fontweight='bold')
        plt.xlabel("Hour of Day (24h)", fontsize=11)
        plt.ylabel("Delay Waiting in Line (Minutes)", fontsize=11)
        plt.xlim(0, 24)
        plt.grid(True, linestyle=":", alpha=0.6)
        plt.legend(loc="upper left")

    # Subplot 2: Zoomed-in Midday Clog (11:00 AM - 14:00 PM)
    plt.subplot(2, 1, 2)
    if not df_delays.empty:
        zoom_df = df_delays[(df_delays["time_hour"] >= 11.0) & (df_delays["time_hour"] <= 14.0)].sort_values("time_hour")
        if not zoom_df.empty:
            plt.plot(zoom_df["time_hour"], zoom_df["delay_min"], marker='o', color='firebrick', linewidth=2, label="Bus Queue Wait Time")
            plt.axhline(10.0, color="darkred", linestyle="--", linewidth=1.5, label="10-minute User Delay Mark")
            plt.axvline(12.0, color="green", linestyle=":", linewidth=2, label="12:00 PM (Reported Clogging Time)")
            plt.title("Zoomed View: The 12:00 PM Clog at SM North EDSA Unloading Zone", fontsize=13, fontweight='bold')
            plt.xlabel("Hour of Day", fontsize=11)
            plt.ylabel("Minutes Stuck in Front of Station", fontsize=11)
            plt.xticks(np.arange(11.0, 14.1, 0.5), ["11:00 AM", "11:30 AM", "12:00 PM", "12:30 PM", "1:00 PM", "1:30 PM", "2:00 PM"])
            plt.grid(True, linestyle=":", alpha=0.6)
            plt.legend(loc="upper left")

    plt.tight_layout()
    plot_path = os.path.join(output_dir, "sm_north_12pm_clog_analysis.png")
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"\nDetailed diagnostic chart saved to: {plot_path}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    run_midday_analysis()
