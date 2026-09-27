import logging
import os
from typing import Optional

import numpy as np
import pandas as pd

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import folium
    from folium.plugins import HeatMap
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

from edsa_carousel_sim.entities import SimulationState
from edsa_carousel_sim.metrics import SystemMetrics, StationMetrics
from edsa_carousel_sim.osm_network import EDSANetwork
from edsa_carousel_sim.config import SimulationConfig

logger = logging.getLogger(__name__)


def safe_save_figure(fig, output_path: str, dpi: int = 200, bbox_inches: Optional[str] = 'tight') -> None:
    """Safely save a matplotlib figure with retries on Windows in case of transient file locking."""
    import time
    for attempt in range(3):
        try:
            fig.savefig(output_path, dpi=dpi, bbox_inches=bbox_inches)
            return
        except OSError as e:
            if attempt == 2:
                # If still locked, save with alternate suffix
                alt_path = output_path.replace(".png", "_new.png")
                logger.warning(f"Could not overwrite {output_path} ({e}). Saving to {alt_path}")
                fig.savefig(alt_path, dpi=dpi, bbox_inches=bbox_inches)
                return
            time.sleep(0.3)


def plot_station_delays(metrics: SystemMetrics, output_path: str = 'station_delays.png') -> None:
    """
    Generate a bar chart of cumulative bus delay per station, sorted descending.
    """
    if not HAS_MATPLOTLIB:
        logger.warning("Matplotlib is not installed. Skipping plot_station_delays.")
        return

    delays = [
        {'Station': sm.name, 'Cumulative Delay (s)': sm.cumulative_bus_delay_sec}
        for sm in metrics.station_metrics
    ]
    df = pd.DataFrame(delays).sort_values(by='Cumulative Delay (s)', ascending=False)

    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x='Station', y='Cumulative Delay (s)', hue='Station', palette='viridis', legend=False)
    plt.title("Cumulative Bus Delay per Station")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    safe_save_figure(plt.gcf(), output_path)
    plt.close()
    logger.info(f"Station delays plot saved to {output_path}")


def plot_passenger_wait_times(sim_state: SimulationState, output_path: str = 'wait_times.png') -> None:
    """
    Generate a box plot of passenger wait times by station.
    """
    if not HAS_MATPLOTLIB:
        logger.warning("Matplotlib is not installed. Skipping plot_passenger_wait_times.")
        return

    data = []
    for station_name, queue in sim_state.stations.items():
        for wt in queue.passenger_wait_times:
            data.append({'Station': station_name, 'Wait Time (s)': wt})

    if not data:
        logger.warning("No passenger wait times found to plot.")
        return

    df = pd.DataFrame(data)
    
    plt.figure(figsize=(14, 7))
    sns.boxplot(data=df, x='Station', y='Wait Time (s)', hue='Station', palette='Set2', legend=False)
    plt.title("Passenger Wait Times by Station")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    safe_save_figure(plt.gcf(), output_path)
    plt.close()
    logger.info(f"Wait times plot saved to {output_path}")


def plot_queue_over_time(sim_state: SimulationState, output_path: str = 'queue_trends.png') -> None:
    """
    Generate a line chart showing passenger queue size over time for the top 5 busiest stations.
    """
    if not HAS_MATPLOTLIB:
        logger.warning("Matplotlib is not installed. Skipping plot_queue_over_time.")
        return

    # Determine top 5 busiest stations by arrivals
    station_arrivals = {name: q.total_passengers_arrived for name, q in sim_state.stations.items()}
    top_5 = sorted(station_arrivals.keys(), key=lambda k: station_arrivals[k], reverse=True)[:5]

    if not top_5:
        logger.warning("No stations found for queue trends.")
        return

    time_series = []
    current_queues = {s: 0 for s in top_5}

    for event in sim_state.event_log:
        etype = event.get('event_type', '').lower()
        if 'passenger' in etype or 'queue' in etype:
            station = event.get('entity_id')
            if station in top_5:
                # Estimate queue size if not explicitly in details
                if 'arrive' in etype or 'arrival' in etype:
                    current_queues[station] += 1
                elif 'board' in etype:
                    current_queues[station] = max(0, current_queues[station] - 1)
                
                details = event.get('details', {})
                q_size = details.get('queue_size', current_queues[station])
                
                time_series.append({
                    'Station': station, 
                    'Time': event.get('time', 0), 
                    'Queue Size': q_size
                })

    if not time_series:
        logger.warning("No queue events found to plot.")
        return

    df = pd.DataFrame(time_series).sort_values(by='Time')

    plt.figure(figsize=(14, 7))
    for station in top_5:
        st_df = df[df['Station'] == station]
        # Use step to represent discrete changes in queue size
        plt.step(st_df['Time'], st_df['Queue Size'], where='post', label=station)

    plt.title("Queue Size Over Time (Top 5 Stations)")
    plt.xlabel("Simulation Time (s)")
    plt.ylabel("Queue Size")
    plt.legend()
    plt.tight_layout()
    safe_save_figure(plt.gcf(), output_path)
    plt.close()
    logger.info(f"Queue trends plot saved to {output_path}")


def plot_headway_distribution(sim_state: SimulationState, output_path: str = 'headway_dist.png') -> None:
    """
    Generate a histogram of headways across all stations.
    """
    if not HAS_MATPLOTLIB:
        logger.warning("Matplotlib is not installed. Skipping plot_headway_distribution.")
        return

    headways = []
    for station_name, queue in sim_state.stations.items():
        arr_times = sorted(queue.bus_arrival_times)
        if len(arr_times) > 1:
            diffs = np.diff(arr_times)
            headways.extend(diffs)
            
    if not headways:
        logger.warning("Not enough bus arrivals to calculate headways.")
        return
        
    plt.figure(figsize=(10, 6))
    sns.histplot(headways, bins=30, kde=True, color='purple')
    plt.title("Overall Bus Headway Distribution")
    plt.xlabel("Headway (s)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    safe_save_figure(plt.gcf(), output_path)
    plt.close()
    logger.info(f"Headway distribution plot saved to {output_path}")


def plot_demand_profile(sim_state: SimulationState, output_path: str = 'demand_profile.png') -> None:
    """
    Generate a line chart showing passenger arrivals per hour across the simulation.
    Highlights typical rush hour windows.
    """
    if not HAS_MATPLOTLIB:
        logger.warning("Matplotlib is not installed. Skipping plot_demand_profile.")
        return
        
    arrivals = [p.arrival_time for p in sim_state.all_passengers if p.arrival_time is not None]
    if not arrivals:
        logger.warning("No passenger arrivals found for demand profile.")
        return
        
    # Convert seconds to hours
    df = pd.DataFrame({'Arrival Hour': np.array(arrivals) / 3600.0})
    
    plt.figure(figsize=(12, 6))
    sns.histplot(data=df, x='Arrival Hour', bins=24, element="poly", color="orange", fill=False)
    plt.title("System-wide Passenger Demand Profile (Arrivals per Hour)")
    plt.xlabel("Hour of Simulation")
    plt.ylabel("Total Arrivals")
    
    # Highlight typical rush hours (7-9 AM, 5-7 PM)
    plt.axvspan(7, 9, color='red', alpha=0.1, label='Morning Peak (7-9)')
    plt.axvspan(17, 19, color='blue', alpha=0.1, label='Evening Peak (17-19)')
    
    plt.legend()
    plt.tight_layout()
    safe_save_figure(plt.gcf(), output_path)
    plt.close()
    logger.info(f"Demand profile plot saved to {output_path}")


def plot_route_schematic(sim_state: SimulationState, network: EDSANetwork, metrics: SystemMetrics, output_path: str = 'route_schematic.png') -> None:
    """
    Generate a pure vector transit route and bottleneck schematic without any map tile background.
    Plots the spatial geometry (Lon vs Lat) of the EDSA Busway with station bubbles sized by
    passenger demand and color-coded by bus queuing delay severity.
    Includes a linear corridor delay profile panel. 100% offline, zero network requests.
    """
    if not HAS_MATPLOTLIB:
        logger.warning("Matplotlib is not installed. Skipping plot_route_schematic.")
        return

    from matplotlib.lines import Line2D

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 10), gridspec_kw={'width_ratios': [1.2, 1]})
    fig.patch.set_facecolor('#ffffff')

    metrics_dict = {sm.name: sm for sm in metrics.station_metrics}

    # ── Left Panel: Spatial Route Diagram (Lon vs Lat) without map background ──
    ax1.set_facecolor('#fdfefe')
    
    # Route line connecting stations
    lons = [node.lon for node in network.station_nodes]
    lats = [node.lat for node in network.station_nodes]
    
    # Draw busway track
    ax1.plot(lons, lats, color='#1f77b4', linewidth=6, alpha=0.85, zorder=2, label='EDSA Dedicated Busway')
    ax1.plot(lons, lats, color='#aec7e8', linewidth=2, linestyle='--', alpha=0.9, zorder=3)

    # Plot stations
    for idx, node in enumerate(network.station_nodes):
        sm = metrics_dict.get(node.name)
        delay_min = (sm.cumulative_bus_delay_sec / 60.0) if sm else 0.0
        pax = sm.total_passengers_arrived if sm else 100
        
        # Color coding: Green (<15m), Orange (15-60m), Red (>60m)
        if delay_min < 15.0:
            color = '#2ca02c'  # Low Delay Green
        elif delay_min < 60.0:
            color = '#ff7f0e'  # Moderate Delay Orange
        else:
            color = '#d62728'  # Severe Bottleneck Red
            
        size = 100 + (pax / 5800.0) * 300
        
        ax1.scatter(node.lon, node.lat, s=size, color=color, edgecolors='#111111', linewidth=1.5, zorder=5)
        
        # Label offset alternating to avoid clutter
        x_offset = 0.0028 if idx % 2 == 0 else -0.0028
        ha = 'left' if x_offset > 0 else 'right'
        
        # Highlight top bottlenecks
        if delay_min > 500.0:
            peak_q = getattr(sm, 'max_bus_queue_count', 0)
            ax1.annotate(
                f"{node.name}\n({delay_min:.0f} min delay | {peak_q} bus queue)",
                xy=(node.lon, node.lat),
                xytext=(node.lon + x_offset * 1.6, node.lat + 0.004),
                fontsize=9, fontweight='bold', color='#800000',
                bbox=dict(boxstyle="round,pad=0.35", fc="#ffeaea", ec="#d62728", lw=1.5),
                arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.5),
                zorder=7, ha=ha
            )
        else:
            ax1.annotate(
                node.name,
                xy=(node.lon, node.lat),
                xytext=(node.lon + x_offset, node.lat),
                fontsize=8, color='#222222',
                zorder=6, ha=ha, va='center'
            )

    ax1.set_title("EDSA Busway: Spatial Route & Delay Schematic\n(Monumento to PITX - Pure Vector, No Map Background)", fontsize=13, fontweight='bold')
    ax1.set_xlabel("Longitude (°E)", fontsize=10)
    ax1.set_ylabel("Latitude (°N)", fontsize=10)
    ax1.grid(True, linestyle=":", alpha=0.5, color='#cccccc')
    
    legend_elements = [
        Line2D([0], [0], color='#1f77b4', lw=4, label='EDSA Dedicated Busway Line'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#2ca02c', markersize=10, label='Low Delay (<15 min)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ff7f0e', markersize=10, label='Moderate Delay (15-60 min)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#d62728', markersize=12, label='Severe Bottleneck (>60 min)'),
    ]
    ax1.legend(handles=legend_elements, loc='lower left', framealpha=0.95)

    # ── Right Panel: Linear Corridor Delay Profile ──
    ax2.set_facecolor('#ffffff')
    station_names = [node.name for node in network.station_nodes]
    delays_min = [(metrics_dict[name].cumulative_bus_delay_sec / 60.0) if name in metrics_dict else 0 for name in station_names]

    y_pos = np.arange(len(station_names))
    colors = ['#d62728' if d > 60 else ('#ff7f0e' if d > 15 else '#2ca02c') for d in delays_min]

    bars = ax2.barh(y_pos, delays_min, color=colors, edgecolor='#333333', height=0.68, zorder=3)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(station_names, fontsize=8)
    ax2.invert_yaxis()  # Top to bottom: Monumento to PITX
    ax2.set_xlabel("Cumulative Bus Queuing Delay (Minutes)", fontsize=10)
    ax2.set_title("Cumulative Delay by Station Along the Corridor", fontsize=13, fontweight='bold')
    ax2.grid(True, axis='x', linestyle=":", alpha=0.6)

    # Annotate values on bars
    for bar, delay in zip(bars, delays_min):
        if delay > 5:
            ax2.text(bar.get_width() + max(delays_min)*0.015, bar.get_y() + bar.get_height()/2,
                     f"{delay:.0f}m", va='center', fontsize=8, color='#222222', fontweight='bold' if delay > 60 else 'normal')

    plt.tight_layout()
    safe_save_figure(fig, output_path, dpi=200, bbox_inches='tight')
    plt.close()
    logger.info(f"Route schematic saved to {output_path}")


def generate_all_visualizations(sim_state: SimulationState, network: EDSANetwork, metrics: SystemMetrics, output_dir: str = '.') -> None:
    """
    Convenience function to generate all plots and route schematics (100% offline, zero map tile backgrounds).
    """
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("Starting generation of visualizations...")
    plot_station_delays(metrics, os.path.join(output_dir, 'station_delays.png'))
    plot_passenger_wait_times(sim_state, os.path.join(output_dir, 'wait_times.png'))
    plot_queue_over_time(sim_state, os.path.join(output_dir, 'queue_trends.png'))
    plot_headway_distribution(sim_state, os.path.join(output_dir, 'headway_dist.png'))
    plot_demand_profile(sim_state, os.path.join(output_dir, 'demand_profile.png'))
    plot_route_schematic(sim_state, network, metrics, os.path.join(output_dir, 'route_schematic.png'))
    logger.info("Finished generating all visualizations.")
