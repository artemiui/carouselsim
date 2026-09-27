# EDSA Carousel Busway Simulation Engine

A modular, parameter-driven discrete-event simulation of the **EDSA Busway (Carousel)** route in Metro Manila, running between **Monumento** and **PITX** (~37 km with road factor). Built with [SimPy](https://simpy.readthedocs.io/) for discrete-event simulation and optionally integrates [OSMnx](https://osmnx.readthedocs.io/) for real road-network geometry.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run a full 24-hour simulation with all outputs
python -m edsa_carousel_sim.run_simulation --output-dir output

# Run using downloaded OSM XML (100% offline, exact road geometry)
python -m edsa_carousel_sim.run_simulation --osm-xml edsa_corridor.osm --output-dir output

# Launch the Interactive Simulation Dashboard & Live Parameter Front End
python serve_map.py
# Opens http://localhost:8000/dashboard.html (tweak timeframes, fleet, berths, and run simulations live!)

# Quick smoke test (1 hour, 10 buses, no charts)
python -m edsa_carousel_sim.run_simulation --duration 1 --fleet-size 10 --no-viz
```

### CLI Arguments

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--osm-xml` | str | `None` | Path to local `.osm` / `.xml` file for 100% offline OSM routing |
| `--seed` | int | `42` | Random seed for reproducibility |
| `--duration` | float | `24.0` | Simulation duration (hours) |
| `--fleet-size` | int | `100` | Total number of buses to dispatch |
| `--dispatch-interval` | float | `120` | Seconds between bus dispatches from terminals |
| `--output-dir` | str | `.` | Directory for output charts and map |
| `--verbose` | flag | off | Enable DEBUG-level logging |
| `--no-viz` | flag | off | Skip all visualization/chart generation |

---

## Project Structure

```
edsa_carousel_sim/
├── __init__.py          # Package marker
├── config.py            # Centralized configuration (all dataclasses)
├── osm_network.py       # OSM graph download, station mapping, segment distances
├── entities.py          # Domain objects: Bus, Passenger, StationQueue, SimulationState
├── engine.py            # SimPy processes: passenger gen, bus lifecycle, dispatcher
├── metrics.py           # Post-run analytics: per-station & system-wide metrics
├── visualize.py         # Matplotlib charts + Folium interactive map
└── run_simulation.py    # CLI entry point orchestrating the full pipeline
```

---

## Architecture Overview

### Data Flow

```
get_default_config()          CLI overrides
        │                         │
        ▼                         ▼
   SimulationConfig ──────► build_network() ──► EDSANetwork
        │                                           │
        ▼                                           ▼
   run_simulation(config, network) ──► SimulationState
        │                                    │
        ▼                                    ▼
   compute_metrics(sim_state)      generate_all_visualizations()
        │                                    │
        ▼                                    ▼
   print_executive_summary()        PNG charts + HTML map
```

### Module Dependency Graph

```
config.py ◄── osm_network.py
    ▲              ▲
    │              │
entities.py ◄── engine.py
    ▲              ▲
    │              │
metrics.py    run_simulation.py
    ▲              │
    │              │
visualize.py ◄─────┘
```

`config.py` has zero internal imports — everything flows outward from it. `run_simulation.py` is the only module that imports from all others.

---

## Module Reference

### `config.py` — Configuration Schema

All simulation parameters live here. **No simulation logic or magic numbers exist anywhere else.** Users tune behavior by editing `get_default_config()` or overriding fields after construction.

#### Dataclasses

| Class | Key Fields | Purpose |
|-------|-----------|---------|
| `NetworkConfig` | `osm_corridor_bbox`, `bus_lane_speed_limit_kmh`, `osm_network_type` | OSM bounding box & speed limit |
| `StationDefinition` | `name`, `lat`, `lon`, `platform_type`, `berth_capacity`, `is_terminal` | Per-station static properties |
| `FleetConfig` | `fleet_size`, `dispatch_interval_seconds`, `bus_capacity`, `bus_length_meters` | Bus fleet parameters |
| `DwellConfig` | `boarding_time_per_pax_sec`, `alighting_time_per_pax_sec`, `door_overhead_sec` | Dwell time formula inputs |
| `RushHourWindow` | `start_hour`, `end_hour`, `label` | Time-of-day peak period definition |
| `DemandConfig` | `rush_hour_windows`, `base_passenger_arrival_rate`, `rush_hour_multipliers`, `alighting_fraction_range` | Demand model parameters |
| `SimulationConfig` | Composes all above + `simulation_duration_hours`, `random_seed`, `enable_overtaking` | Top-level config object |

#### Important: `rush_hour_multipliers`

This is structured as `Dict[str, Dict[str, float]]` keyed by window label (`"AM Peak"`, `"Midday Peak"`, `"PM Peak"`), then by **station name**. During each window, the station's base passenger arrival rate is scaled by its specific multiplier:
- **AM & PM Commuter Peaks (7:00–9:30, 17:00–20:00)**: 4.0× for major transfer hubs, 1.5× for local stops.
- **Midday Peak (11:00–13:30)**: Extreme **6.0× surge at SM North EDSA** capturing mall lunch-hour and shopping foot traffic, with 2.0–3.0× spillover to adjacent stops.

#### Station List

20 stations in order: Monumento (Terminal) → Bagong Barrio → Balintawak → Kaingin Road → **SM North EDSA** → North Avenue → Quezon Avenue → GMA Kamuning → Cubao → Santolan-Annapolis → Ortigas → Shaw Boulevard → Crossing/Pioneer → Guadalupe → Buendia/Sen. Gil Puyat → Ayala → Magallanes → Taft Avenue → Macapagal/MOA → PITX (Terminal).

Berth capacities: 4 (Monumento, North Avenue, Cubao, Ayala, PITX), 3 (Ortigas, Shaw Blvd, Guadalupe, Magallanes, Taft Ave), 2 (most median stops), and **1 (SM North EDSA)** reflecting its single functional unloading bay that causes severe midday bus queues.

---

### Midday Clogging Case Study: SM North EDSA (12:00 PM)

Run `python analyze_sm_north_clog.py` to inspect the 12:00 PM bottleneck:
- **Physical Root Cause**: Single active berth slot (`berth_capacity = 1`) + high alighting/boarding exchange (dwell time ~90–120s per bus) + 120s dispatch headway.
- **Queue Propagation**: Arriving buses cannot overtake and must stack up in the dedicated busway lane upstream of the station.
- **Simulation Findings**: Peak queue reaches **35 buses** (~420 meters physical backup), with individual bus delays exceeding **10 to 14.2 minutes** right in front of the platform between 11:50 AM and 12:20 PM.

### `osm_network.py` — Network & Routing

#### Key Types

- **`StationNode`** — A station mapped to the road network (`name`, `lat`, `lon`, `osm_node_id`, `order_index`).
- **`RouteSegment`** — A segment between two consecutive stations (`from_station`, `to_station`, `distance_meters`, `travel_time_seconds`).
- **`EDSANetwork`** — Container holding `station_nodes`, `segments_forward` (Monumento→PITX), `segments_reverse` (PITX→Monumento), `total_distance_meters`, and optionally the raw `osm_graph`.

#### Key Functions

| Function | Signature | Notes |
|----------|-----------|-------|
| `build_network` | `(config: SimulationConfig) → EDSANetwork` | Tries OSMnx, falls back to haversine × 1.3 |
| `get_station_sequence` | `(network, direction='forward') → list[StationNode]` | Returns ordered station list |
| `get_travel_time` | `(network, from_station, to_station) → float` | Seconds between consecutive stations |
| `haversine_distance` | `(lat1, lon1, lat2, lon2) → float` | Great-circle distance in meters |

#### OSM Fallback Behavior

`osmnx` and `networkx` are imported separately with `try/except`. If `osmnx` is unavailable (common — it requires GDAL/Fiona), the module silently falls back to **haversine distances × 1.3 road factor**. The simulation works identically either way; only segment distances differ.

---

### `entities.py` — Domain Objects

#### `Passenger` (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Unique passenger ID |
| `origin_station` | `str` | Station name where passenger arrives |
| `destination_station` | `str` | Target station name |
| `arrival_time` | `float` | SimPy timestamp when passenger joined queue |
| `board_time` | `float` | When they boarded a bus (-1 if not yet) |
| `alight_time` | `float` | When they got off (-1 if not yet) |
| `denied` | `bool` | True if left behind due to full buses |

#### `Bus` (class)

Constructed with `Bus(id, capacity, length_meters)`. Key properties:

- `occupancy` → current passenger count
- `remaining_capacity` → seats available
- `board_passengers(passengers, sim_time)` → load passengers, set `board_time`
- `alight_passengers(station_name, fraction_range, rng, sim_time)` → remove a random fraction; removes ALL at terminal stations (checks name against `"pitx"` / `"monumento"`, case-insensitive)
- `state` → `BusState` enum: `IDLE`, `EN_ROUTE`, `QUEUING_AT_STATION`, `DWELLING`, `AT_TERMINAL`, `BROKEN_DOWN`
- `event_log` → list of `{time, event_type, station, details}` dicts

#### `StationQueue` (class)

Constructed with `StationQueue(station_def: StationDefinition)`. The `berth_resource` field is set to a `simpy.Resource` during engine initialization — it is **not** set in the constructor.

Key method — `board_to_bus`:
```python
def board_to_bus(self, bus, dwell_config, alighting_fraction_range, rng, sim_time)
    -> tuple[int, int, float]   # (n_boarded, n_alighted, dwell_time)
```
Dwell formula: `T_dwell = door_overhead_sec + max(n_on × boarding_time_per_pax_sec, n_off × alighting_time_per_pax_sec)`

**Denial tracking**: after boarding, if the bus is full and passengers remain in queue, `total_passengers_denied` is incremented by the remaining queue length.

#### `InterventionEngine` (ABC)

Abstract base class for runtime scenario injection:
```python
class InterventionEngine(ABC):
    @abstractmethod
    def trigger(self, env, sim_state, event_type: str, **kwargs): ...
```
Subclass this to implement bus breakdowns, express services, or holding strategies. Register instances via `sim_state.interventions.append(my_intervention)`.

#### `SimulationState`

Constructed with `SimulationState(env, config)`. Contains:
- `buses: Dict[int, Bus]` — all active buses
- `stations: Dict[str, StationQueue]` — keyed by station name
- `event_log: List[dict]` — global event log (`{time, event_type, entity_id, details}`)
- `all_passengers: List[Passenger]` — every passenger created
- `interventions: List[InterventionEngine]` — registered hooks
- `get_sim_hour() → float` — converts `env.now` to hour-of-day (0–24)

---

### `engine.py` — SimPy Processes

#### Process: `passenger_generator(env, sim_state, rng)`

Runs in an infinite loop, batching every 60 simulation-seconds. For each station:
1. Computes current `rush_multiplier` via `_get_rush_multiplier(sim_hour, station_name, config)`.
2. Draws `n_arrivals ~ Poisson(base_rate × multiplier)`.
3. Each passenger gets a weighted-random destination (3× weight for major hubs).
4. Logs `QUEUE_UPDATE` events to `sim_state.event_log`.

#### Process: `bus_process(env, bus, sim_state, network, rng)`

Full bus lifecycle in an infinite loop:
1. Gets station sequence for current `bus.direction`.
2. For each station (skipping travel for the first station of a trip):
   - **Travel**: `yield env.timeout(travel_time)` with `bus.state = EN_ROUTE`.
   - **Queue for berth**: `with station_queue.berth_resource.request() as req: yield req` — tracks queue delay.
   - **Dwell**: Calls `station_queue.board_to_bus(...)`, yields `env.timeout(dwell_time)`.
   - Records `BUS_ARRIVE_STATION`, `BUS_DEPART_STATION` events with occupancy/delay details.
3. At terminal: alight all passengers, 300s turnaround, reverse direction, increment `trip_count`.

#### Process: `bus_dispatcher(env, sim_state, network, rng)`

Dispatches buses alternating forward/reverse at `dispatch_interval_seconds` until `fleet_size` is reached. Each bus gets its own `bus_process` coroutine.

#### Entry Point: `run_simulation(config, network) → SimulationState`

Creates `simpy.Environment`, initializes all `StationQueue` objects with `simpy.Resource(env, capacity=berth_capacity)`, seeds `np.random.default_rng(config.random_seed)`, starts `passenger_generator` + `bus_dispatcher`, and runs `env.run(until=duration_hours × 3600)`.

---

### `metrics.py` — Post-Run Analytics

#### `StationMetrics` (dataclass)

Per-station: `name`, `total_passengers_arrived`, `total_passengers_boarded`, `total_passengers_denied`, `denial_rate`, `avg_wait_time_sec`, `max_queue_length`, `cumulative_bus_delay_sec`, `headway_mean_sec`, `headway_std_sec`, `headway_cv`.

#### `SystemMetrics` (dataclass)

System-wide: `total_passengers_served`, `total_passengers_denied`, `overall_denial_rate`, `avg_wait_time_sec`, `median_wait_time_sec`, `total_bus_trips`, `avg_bus_occupancy`, `top_bottleneck_stations` (top 5 by cumulative delay), `bus_bunching_severity` (mean of per-station headway σ), `station_metrics` (list).

#### Key Functions

| Function | Returns | Description |
|----------|---------|-------------|
| `compute_metrics(sim_state)` | `SystemMetrics` | Aggregates all station and system metrics |
| `print_executive_summary(metrics)` | `None` | ASCII-safe formatted console report |
| `get_event_dataframe(sim_state)` | `pd.DataFrame` | Global event log as DataFrame |
| `get_passenger_dataframe(sim_state)` | `pd.DataFrame` | All passengers as DataFrame |

---

### `visualize.py` — Charts & Maps

All visualization functions use Matplotlib/Seaborn and run 100% offline with zero external network requests or map tile servers.

| Function | Output | Description |
|----------|--------|-------------|
| `plot_station_delays(metrics, path)` | PNG | Bar chart, sorted descending by cumulative delay |
| `plot_passenger_wait_times(sim_state, path)` | PNG | Box plot of wait times by station |
| `plot_queue_over_time(sim_state, path)` | PNG | Step chart for top 5 busiest stations from event log |
| `plot_headway_distribution(sim_state, path)` | PNG | Histogram with KDE of bus headways |
| `plot_demand_profile(sim_state, path)` | PNG | Hourly arrival density with rush-hour shading |
| `plot_route_schematic(sim_state, network, metrics, path)` | PNG | 2-panel transit schematic (spatial route arc + linear corridor delay profile, no map background) |
| `generate_all_visualizations(sim_state, network, metrics, output_dir)` | All above | Convenience wrapper generating all 6 static charts |

> **Map-Free Spatial Visualization**:
> Web-based map tile dependencies have been removed. The spatial route layout is rendered as a clean, publication-grade vector transit schematic (`route_schematic.png`) plotting stations at their true coordinates, connected by the EDSA busway line, with station bubble sizes proportional to passenger demand and color-coded by delay severity. It operates 100% offline with zero HTTP 403 / tile blocking issues.

---

## Simulation Model Details

### Passenger Arrival Model

Non-homogeneous Poisson process. Every 60 simulation-seconds, for each station:

```
λ(t, station) = base_passenger_arrival_rate × rush_multiplier(station, hour(t))
n_arrivals ~ Poisson(λ)
```

- **Off-peak**: `λ = 2.0` pax/min (default)
- **Rush hour at major hub**: `λ = 2.0 × 4.0 = 8.0` pax/min
- **Rush hour at local stop**: `λ = 2.0 × 1.5 = 3.0` pax/min

### Dwell Time Formula

```
T_dwell = T_overhead + max(N_on × t_board, N_off × t_alight)
```

Default: `T_dwell = 10 + max(N_on × 2.5, N_off × 1.5)` seconds.

Boarding and alighting happen in parallel (max, not sum), which models multiple-door buses.

### Alighting Model

At each intermediate stop, a fraction `f ~ Uniform(0.05, 0.30)` of on-board passengers alight. At terminal stations (Monumento, PITX), **all** passengers alight.

### Station Berthing

Each station has a `simpy.Resource(capacity=berth_capacity)`. When a bus arrives:
1. It requests a berth slot.
2. If all berths are occupied, the bus waits (simulating physical queuing in the busway lane).
3. Queue delay is tracked in `station_queue.cumulative_bus_delay_sec`.
4. Overtaking is disabled by default (`config.enable_overtaking = False`) — buses process berth requests sequentially.

### Travel Time

```
T_travel = distance_meters / (bus_lane_speed_limit_kmh × 1000 / 3600)
```

Default: 50 km/h → 13.89 m/s. With haversine fallback, total route ≈ 37.2 km, so end-to-end free-flow time ≈ 44.6 minutes.

---

## How to Extend

### Adding a New Station

Edit `get_default_config()` in `config.py`. Insert a new `StationDefinition` into the `stations` list at the correct geographic position. Add its name to `rush_hour_multipliers` if it's a major hub.

### Changing Demand Patterns

Modify `DemandConfig` fields:
- Add new `RushHourWindow` entries for midday or late-night peaks.
- Adjust `base_passenger_arrival_rate` for system-wide throughput.
- Set per-station multipliers in `rush_hour_multipliers`.

### Implementing an Intervention

Subclass `InterventionEngine` from `entities.py`:

```python
from edsa_carousel_sim.entities import InterventionEngine

class BusBreakdown(InterventionEngine):
    def trigger(self, env, sim_state, event_type, **kwargs):
        if event_type == "breakdown":
            bus_id = kwargs["bus_id"]
            bus = sim_state.buses[bus_id]
            bus.state = BusState.BROKEN_DOWN
            # Block lane for repair_time seconds
            yield env.timeout(kwargs.get("repair_time", 600))
            bus.state = BusState.IDLE
```

Register it before running: `sim_state.interventions.append(BusBreakdown())`.

### Using Real OSM Data

Install the full GIS stack:
```bash
pip install osmnx geopandas shapely
```

The `osm_network.py` module will automatically detect `osmnx`, download the EDSA road network within the configured bounding box, snap stations to the nearest graph nodes, and compute shortest-path distances via `networkx`. No code changes needed.

---

## Event Log Schema

Events in `sim_state.event_log` follow this structure:

```python
{
    "time": float,          # SimPy timestamp (seconds from sim start)
    "event_type": str,      # One of the types below
    "entity_id": str,       # Bus ID (as string) or station name
    "details": dict         # Event-specific payload
}
```

| `event_type` | `entity_id` | `details` keys |
|-------------|-------------|----------------|
| `BUS_DISPATCH` | bus ID | `direction` |
| `BUS_ARRIVE_STATION` | bus ID | `station`, `occupancy` |
| `BUS_DEPART_STATION` | bus ID | `station`, `boarded`, `alighted`, `delay_sec` |
| `TRIP_COMPLETE` | bus ID | `direction`, `trip` |
| `QUEUE_UPDATE` | station name | `queue_length`, `arrivals` |

---

## Dependencies

| Package | Required | Purpose |
|---------|----------|---------|
| `simpy >= 4.0` | **Yes** | Discrete-event simulation engine |
| `numpy >= 1.24` | **Yes** | Random number generation, array operations |
| `pandas >= 2.0` | **Yes** | DataFrame exports for metrics |
| `matplotlib >= 3.7` | Optional | Static chart generation |
| `seaborn >= 0.12` | Optional | Chart styling |
| `folium >= 0.14` | Optional | Interactive HTML map |
| `networkx >= 3.1` | Optional | Graph shortest-path computation |
| `osmnx >= 1.6` | Optional | OpenStreetMap network download |
| `geopandas >= 0.13` | Optional | Required by osmnx |
| `shapely >= 2.0` | Optional | Required by osmnx |

The simulation runs correctly with only `simpy`, `numpy`, and `pandas`. All visualization and GIS features degrade gracefully when their dependencies are missing.

---

## Typical 24-Hour Output (Seed=42)

```
Total Passengers Served: 82,514
Total Passengers Denied: 0 (0.00% denial rate)
Average Wait Time: 132.6 seconds (2.2 minutes)
Median Wait Time: 64.8 seconds
Total Bus Trips: 2,343
Bus Bunching Severity: 90.8 seconds
Wall-clock time: ~8 seconds
```

Top bottlenecks: GMA Kamuning (521.8 min), Santolan-Annapolis (517.7 min), Quezon Avenue (452.5 min) — all 2-berth stations under 4× demand surge.
