"""Core SimPy discrete-event simulation engine for the EDSA Busway.

Implements realistic passenger generation with directional OD flows,
station queuing, berth contention, Bagong Barrio U-turn friction,
and Monumento/PITX terminal bus stacking.
"""

from __future__ import annotations
import logging
import simpy
import numpy as np
from typing import Dict, List, Any

from edsa_carousel_sim.config import SimulationConfig
from edsa_carousel_sim.osm_network import EDSANetwork, get_station_sequence, get_travel_time
from edsa_carousel_sim.entities import (
    Passenger, Bus, BusState, StationQueue, SimulationState,
)

logger = logging.getLogger(__name__)


def _get_rush_multiplier(sim_hour: float, station_name: str, config: SimulationConfig) -> float:
    """Return the demand multiplier for a station at a given hour of day."""
    for window in config.demand.rush_hour_windows:
        if window.start_hour <= sim_hour < window.end_hour:
            window_dict = config.demand.rush_hour_multipliers.get(window.label)
            if isinstance(window_dict, dict):
                return window_dict.get(station_name, 1.0)
            return config.demand.rush_hour_multipliers.get(station_name, 1.0)
    return 1.0


def passenger_generator(env: simpy.Environment, sim_state: SimulationState, rng: np.random.Generator):
    """
    Generates passengers at each station with realistic, directional OD patterns:
    - Munoz (AM): Commuters travel Southbound towards SM North, Cubao, Ortigas, Ayala, PITX.
    - Ayala/Guadalupe/Ortigas (PM): Commuters travel Northbound towards Munoz, Balintawak, Monumento.
    - SM North: High midday (12 PM) and evening (5 PM) mall & transfer traffic.
    - Trinoma: Common boarding and alighting in both directions.
    - Philam: Minimal passenger arrivals (rarely onloaded).
    - MOA: High destination attraction (offloading zone), minimal boarding lines.
    - Hotspots (Quezon Ave, Guadalupe, Cubao, Ayala): Large passenger lines.
    """
    passenger_id = 0
    config = sim_state.config
    station_defs = config.stations
    station_names = [st.name for st in station_defs]
    name_to_idx = {st.name: i for i, st in enumerate(station_defs)}
    num_stations = len(station_defs)

    while True:
        sim_hour = sim_state.get_sim_hour()

        # Batch generation every 60 simulation-seconds (1 minute)
        for orig_idx, st_def in enumerate(station_defs):
            orig_name = st_def.name
            sq = sim_state.stations[orig_name]

            # Base arrival rate (overrideable per station)
            base_rate = st_def.base_arrival_rate if st_def.base_arrival_rate is not None else config.demand.base_passenger_arrival_rate
            multiplier = _get_rush_multiplier(sim_hour, orig_name, config)
            rate_per_min = base_rate * multiplier

            n_arrivals = rng.poisson(max(rate_per_min, 0.0))

            for _ in range(n_arrivals):
                # Determine destination based on time-of-day directional demand
                possible_dests = [s for s in station_names if s != orig_name]
                if not possible_dests:
                    continue

                weights = []
                for d_name in possible_dests:
                    d_idx = name_to_idx[d_name]
                    is_southbound = (d_idx > orig_idx)
                    d_def = station_defs[d_idx]

                    w = 1.0
                    # Attraction multiplier from config
                    w *= _get_rush_multiplier(sim_hour, d_name, config)

                    # Directional commuting behavior:
                    # 1. Morning peak (7:00 - 9:30): Predominantly Southbound towards CBDs (Ayala, Ortigas, Buendia)
                    if 7.0 <= sim_hour < 9.5:
                        if is_southbound:
                            w *= 3.5
                            if any(k in d_name for k in ("Ayala", "Ortigas", "Buendia", "Cubao")):
                                w *= 2.5
                        else:
                            w *= 0.5

                    # 2. Evening peak (17:00 - 20:00): Predominantly Northbound towards residential north
                    elif 17.0 <= sim_hour < 20.0:
                        if not is_southbound:
                            w *= 3.5
                            if any(k in d_name for k in ("Fernando Poe", "Roosevelt", "Munoz", "Balintawak", "Monumento", "SM North")):
                                w *= 2.5  # High alighting in northern residential hubs!
                        else:
                            w *= 0.6

                    # 3. Midday peak (11:30 - 13:30): High attraction to SM North and Trinoma/North Ave
                    elif 11.5 <= sim_hour < 13.5:
                        if any(k in d_name for k in ("SM North", "North Avenue", "Trinoma")):
                            w *= 4.0

                    # 4. MOA as common offloading destination
                    if "MOA" in d_name or "Macapagal" in d_name:
                        w *= 2.5 * d_def.alighting_share_multiplier

                    # 5. Philam has minimal destination attraction
                    if "Philam" in d_name:
                        w *= 0.2

                    weights.append(max(w, 0.01))

                weights_arr = np.array(weights)
                p_sum = weights_arr.sum()
                probs = weights_arr / p_sum if p_sum > 0 else None

                dest_name = rng.choice(possible_dests, p=probs)
                dest_idx = name_to_idx[dest_name]

                # Assign direction based on relative position
                direction = 'forward' if dest_idx > orig_idx else 'reverse'

                passenger_id += 1
                pax = Passenger(
                    id=passenger_id,
                    origin_station=orig_name,
                    destination_station=dest_name,
                    direction=direction,
                    arrival_time=env.now,
                )
                sq.add_passenger(pax)
                sim_state.all_passengers.append(pax)

            if n_arrivals > 0:
                sim_state.log_event(
                    env.now, "QUEUE_UPDATE", orig_name,
                    {
                        "queue_length": sq.queue_length,
                        "forward_q": len(sq.waiting_forward),
                        "reverse_q": len(sq.waiting_reverse),
                        "arrivals": n_arrivals
                    },
                )

        yield env.timeout(60.0)


def bus_process(
    env: simpy.Environment,
    bus: Bus,
    sim_state: SimulationState,
    network: EDSANetwork,
    rng: np.random.Generator,
):
    """
    SimPy process: Models the physical and operational lifecycle of a bus:
    - Route transit with OSM travel times
    - Bagong Barrio U-turn stop friction
    - Station berth queuing & physical bus queue propagation
    - Passenger onloading (boarding) & offloading (alighting) dwell time
    - Terminal turnaround & bus stacking at Monumento / PITX
    """
    config = sim_state.config

    while True:
        station_sequence = get_station_sequence(network, bus.direction)
        if not station_sequence:
            logger.error("Empty station sequence for bus %d direction %s", bus.id, bus.direction)
            break

        for i, station_node in enumerate(station_sequence):
            station_name = station_node.name
            bus.current_station = station_name
            station_queue = sim_state.stations.get(station_name)
            if station_queue is None:
                continue

            # ── 1. Travel segment from previous station ──
            if i > 0:
                prev_name = station_sequence[i - 1].name
                travel_time = get_travel_time(network, prev_name, station_name)
                bus.state = BusState.EN_ROUTE
                bus.speed_kmh = config.network.bus_lane_speed_limit_kmh
                yield env.timeout(travel_time)

                # ── Operational Friction: Bagong Barrio U-Turn Stop ──
                # Between Monumento and Bagong Barrio, buses encounter U-turn traffic conflict
                if config.friction.enable_u_turn_friction:
                    if (prev_name == "Monumento" and station_name == "Bagong Barrio") or \
                       (prev_name == "Bagong Barrio" and station_name == "Monumento"):
                        if rng.random() < config.friction.u_turn_stop_probability:
                            u_delay = rng.uniform(
                                config.friction.u_turn_delay_range_sec[0],
                                config.friction.u_turn_delay_range_sec[1]
                            )
                            yield env.timeout(u_delay)
                            bus.log_event(env.now, "U_TURN_STOP_DELAY", "Bagong Barrio U-Turn", {"delay_sec": u_delay})

            # ── 2. Station Arrival & Berth Queuing ──
            target_pax_queue = station_queue.waiting_forward if bus.direction == 'forward' else station_queue.waiting_reverse
            has_alighting = any(p.destination_station == station_name for p in bus.passengers)
            has_waiting_pax = (len(target_pax_queue) > 0)
            is_terminal = station_queue.station_def.is_terminal

            # REFINEMENT: "If there are no pax, it doesn't clog!"
            # If no passengers want to alight, no passengers are waiting at the platform,
            # and it is not a terminal turnaround:
            # The bus does NOT occupy the berth and glides right through with ZERO delay and ZERO dwell!
            if not has_alighting and not has_waiting_pax and not is_terminal:
                bus.state = BusState.EN_ROUTE
                station_queue.record_bus_arrival(env.now)
                bus.log_event(env.now, "BYPASS_STATION_NO_PAX", station_name,
                              {"occupancy": bus.occupancy, "direction": bus.direction})
                continue

            bus.state = BusState.QUEUING_AT_STATION
            bus.speed_kmh = 0.0
            bus.log_event(env.now, "ARRIVE_STATION", station_name, {"occupancy": bus.occupancy, "direction": bus.direction})
            sim_state.log_event(env.now, "BUS_ARRIVE_STATION", str(bus.id),
                                {"station": station_name, "occupancy": bus.occupancy, "direction": bus.direction})

            # Physical lane separation: Southbound and Northbound buses queue in their OWN dedicated lanes!
            berth_resource = station_queue.get_berth_resource(bus.direction)

            with berth_resource.request() as req:
                queue_entry_time = env.now
                yield req

                queue_delay = env.now - queue_entry_time
                station_queue.cumulative_bus_delay_sec += queue_delay
                station_queue.bus_queue_delays.append(queue_delay)
                if queue_delay > station_queue.max_bus_queue_delay_sec:
                    station_queue.max_bus_queue_delay_sec = queue_delay

                if bus.direction == 'forward':
                    station_queue.cumulative_bus_delay_sec_forward += queue_delay
                    station_queue.bus_queue_delays_forward.append(queue_delay)
                else:
                    station_queue.cumulative_bus_delay_sec_reverse += queue_delay
                    station_queue.bus_queue_delays_reverse.append(queue_delay)

                # Passengers stuck in queued bus right outside destination
                for p in bus.passengers:
                    if p.destination_station == station_name:
                        p.station_clog_delay_sec += queue_delay

                # Physical bus queue count and distance tracking for this specific direction's lane
                bus_q_count = berth_resource.count + len(berth_resource.queue)
                if bus.direction == 'forward':
                    if bus_q_count > station_queue.max_bus_queue_count_forward:
                        station_queue.max_bus_queue_count_forward = bus_q_count
                else:
                    if bus_q_count > station_queue.max_bus_queue_count_reverse:
                        station_queue.max_bus_queue_count_reverse = bus_q_count
                if bus_q_count > station_queue.max_bus_queue_count:
                    station_queue.max_bus_queue_count = bus_q_count

                if queue_delay >= 480.0:  # 8+ minutes queuing
                    logger.warning(
                        "HEAVY BOTTLENECK (%s): Bus %d delayed %.1f min queuing for berth at %s "
                        "(sim_time=%.2f h, %d buses in queue, ~%.0f m backup)",
                        bus.direction.upper(), bus.id, queue_delay / 60.0, station_name,
                        env.now / 3600.0, bus_q_count, bus_q_count * bus.length_meters
                    )

                # ── 3. Platform Dwell: Onloading & Offloading ──
                bus.state = BusState.DWELLING
                n_boarded, n_alighted, dwell_time = station_queue.board_to_bus(
                    bus=bus,
                    dwell_config=config.dwell,
                    rng=rng,
                    sim_time=env.now,
                )
                if dwell_time > 0:
                    yield env.timeout(dwell_time)

                # ── Rogue Actor Lingering Behavior ("Nagpupuno" driver) ──
                # CRITICAL REFINEMENT: If there are NO passengers waiting on the platform,
                # the driver will NEVER linger! (No pax = no incentive/ability to nagpupuno).
                if config.friction.enable_rogue_actors and i < len(station_sequence) - 1:
                    target_queue = station_queue.waiting_forward if bus.direction == 'forward' else station_queue.waiting_reverse
                    if len(target_queue) > 0 and bus.occupancy < bus.capacity * 0.90:
                        prob = config.friction.rogue_actor_probability * (1.3 if station_queue.station_def.is_hotspot else 0.8)
                        if rng.random() < prob:
                            rogue_extra_sec = rng.uniform(
                                config.friction.rogue_extra_dwell_sec[0],
                                config.friction.rogue_extra_dwell_sec[1]
                            )
                            station_queue.set_active_rogue_bus(bus.direction, bus.id)
                            bus.log_event(env.now, "ROGUE_ACTOR_LINGERING", station_name,
                                          {"extra_dwell_sec": rogue_extra_sec, "initial_occ": bus.occupancy, "direction": bus.direction})
                            sim_state.log_event(env.now, "ROGUE_ACTOR_LINGERING", str(bus.id),
                                                {"station": station_name, "extra_dwell_sec": rogue_extra_sec, "direction": bus.direction})
                            
                            yield env.timeout(rogue_extra_sec)
                            
                            extra_boarded = station_queue.board_additional(bus, sim_time=env.now)
                            n_boarded += extra_boarded
                            station_queue.set_active_rogue_bus(bus.direction, None)
                            dwell_time += rogue_extra_sec

                station_queue.record_bus_arrival(env.now)

                bus.log_event(env.now, "DEPART_STATION", station_name,
                              {"boarded": n_boarded, "alighted": n_alighted, "occupancy": bus.occupancy, "direction": bus.direction})
                sim_state.log_event(env.now, "BUS_DEPART_STATION", str(bus.id),
                                    {"station": station_name, "boarded": n_boarded,
                                     "alighted": n_alighted, "delay_sec": queue_delay, "dwell_sec": dwell_time, "direction": bus.direction})

        # ── 4. Terminal Turnaround & Stacking ──
        bus.state = BusState.AT_TERMINAL
        bus.alight_passengers(bus.current_station, is_terminal=True, alighting_multiplier=1.0, rng=rng, sim_time=env.now)
        bus.trip_count += 1
        trip_duration = env.now - bus.current_trip_start_time
        bus.completed_trip_durations.append(trip_duration)

        bus.log_event(env.now, "TRIP_COMPLETE", bus.current_station,
                      {"direction": bus.direction, "trip": bus.trip_count, "duration_sec": trip_duration})
        sim_state.log_event(env.now, "TRIP_COMPLETE", str(bus.id),
                            {"direction": bus.direction, "trip": bus.trip_count, "duration_sec": trip_duration})

        # Monumento or PITX terminal bus stacking resource
        staging_resource = (
            sim_state.monumento_staging_resource if "Monumento" in bus.current_station
            else sim_state.pitx_staging_resource
        )

        with staging_resource.request() as stage_req:
            yield stage_req
            # Layover and staging recovery time
            yield env.timeout(config.friction.terminal_turnaround_sec)

        # Reverse direction for the next cycle
        bus.direction = "reverse" if bus.direction == "forward" else "forward"
        bus.current_trip_start_time = env.now
        bus.log_event(env.now, "START_TRIP", bus.current_station, {"direction": bus.direction})


def bus_dispatcher(
    env: simpy.Environment,
    sim_state: SimulationState,
    network: EDSANetwork,
    rng: np.random.Generator,
):
    """
    Dispatches buses from terminal staging stacks at regular intervals,
    alternating between Monumento (Southbound) and PITX (Northbound).
    """
    config = sim_state.config
    fleet_size = config.fleet.fleet_size
    dispatch_interval = config.fleet.dispatch_interval_seconds

    next_dir = "forward"

    for bus_idx in range(fleet_size):
        bus_id = bus_idx + 1
        bus = Bus(
            id=bus_id,
            capacity=config.fleet.bus_capacity,
            length_meters=config.fleet.bus_length_meters,
            max_boarding_per_stop=config.fleet.max_boarding_per_stop,
        )
        bus.direction = next_dir
        bus.current_trip_start_time = env.now
        sim_state.buses[bus_id] = bus
        sim_state.log_event(env.now, "BUS_DISPATCH", str(bus_id), {"direction": next_dir})
        bus.log_event(env.now, "START_TRIP", "Monumento" if next_dir == "forward" else "PITX", {"direction": next_dir})

        env.process(bus_process(env, bus, sim_state, network, rng))

        next_dir = "reverse" if next_dir == "forward" else "forward"

        if bus_idx < fleet_size - 1:
            yield env.timeout(dispatch_interval)


def run_simulation(config: SimulationConfig, network: EDSANetwork) -> SimulationState:
    """
    Initialises SimPy environment, builds terminal staging resources and
    station berth queues, launches processes, and runs the simulation.
    """
    env = simpy.Environment()
    rng = np.random.default_rng(config.random_seed)

    sim_state = SimulationState(env=env, config=config)

    # Monumento and PITX terminal staging stacks (multiple buses naturally stacked)
    sim_state.monumento_staging_resource = simpy.Resource(env, capacity=config.friction.monumento_stacking_capacity)
    sim_state.pitx_staging_resource = simpy.Resource(env, capacity=config.friction.pitx_stacking_capacity)

    # Initialise directional station berth resources (physically segregated median lanes)
    for station_def in config.stations:
        sq = StationQueue(station_def=station_def)
        sq.berth_resource_forward = simpy.Resource(env, capacity=station_def.berth_capacity)
        sq.berth_resource_reverse = simpy.Resource(env, capacity=station_def.berth_capacity)
        sq.berth_resource = sq.berth_resource_forward
        sim_state.stations[station_def.name] = sq

    # Launch background processes
    env.process(passenger_generator(env, sim_state, rng))
    env.process(bus_dispatcher(env, sim_state, network, rng))

    run_time = config.simulation_duration_hours * 3600.0
    logger.info("Starting EDSA Carousel simulation for %.1f hours (%.0f seconds)...", config.simulation_duration_hours, run_time)
    env.run(until=run_time)
    logger.info("Simulation completed.")

    return sim_state
