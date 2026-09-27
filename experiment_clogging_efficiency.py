"""
Transportation Systems Research Experiment:
Impact of Bus Overloading and Station Clogging on Corridor Efficiency.

Research Question:
Does overloading buses with passengers and allowing station queues to back up
make circulation more efficient, or does it trigger severe systemic congestion?

Metrics:
1. Passenger Wait-Times (Average & Median platform wait time)
2. Bus Roundtrip / Cycle Times (Trip duration from Monumento to PITX and vice-versa)
3. Fleet Productivity (Total roundtrips completed in 24 hours)
4. Bus Bunching Severity Index (Standard deviation of headways, sigma_H)
"""

import copy
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from edsa_carousel_sim.config import get_default_config, SimulationConfig
from edsa_carousel_sim.osm_network import build_network
from edsa_carousel_sim.engine import run_simulation
from edsa_carousel_sim.metrics import compute_metrics

def run_experiment():
    print("=" * 75)
    print(" TRANSPORT RESEARCH EXPERIMENT: OVERLOADING & CLOGGING VS EFFICIENCY")
    print("=" * 75)

    scenarios = {}

    # ── Scenario 1: Status Quo (Overloading & Clogging) ──
    # Single berth at SM North (capacity=1), full passenger crush loading (capacity=70),
    # extended dwell times as passengers push through doors.
    c1 = get_default_config()
    c1.simulation_duration_hours = 24.0
    c1.random_seed = 42
    c1.fleet.bus_capacity = 70  # Overloaded crush capacity
    for st in c1.stations:
        if st.name == "SM North EDSA":
            st.berth_capacity = 1
    scenarios["1. Overloaded & Clogged (Status Quo)"] = c1

    # ── Scenario 2: Load-Balanced / Fast-Dwell Policy (Anti-Overloading) ──
    # Buses cap passenger intake (capacity=50) to keep dwell times short and prevent
    # single buses from monopolizing berths. Rapid boarding/unloading turnover.
    c2 = copy.deepcopy(c1)
    c2.fleet.bus_capacity = 45  # Controlled load, faster passenger exchange
    c2.dwell.boarding_time_per_pax_sec = 1.8  # Smoother movement, less internal crowding
    scenarios["2. Regulated Loading (Fast Turnover)"] = c2

    # ── Scenario 3: De-Clogged Infrastructure (Anti-Clogging) ──
    # Eliminate the physical berth bottleneck at SM North (berth_capacity=2),
    # maintaining standard capacity (60).
    c3 = copy.deepcopy(c1)
    c3.fleet.bus_capacity = 60
    for st in c3.stations:
        if st.name == "SM North EDSA":
            st.berth_capacity = 2
    scenarios["3. De-Clogged Platform (Dual Berth)"] = c3

    # ── Scenario 4: Fully Optimized Busway (Anti-Overloading + Anti-Clogging) ──
    # Dual berths at major bottlenecks + off-board fare collection (t_board=1.0s, overhead=5s).
    c4 = copy.deepcopy(c3)
    c4.dwell.boarding_time_per_pax_sec = 1.0
    c4.dwell.alighting_time_per_pax_sec = 1.0
    c4.dwell.door_overhead_sec = 5.0
    scenarios["4. Modern BRT (Off-Board Fares + Dual Berths)"] = c4

    results = []

    for name, cfg in scenarios.items():
        print(f"\nRunning {name}...")
        net = build_network(cfg)
        sim_state = run_simulation(cfg, net)
        metrics = compute_metrics(sim_state)

        # Calculate trip durations (Roundtrip / one-way trip times)
        trip_durations = []
        for bus in sim_state.buses.values():
            start_times = {}
            for ev in bus.event_log:
                if ev["event_type"] == "START_TRIP":
                    start_times[ev.get("details", {}).get("direction", "forward")] = ev["time"]
                elif ev["event_type"] == "TRIP_COMPLETE":
                    dir_ = ev.get("details", {}).get("direction", "forward")
                    if dir_ in start_times:
                        duration_min = (ev["time"] - start_times[dir_]) / 60.0
                        if 15.0 < duration_min < 180.0:  # Valid trip duration filter
                            trip_durations.append(duration_min)

        avg_trip_time = float(np.mean(trip_durations)) if trip_durations else 0.0
        p90_trip_time = float(np.percentile(trip_durations, 90)) if trip_durations else 0.0
        p95_wait_time = float(np.percentile(
            [wt for sq in sim_state.stations.values() for wt in sq.passenger_wait_times], 95
        )) / 60.0 if any(sq.passenger_wait_times for sq in sim_state.stations.values()) else 0.0

        sm_north = sim_state.stations.get("SM North EDSA")
        sm_north_delay = (sm_north.cumulative_bus_delay_sec / 60.0) if sm_north else 0.0
        sm_max_bus_wait = (sm_north.max_bus_queue_delay_sec / 60.0) if sm_north else 0.0

        results.append({
            "Scenario": name,
            "Total Pax Served": metrics.total_passengers_served,
            "Avg Pax Wait (min)": metrics.avg_wait_time_sec / 60.0,
            "95th% Pax Wait (min)": p95_wait_time,
            "Avg Trip Time (min)": avg_trip_time,
            "Roundtrip Time (min)": avg_trip_time * 2.0,
            "Trips Completed": metrics.total_bus_trips,
            "Headway Sigma (sec)": metrics.bus_bunching_severity,
            "SM North Bus Delay (min)": sm_north_delay,
            "SM North Max Queue Wait (min)": sm_max_bus_wait,
        })

    df = pd.DataFrame(results)

    print("\n" + "=" * 105)
    print("                            RESEARCH EXPERIMENT RESULTS SUMMARY")
    print("=" * 105)
    print(f"{'Scenario':<42} | {'Avg Wait':>9} | {'Roundtrip':>10} | {'Trips':>6} | {'Headway std':>11} | {'SM Clog Wait':>12}")
    print("-" * 105)
    for r in results:
        print(f"{r['Scenario']:<42} | {r['Avg Pax Wait (min)']:>8.2f}m | {r['Roundtrip Time (min)']:>9.1f}m | "
              f"{r['Trips Completed']:>6} | {r['Headway Sigma (sec)']:>10.1f}s | {r['SM North Max Queue Wait (min)']:>11.1f}m")
    print("=" * 105)

    # ── Generate Comparative Visualizations ──
    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    fig.patch.set_facecolor('#ffffff')

    short_names = ["1. Overload & Clogged", "2. Regulated Load", "3. Dual Berth", "4. Modern BRT"]
    colors = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4']

    # Subplot 1: Passenger Wait Time
    ax = axes[0, 0]
    bars = ax.bar(short_names, df["Avg Pax Wait (min)"], color=colors, edgecolor='#333333', width=0.55)
    ax.set_title("Average Passenger Wait Time (Lower is Better)", fontsize=12, fontweight='bold')
    ax.set_ylabel("Minutes", fontsize=11)
    ax.grid(True, axis='y', linestyle=":", alpha=0.6)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, f"{bar.get_height():.2f}m", ha='center', fontsize=10, fontweight='bold')

    # Subplot 2: Roundtrip Time
    ax = axes[0, 1]
    bars = ax.bar(short_names, df["Roundtrip Time (min)"], color=colors, edgecolor='#333333', width=0.55)
    ax.set_title("Average Bus Roundtrip Cycle Time (Lower is Better)", fontsize=12, fontweight='bold')
    ax.set_ylabel("Minutes per Roundtrip", fontsize=11)
    ax.grid(True, axis='y', linestyle=":", alpha=0.6)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.0, f"{bar.get_height():.1f}m", ha='center', fontsize=10, fontweight='bold')

    # Subplot 3: Total Bus Trips Completed (Circulation Throughput)
    ax = axes[1, 0]
    bars = ax.bar(short_names, df["Trips Completed"], color=colors, edgecolor='#333333', width=0.55)
    ax.set_title("Total Bus Trips Completed in 24h (Higher is Better)", fontsize=12, fontweight='bold')
    ax.set_ylabel("Completed Trips", fontsize=11)
    ax.grid(True, axis='y', linestyle=":", alpha=0.6)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 30, f"{int(bar.get_height()):,}", ha='center', fontsize=10, fontweight='bold')

    # Subplot 4: Headway Instability (Bus Bunching Severity)
    ax = axes[1, 1]
    bars = ax.bar(short_names, df["Headway Sigma (sec)"], color=colors, edgecolor='#333333', width=0.55)
    ax.set_title("Bus Bunching Severity Index (σ of Headways) (Lower is Better)", fontsize=12, fontweight='bold')
    ax.set_ylabel("Headway Standard Deviation (Seconds)", fontsize=11)
    ax.grid(True, axis='y', linestyle=":", alpha=0.6)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5, f"{bar.get_height():.1f}s", ha='center', fontsize=10, fontweight='bold')

    plt.tight_layout()
    chart_path = "output/research_clogging_efficiency_experiment.png"
    plt.savefig(chart_path, dpi=200)
    plt.close()
    print(f"\nResearch experiment comparison chart saved to: {chart_path}\n")

if __name__ == "__main__":
    run_experiment()
