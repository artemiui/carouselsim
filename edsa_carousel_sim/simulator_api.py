"""Simulation API module for dynamic, parameter-driven runs from the front-end dashboard.

Supports arbitrary start/end hour timeframes, operational parameter adjustments,
and time-slice snapshot generation for interactive playback.
"""

from __future__ import annotations
import time
import logging
from typing import Dict, List, Any, Tuple
import numpy as np
import simpy

from edsa_carousel_sim.config import get_default_config, SimulationConfig
from edsa_carousel_sim.osm_network import build_network, EDSANetwork
from edsa_carousel_sim.entities import StationQueue, SimulationState
from edsa_carousel_sim.engine import passenger_generator, bus_dispatcher

logger = logging.getLogger(__name__)

# Cached OSM network for fast repeated runs
_CACHED_NETWORK: EDSANetwork | None = None


def get_cached_network(cfg: SimulationConfig) -> EDSANetwork:
    """Builds or returns cached OSM network graph."""
    global _CACHED_NETWORK
    if _CACHED_NETWORK is None or len(_CACHED_NETWORK.station_nodes) != len(cfg.stations):
        logger.info(f"Initializing cached EDSANetwork with {len(cfg.stations)} stations...")
        _CACHED_NETWORK = build_network(cfg)
    return _CACHED_NETWORK


def run_simulation_window(params: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Executes a parameter-driven discrete-event simulation and returns snapshot time-slices
    for an arbitrary [start_hour, end_hour] timeframe.
    """
    start_hour = float(params.get('start_hour', 8.0))
    end_hour = float(params.get('end_hour', 11.0))
    step_minutes = float(params.get('step_minutes', 2.0))
    fleet_size = int(params.get('fleet_size', 100))
    dispatch_interval = float(params.get('dispatch_interval', 120.0))
    bus_capacity = int(params.get('bus_capacity', 60))
    sm_north_berths = int(params.get('sm_north_berths', 2))
    guadalupe_berths = int(params.get('guadalupe_berths', 2))
    rogue_prob = float(params.get('rogue_probability', 0.12))
    is_weekend = bool(params.get('is_weekend', False))

    if end_hour <= start_hour:
        end_hour = start_hour + 3.0

    # Build config
    cfg = get_default_config(is_weekend=is_weekend)
    cfg.fleet.fleet_size = fleet_size
    cfg.fleet.dispatch_interval_seconds = dispatch_interval
    cfg.fleet.bus_capacity = bus_capacity
    cfg.simulation_duration_hours = end_hour
    cfg.friction.rogue_actor_probability = rogue_prob
    cfg.friction.enable_rogue_actors = (rogue_prob > 0.0)

    # Station berth overrides
    for st in cfg.stations:
        if st.name == "SM North EDSA":
            st.berth_capacity = sm_north_berths
        elif st.name == "Guadalupe":
            st.berth_capacity = guadalupe_berths

    network = get_cached_network(cfg)

    # Initialize SimPy environment
    env = simpy.Environment()
    rng = np.random.default_rng(cfg.random_seed)
    sim_state = SimulationState(env=env, config=cfg)

    # Staging resources
    sim_state.monumento_staging_resource = simpy.Resource(env, capacity=cfg.friction.monumento_stacking_capacity)
    sim_state.pitx_staging_resource = simpy.Resource(env, capacity=cfg.friction.pitx_stacking_capacity)

    # Berth resources (Separate physical median lanes for SB and NB)
    for station_def in cfg.stations:
        sq = StationQueue(station_def=station_def)
        sq.berth_resource_forward = simpy.Resource(env, capacity=station_def.berth_capacity)
        sq.berth_resource_reverse = simpy.Resource(env, capacity=station_def.berth_capacity)
        sq.berth_resource = sq.berth_resource_forward
        sim_state.stations[station_def.name] = sq

    env.process(passenger_generator(env, sim_state, rng))
    env.process(bus_dispatcher(env, sim_state, network, rng))

    snapshots = []
    start_sec = start_hour * 3600.0
    end_sec = end_hour * 3600.0
    step_sec = step_minutes * 60.0

    def recorder_process():
        # Fast forward to start time if requested
        if start_sec > 0:
            yield env.timeout(start_sec)

        while env.now <= end_sec:
            now_sec = env.now
            sim_hour = (now_sec / 3600.0) % 24.0
            hh = int(sim_hour)
            mm = int((sim_hour - hh) * 60)
            ampm = "AM" if hh < 12 or hh == 24 else "PM"
            disp_hh = hh if hh <= 12 else hh - 12
            if disp_hh == 0:
                disp_hh = 12
            time_str = f"{disp_hh:02d}:{mm:02d} {ampm}"

            st_data = {}
            total_waiting = 0
            total_queuing_buses = 0
            total_dwelling_buses = 0

            for name, sq in sim_state.stations.items():
                fw = len(sq.waiting_forward)
                rv = len(sq.waiting_reverse)
                tot = fw + rv
                total_waiting += tot

                n_dwell_sb = sq.berth_resource_forward.count
                n_queue_sb = len(sq.berth_resource_forward.queue)
                n_dwell_nb = sq.berth_resource_reverse.count
                n_queue_nb = len(sq.berth_resource_reverse.queue)

                total_dwelling_buses += (n_dwell_sb + n_dwell_nb)
                total_queuing_buses += (n_queue_sb + n_queue_nb)

                delays_sb = sq.bus_queue_delays_forward[-10:] if sq.bus_queue_delays_forward else [0.0]
                avg_delay_sb = float(np.mean(delays_sb)) / 60.0

                delays_nb = sq.bus_queue_delays_reverse[-10:] if sq.bus_queue_delays_reverse else [0.0]
                avg_delay_nb = float(np.mean(delays_nb)) / 60.0

                st_data[name] = {
                    'pax_q_forward': fw,
                    'pax_q_reverse': rv,
                    'pax_q_total': tot,
                    'buses_dwelling': n_dwell_sb + n_dwell_nb,
                    'buses_queuing': n_queue_sb + n_queue_nb,
                    'buses_dwelling_sb': n_dwell_sb,
                    'buses_queuing_sb': n_queue_sb,
                    'buses_dwelling_nb': n_dwell_nb,
                    'buses_queuing_nb': n_queue_nb,
                    'max_bus_q': max(sq.max_bus_queue_count_forward, sq.max_bus_queue_count_reverse),
                    'max_bus_q_sb': sq.max_bus_queue_count_forward,
                    'max_bus_q_nb': sq.max_bus_queue_count_reverse,
                    'avg_delay_min': round(max(avg_delay_sb, avg_delay_nb), 1),
                    'avg_delay_min_sb': round(avg_delay_sb, 1),
                    'avg_delay_min_nb': round(avg_delay_nb, 1),
                    'has_rogue_bus_sb': (sq.active_rogue_bus_forward is not None),
                    'has_rogue_bus_nb': (sq.active_rogue_bus_reverse is not None),
                    'has_rogue_bus': (sq.active_rogue_bus_forward is not None or sq.active_rogue_bus_reverse is not None),
                    'rogue_bus_id_sb': sq.active_rogue_bus_forward,
                    'rogue_bus_id_nb': sq.active_rogue_bus_reverse,
                    'rogue_bus_id': sq.active_rogue_bus_forward or sq.active_rogue_bus_reverse,
                }

            # Directional Bottleneck Identification:
            # "If there are no pax, it doesn't clog" - a bottleneck ONLY exists if buses are queuing or a rogue is lingering!
            worst_st_sb = None
            max_q_sb = 0
            for s_name, d in st_data.items():
                if d['buses_queuing_sb'] > max_q_sb:
                    max_q_sb = d['buses_queuing_sb']
                    worst_st_sb = s_name
                elif d['has_rogue_bus_sb'] and max_q_sb == 0:
                    worst_st_sb = s_name

            worst_st_nb = None
            max_q_nb = 0
            for s_name, d in st_data.items():
                if d['buses_queuing_nb'] > max_q_nb:
                    max_q_nb = d['buses_queuing_nb']
                    worst_st_nb = s_name
                elif d['has_rogue_bus_nb'] and max_q_nb == 0:
                    worst_st_nb = s_name

            # Overall bottleneck
            worst_st = None
            if max_q_sb > 0 and max_q_sb >= max_q_nb:
                worst_st = worst_st_sb
            elif max_q_nb > 0:
                worst_st = worst_st_nb
            elif worst_st_sb:
                worst_st = worst_st_sb
            elif worst_st_nb:
                worst_st = worst_st_nb
            else:
                worst_st = "None (Free Flow)"

            snapshots.append({
                'time_sec': now_sec,
                'time_str': time_str,
                'hour': round(sim_hour, 2),
                'total_waiting_pax': total_waiting,
                'total_buses_queuing': total_queuing_buses,
                'total_buses_queuing_sb': sum(d['buses_queuing_sb'] for d in st_data.values()),
                'total_buses_queuing_nb': sum(d['buses_queuing_nb'] for d in st_data.values()),
                'total_buses_dwelling': total_dwelling_buses,
                'bottleneck_station': worst_st,
                'bottleneck_station_sb': worst_st_sb or "None (Free Flow)",
                'bottleneck_station_nb': worst_st_nb or "None (Free Flow)",
                'max_bus_queue': max(max_q_sb, max_q_nb),
                'max_bus_queue_sb': max_q_sb,
                'max_bus_queue_nb': max_q_nb,
                'has_active_rogue': any(d['has_rogue_bus'] for d in st_data.values()),
                'has_active_rogue_sb': any(d['has_rogue_bus_sb'] for d in st_data.values()),
                'has_active_rogue_nb': any(d['has_rogue_bus_nb'] for d in st_data.values()),
                'stations': st_data,
            })

            yield env.timeout(step_sec)

    env.process(recorder_process())

    t0 = time.time()
    env.run(until=end_sec)
    elapsed = time.time() - t0

    meta = {
        'start_hour': start_hour,
        'end_hour': end_hour,
        'step_minutes': step_minutes,
        'fleet_size': fleet_size,
        'dispatch_interval': dispatch_interval,
        'bus_capacity': bus_capacity,
        'sm_north_berths': sm_north_berths,
        'guadalupe_berths': guadalupe_berths,
        'is_weekend': is_weekend,
        'total_snapshots': len(snapshots),
        'elapsed_sec': round(elapsed, 2),
        'stations': [
            {
                'name': st.name,
                'lat': st.lat,
                'lon': st.lon,
                'berths': st.berth_capacity,
                'is_terminal': st.is_terminal,
                'is_hotspot': st.is_hotspot,
            }
            for st in cfg.stations
        ]
    }

    return snapshots, meta
