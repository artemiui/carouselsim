#!/usr/bin/env python3
"""Empirical Research Experiment: Impact of Bus Overloading, Queuing,
and Onloading/Offloading Dynamics on EDSA Carousel Circulation Efficiency.

Evaluates 4 operational scenarios under realistic 22-station corridor conditions:
1. Overloaded & Clogged (Status Quo Baseline): Crush load (70 pax), unregulated boarding, single-berth choke.
2. Regulated Onloading (Flow-Preserving Dwell): Metered boarding (max 25 pax/stop or 50 pax cap) to prevent berth blowout.
3. Headway-Tuned Dispatch: Paced 150s dispatch to align with onloading capacity.
4. Infrastructure De-Clogging: Dual-berth expansion at SM North and Guadalupe under standard onloading/offloading.

100% offline, pure Python & Matplotlib (no web tiles or external APIs).
"""

from __future__ import annotations
import sys
import os

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import time
import copy
import logging
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from edsa_carousel_sim.config import get_default_config, SimulationConfig, StationDefinition
from edsa_carousel_sim.osm_network import build_network
from edsa_carousel_sim.engine import run_simulation
from edsa_carousel_sim.metrics import compute_metrics, SystemMetrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_experiment_scenario(config: SimulationConfig, label: str) -> dict:
    """Executes a single simulation scenario and extracts key efficiency metrics."""
    logger.info("==================================================")
    logger.info("Executing Scenario: %s", label)
    logger.info("==================================================")
    
    t0 = time.time()
    network = build_network(config)
    sim_state = run_simulation(config, network)
    sys_metrics = compute_metrics(sim_state)
    elapsed = time.time() - t0
    
    # Calculate one-way and roundtrip cycle times from completed bus trips
    one_way_durations_min = []
    for bus in sim_state.buses.values():
        for dur in bus.completed_trip_durations:
            one_way_durations_min.append(dur / 60.0)

    mean_roundtrip_min = float(np.mean(one_way_durations_min)) * 2.0 if one_way_durations_min else 0.0
    median_roundtrip_min = float(np.median(one_way_durations_min)) * 2.0 if one_way_durations_min else 0.0
    mean_cycle_time = mean_roundtrip_min
    median_cycle_time = median_roundtrip_min

    # Extract station-specific bottleneck metrics
    st_dict = {sm.name: sm for sm in sys_metrics.station_metrics}
    sm_north_sm = st_dict.get("SM North EDSA")
    guadalupe_sm = st_dict.get("Guadalupe")
    munoz_sm = st_dict.get("Munoz / FPJ")
    ayala_sm = st_dict.get("Ayala")
    cubao_sm = st_dict.get("Cubao")

    # Passenger in-bus queue delay (stuck right outside destination)
    clog_delays = [p.station_clog_delay_sec for p in sim_state.all_passengers if p.station_clog_delay_sec > 0]
    avg_pax_clog_delay = float(np.mean(clog_delays)) / 60.0 if clog_delays else 0.0
    pax_affected_by_clog = len(clog_delays)

    res = {
        'label': label,
        'avg_wait_min': sys_metrics.avg_wait_time_sec / 60.0,
        'med_wait_min': sys_metrics.median_wait_time_sec / 60.0,
        'mean_cycle_time_min': mean_cycle_time,
        'median_cycle_time_min': median_cycle_time,
        'total_served': sys_metrics.total_passengers_served,
        'total_trips': sys_metrics.total_bus_trips,
        'headway_std_sec': sys_metrics.bus_bunching_severity,
        'sm_north_cum_delay_min': (sm_north_sm.cumulative_bus_delay_sec / 60.0) if sm_north_sm else 0.0,
        'sm_north_peak_bus_q': sm_north_sm.max_bus_queue_count if sm_north_sm else 0,
        'sm_north_max_wait_min': (sm_north_sm.max_bus_queue_delay_sec / 60.0) if sm_north_sm else 0.0,
        'guadalupe_cum_delay_min': (guadalupe_sm.cumulative_bus_delay_sec / 60.0) if guadalupe_sm else 0.0,
        'guadalupe_max_wait_min': (guadalupe_sm.max_bus_queue_delay_sec / 60.0) if guadalupe_sm else 0.0,
        'munoz_max_pax_q': munoz_sm.max_queue_length if munoz_sm else 0,
        'ayala_max_pax_q': ayala_sm.max_queue_length if ayala_sm else 0,
        'cubao_max_pax_q': cubao_sm.max_queue_length if cubao_sm else 0,
        'avg_pax_clog_delay_min': avg_pax_clog_delay,
        'pax_affected_by_clog': pax_affected_by_clog,
        'elapsed_sec': elapsed,
        'sim_state': sim_state,
        'sys_metrics': sys_metrics,
    }
    
    logger.info("Finished %s in %.2fs: AvgWait=%.2f min, CycleTime=%.1f min, Trips=%d, SMNorthDelay=%.1f min",
                label, elapsed, res['avg_wait_min'], res['mean_cycle_time_min'], res['total_trips'], res['sm_north_cum_delay_min'])
    return res


def main():
    logger.info("Initializing Realistic EDSA Carousel Research Experiment...")
    out_dir = os.path.abspath("output")
    os.makedirs(out_dir, exist_ok=True)

    # ─────────────────────────────────────────────────────────────
    # Configuration 1: Status Quo Baseline (Overloaded & Clogged)
    # - Bus capacity: 70 passengers (crush loading)
    # - Unregulated boarding (bus waits until full)
    # - Single-berth constraint at SM North
    # ─────────────────────────────────────────────────────────────
    cfg1 = get_default_config(is_weekend=False)
    cfg1.fleet.bus_capacity = 70
    cfg1.fleet.max_boarding_per_stop = None  # Unregulated loading
    label1 = "1. Overloaded & Clogged (Status Quo)"

    # ─────────────────────────────────────────────────────────────
    # Configuration 2: Regulated Onloading (Flow-Preserving Dwell)
    # - Bus capacity: 70 passengers
    # - Max 25 boarding passengers per stop (prevents dwell blowout)
    # ─────────────────────────────────────────────────────────────
    cfg2 = get_default_config(is_weekend=False)
    cfg2.fleet.bus_capacity = 70
    cfg2.fleet.max_boarding_per_stop = 25  # Capped onloading per stop
    label2 = "2. Regulated Onloading (Cap 25/stop)"

    # ─────────────────────────────────────────────────────────────
    # Configuration 3: Headway-Paced Dispatch (150s Interval)
    # - Reduces vehicle congestion by matching arrival rate to berth clearing capacity
    # ─────────────────────────────────────────────────────────────
    cfg3 = get_default_config(is_weekend=False)
    cfg3.fleet.bus_capacity = 60
    cfg3.fleet.dispatch_interval_seconds = 150.0  # Wider, stable spacing
    cfg3.fleet.max_boarding_per_stop = None
    label3 = "3. Headway-Paced Dispatch (150s)"

    # ─────────────────────────────────────────────────────────────
    # Configuration 4: Infrastructure De-Clogging (Dual Berths)
    # - Upgrades single-berth choke points (SM North: 2 berths, Guadalupe: 3 berths)
    # - Retains standard onloading/offloading (no off-board fares)
    # ─────────────────────────────────────────────────────────────
    cfg4 = get_default_config(is_weekend=False)
    cfg4.fleet.bus_capacity = 70
    cfg4.fleet.max_boarding_per_stop = None
    # Upgrade SM North to 2 berths and Guadalupe to 3 berths
    for st in cfg4.stations:
        if st.name == "SM North EDSA":
            st.berth_capacity = 2
        elif st.name == "Guadalupe":
            st.berth_capacity = 3
    label4 = "4. Dual Berth Expansion (SM North & Guad)"

    scenarios = [
        (cfg1, label1),
        (cfg2, label2),
        (cfg3, label3),
        (cfg4, label4),
    ]

    results = []
    for cfg, lbl in scenarios:
        res = run_experiment_scenario(cfg, lbl)
        results.append(res)

    # ─────────────────────────────────────────────────────────────
    # Summary Table Construction
    # ─────────────────────────────────────────────────────────────
    summary_rows = []
    for r in results:
        summary_rows.append({
            'Scenario': r['label'],
            'Avg Pax Wait (min)': f"{r['avg_wait_min']:.2f}",
            'Median Pax Wait (min)': f"{r['med_wait_min']:.2f}",
            'Mean Bus Cycle (min)': f"{r['mean_cycle_time_min']:.1f}",
            'Completed Trips': r['total_trips'],
            'Pax Served': f"{r['total_served']:,}",
            'Headway Std (s)': f"{r['headway_std_sec']:.1f}",
            'SM North Max Bus Queue': r['sm_north_peak_bus_q'],
            'SM North Max Wait (min)': f"{r['sm_north_max_wait_min']:.1f}",
            'Guadalupe Max Wait (min)': f"{r['guadalupe_max_wait_min']:.1f}",
            'Pax Clog Delay (min)': f"{r['avg_pax_clog_delay_min']:.1f}",
        })

    summary_df = pd.DataFrame(summary_rows)
    print("\n" + "=" * 90)
    print(" EXPERIMENT RESULTS: EDSA CAROUSEL QUEUING & ONLOADING/OFFLOADING EFFICIENCY")
    print("=" * 90)
    print(summary_df.to_string(index=False))
    print("=" * 90 + "\n")

    # ─────────────────────────────────────────────────────────────
    # High-Resolution Visualization Dashboard
    # ─────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    labels = [r['label'].split('(')[0].strip() for r in results]
    palette = ['#d62728', '#2ca02c', '#1f77b4', '#9467bd']

    # 1. Passenger Wait Times
    ax1 = axes[0, 0]
    wait_times = [r['avg_wait_min'] for r in results]
    bars1 = ax1.bar(labels, wait_times, color=palette, edgecolor='#333333', lw=1.2, width=0.55)
    ax1.set_ylabel("Average Passenger Wait Time (Minutes)", fontsize=11, fontweight='bold')
    ax1.set_title("Passenger Wait Times\n(Lower is Better)", fontsize=12, fontweight='bold')
    ax1.grid(True, axis='y', linestyle=':', alpha=0.6)
    for b in bars1:
        h = b.get_height()
        ax1.text(b.get_x() + b.get_width()/2., h + 0.08, f"{h:.2f}m", ha='center', va='bottom', fontweight='bold', fontsize=10)

    # 2. Bus Roundtrip Cycle Times
    ax2 = axes[0, 1]
    cycle_times = [r['mean_cycle_time_min'] for r in results]
    bars2 = ax2.bar(labels, cycle_times, color=palette, edgecolor='#333333', lw=1.2, width=0.55)
    ax2.set_ylabel("Mean Roundtrip Cycle Time (Minutes)", fontsize=11, fontweight='bold')
    ax2.set_title("Fleet Roundtrip Cycle Time\n(Lower = Faster Turnover, More Capacity)", fontsize=12, fontweight='bold')
    ax2.grid(True, axis='y', linestyle=':', alpha=0.6)
    for b in bars2:
        h = b.get_height()
        ax2.text(b.get_x() + b.get_width()/2., h + 0.6, f"{h:.1f}m", ha='center', va='bottom', fontweight='bold', fontsize=10)

    # 3. Peak Bus Queuing Delay at Bottlenecks
    ax3 = axes[1, 0]
    sm_delays = [r['sm_north_max_wait_min'] for r in results]
    guad_delays = [r['guadalupe_max_wait_min'] for r in results]
    x = np.arange(len(labels))
    w = 0.35
    b3_1 = ax3.bar(x - w/2, sm_delays, width=w, label='SM North EDSA', color='#e377c2', edgecolor='#333333')
    b3_2 = ax3.bar(x + w/2, guad_delays, width=w, label='Guadalupe', color='#17becf', edgecolor='#333333')
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels)
    ax3.set_ylabel("Peak Bus Queuing Delay (Minutes)", fontsize=11, fontweight='bold')
    ax3.set_title("Peak Bus Queuing Behind Stations\n(Time buses spend stuck in line before platform)", fontsize=12, fontweight='bold')
    ax3.legend(framealpha=0.9)
    ax3.grid(True, axis='y', linestyle=':', alpha=0.6)
    for b in b3_1:
        h = b.get_height()
        if h > 0.1:
            ax3.text(b.get_x() + b.get_width()/2., h + 0.15, f"{h:.1f}m", ha='center', va='bottom', fontsize=9)
    for b in b3_2:
        h = b.get_height()
        if h > 0.1:
            ax3.text(b.get_x() + b.get_width()/2., h + 0.15, f"{h:.1f}m", ha='center', va='bottom', fontsize=9)

    # 4. Completed Fleet Trips in 24 Hours
    ax4 = axes[1, 1]
    trips = [r['total_trips'] for r in results]
    bars4 = ax4.bar(labels, trips, color=palette, edgecolor='#333333', lw=1.2, width=0.55)
    ax4.set_ylabel("Total Trips Completed (24h)", fontsize=11, fontweight='bold')
    ax4.set_title("Fleet Productive Output\n(Completed Trips Delivered by 100 Buses)", fontsize=12, fontweight='bold')
    ax4.grid(True, axis='y', linestyle=':', alpha=0.6)
    for b in bars4:
        h = b.get_height()
        ax4.text(b.get_x() + b.get_width()/2., h + 20, f"{h:,}", ha='center', va='bottom', fontweight='bold', fontsize=10)

    for ax in axes.flat:
        ax.tick_params(axis='x', rotation=15)

    plt.suptitle("Empirical Evaluation: EDSA Carousel Circulation Efficiency\nUnder Realistic Station Queuing and Onloading/Offloading Dynamics",
                 fontsize=15, fontweight='bold', y=0.99)
    plt.tight_layout()
    chart_path = os.path.join(out_dir, "realistic_clogging_efficiency_experiment.png")
    plt.savefig(chart_path, dpi=200, bbox_inches='tight')
    plt.close()
    logger.info("Saved experiment visualization to %s", chart_path)


if __name__ == "__main__":
    main()
