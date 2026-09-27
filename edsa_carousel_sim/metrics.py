import pandas as pd
import numpy as np
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from edsa_carousel_sim.entities import SimulationState

logger = logging.getLogger(__name__)


@dataclass
class StationMetrics:
    """Metrics calculated for a single station."""
    name: str
    total_passengers_arrived: int
    total_passengers_boarded: int
    total_passengers_denied: int
    denial_rate: float
    avg_wait_time_sec: float
    max_queue_length: int
    cumulative_bus_delay_sec: float
    headway_mean_sec: float
    headway_std_sec: float
    headway_cv: float
    max_bus_queue_delay_sec: float = 0.0
    max_bus_queue_count: int = 0


@dataclass
class SystemMetrics:
    """Aggregated metrics for the entire EDSA Carousel system."""
    total_passengers_served: int
    total_passengers_denied: int
    overall_denial_rate: float
    avg_wait_time_sec: float
    median_wait_time_sec: float
    total_bus_trips: int
    avg_bus_occupancy: float
    top_bottleneck_stations: List[Tuple[str, float]]
    bus_bunching_severity: float
    station_metrics: List[StationMetrics]


def compute_metrics(sim_state: SimulationState) -> SystemMetrics:
    """
    Computes system-wide and per-station metrics from a completed simulation run.

    Args:
        sim_state: The completed SimulationState object.

    Returns:
        A SystemMetrics object containing all calculated metrics.
    """
    logger.info("Computing metrics from simulation state.")

    station_metrics_list = []
    
    # Calculate station metrics
    for name, station_queue in sim_state.stations.items():
        denial_rate = 0.0
        if station_queue.total_passengers_arrived > 0:
            denial_rate = station_queue.total_passengers_denied / station_queue.total_passengers_arrived
            
        avg_wait = 0.0
        if station_queue.passenger_wait_times:
            avg_wait = float(np.mean(station_queue.passenger_wait_times))
            
        headway_stats = station_queue.get_headway_stats()
        
        sm = StationMetrics(
            name=name,
            total_passengers_arrived=station_queue.total_passengers_arrived,
            total_passengers_boarded=station_queue.total_passengers_boarded,
            total_passengers_denied=station_queue.total_passengers_denied,
            denial_rate=denial_rate,
            avg_wait_time_sec=avg_wait,
            max_queue_length=station_queue.max_queue_length,
            cumulative_bus_delay_sec=station_queue.cumulative_bus_delay_sec,
            headway_mean_sec=headway_stats.get('mean', 0.0),
            headway_std_sec=headway_stats.get('std', 0.0),
            headway_cv=headway_stats.get('cv', 0.0),
            max_bus_queue_delay_sec=station_queue.max_bus_queue_delay_sec,
            max_bus_queue_count=station_queue.max_bus_queue_count,
        )
        station_metrics_list.append(sm)

    # Calculate system metrics
    total_served = sum(sm.total_passengers_boarded for sm in station_metrics_list)
    total_denied = sum(sm.total_passengers_denied for sm in station_metrics_list)
    total_arrived = sum(sm.total_passengers_arrived for sm in station_metrics_list)
    
    overall_denial_rate = 0.0
    if total_arrived > 0:
        overall_denial_rate = total_denied / total_arrived
        
    all_wait_times = []
    for sq in sim_state.stations.values():
        all_wait_times.extend(sq.passenger_wait_times)
        
    avg_sys_wait = float(np.mean(all_wait_times)) if all_wait_times else 0.0
    med_sys_wait = float(np.median(all_wait_times)) if all_wait_times else 0.0
    
    total_trips = sum(bus.trip_count for bus in sim_state.buses.values())
    
    avg_occupancy = 0.0
    total_bus_served = sum(bus.total_passengers_served for bus in sim_state.buses.values())
    if total_trips > 0:
        avg_occupancy = total_bus_served / total_trips

    # Top bottleneck stations
    station_delays = [(sm.name, sm.cumulative_bus_delay_sec) for sm in station_metrics_list]
    station_delays.sort(key=lambda x: x[1], reverse=True)
    top_bottlenecks = station_delays[:5]

    # Bus bunching severity (overall headway std across system)
    all_headways_std = [sm.headway_std_sec for sm in station_metrics_list if sm.headway_std_sec > 0]
    bunching_severity = float(np.mean(all_headways_std)) if all_headways_std else 0.0

    system_metrics = SystemMetrics(
        total_passengers_served=total_served,
        total_passengers_denied=total_denied,
        overall_denial_rate=overall_denial_rate,
        avg_wait_time_sec=avg_sys_wait,
        median_wait_time_sec=med_sys_wait,
        total_bus_trips=total_trips,
        avg_bus_occupancy=avg_occupancy,
        top_bottleneck_stations=top_bottlenecks,
        bus_bunching_severity=bunching_severity,
        station_metrics=station_metrics_list
    )
    
    return system_metrics


def print_executive_summary(metrics: SystemMetrics) -> None:
    """
    Prints a formatted executive summary report to the console.

    Args:
        metrics: The computed SystemMetrics.
    """
    print("=" * 50)
    print(" EDSA CAROUSEL SIMULATION - EXECUTIVE SUMMARY")
    print("=" * 50)
    print(f"Total Passengers Served: {metrics.total_passengers_served}")
    print(f"Total Passengers Denied: {metrics.total_passengers_denied} ({metrics.overall_denial_rate * 100:.2f}% denial rate)")
    print(f"Average Wait Time: {metrics.avg_wait_time_sec:.1f} seconds ({metrics.avg_wait_time_sec / 60:.1f} minutes)")
    print(f"Median Wait Time: {metrics.median_wait_time_sec:.1f} seconds")
    print(f"Total Bus Trips Completed: {metrics.total_bus_trips}")
    print(f"Bus Bunching Severity (Headway sigma): {metrics.bus_bunching_severity:.1f} seconds")
    print()
    print("--- Top 5 Bottleneck Stations ---")
    for i, (name, delay) in enumerate(metrics.top_bottleneck_stations, 1):
        print(f"{i}. {name} - {delay / 60:.1f} minutes cumulative delay")
    print()
    
    print("--- Per-Station Summary ---")
    header = f"{'Station':<22} | {'Arrived':>7} | {'Boarded':>7} | {'Avg Wait':>9} | {'Max Pax Q':>9} | {'Bus Del(m)':>10} | {'Peak Bus Q':>10} | {'Max Bus Wait':>12}"
    print(header)
    print("-" * len(header))
    for sm in metrics.station_metrics:
        print(f"{sm.name:<22} | {sm.total_passengers_arrived:>7} | {sm.total_passengers_boarded:>7} | "
              f"{sm.avg_wait_time_sec:>8.1f}s | {sm.max_queue_length:>9} | {sm.cumulative_bus_delay_sec/60:>9.1f}m | "
              f"{sm.max_bus_queue_count:>10} | {sm.max_bus_queue_delay_sec/60:>10.1f}m")


def get_event_dataframe(sim_state: SimulationState) -> pd.DataFrame:
    """
    Converts the simulation event log into a pandas DataFrame.

    Args:
        sim_state: The completed SimulationState object.

    Returns:
        A pandas DataFrame of all logged events.
    """
    return pd.DataFrame(sim_state.event_log)


def get_passenger_dataframe(sim_state: SimulationState) -> pd.DataFrame:
    """
    Converts the list of all passengers into a pandas DataFrame.

    Args:
        sim_state: The completed SimulationState object.

    Returns:
        A pandas DataFrame containing all passenger data.
    """
    passengers_data = []
    for p in sim_state.all_passengers:
        passengers_data.append({
            "id": p.id,
            "origin_station": p.origin_station,
            "destination_station": p.destination_station,
            "arrival_time": p.arrival_time,
            "board_time": p.board_time,
            "alight_time": p.alight_time,
            "denied": p.denied
        })
    return pd.DataFrame(passengers_data)
