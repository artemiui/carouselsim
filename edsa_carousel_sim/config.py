"""Centralized configuration module for the EDSA Busway (Carousel) discrete-event simulation.

This module defines all network, fleet, station, dwell, and demand parameters
in a centralized, dataclass-driven structure.
"""

from __future__ import annotations
import dataclasses
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


@dataclass
class NetworkConfig:
    osm_corridor_bbox: Tuple[float, float, float, float] = (14.67, 14.50, 121.07, 120.97)  # north, south, east, west
    bus_lane_speed_limit_kmh: float = 50.0
    osm_network_type: str = 'drive'
    osm_xml_path: Optional[str] = "edsa_corridor.osm"  # Path to local .osm / .xml file


@dataclass
class StationDefinition:
    name: str
    lat: float
    lon: float
    platform_type: str  # 'Median' or 'Terminal'
    berth_capacity: int = 2
    is_terminal: bool = False
    is_hotspot: bool = False  # Station characterized by heavy passenger queues / lines
    base_arrival_rate: Optional[float] = None  # Override base arrival rate (pax/min)
    alighting_share_multiplier: float = 1.0  # Propensity for passengers to alight here

    def __post_init__(self):
        if self.platform_type not in ('Median', 'Terminal'):
            raise ValueError(f"platform_type must be 'Median' or 'Terminal', got {self.platform_type}")


@dataclass
class FleetConfig:
    fleet_size: int = 100
    dispatch_interval_seconds: float = 120.0
    bus_capacity: int = 60
    bus_length_meters: float = 12.0
    max_boarding_per_stop: Optional[int] = None  # Optional boarding cap to prevent excessive dwell


@dataclass
class DwellConfig:
    boarding_time_per_pax_sec: float = 2.5
    alighting_time_per_pax_sec: float = 1.5
    door_overhead_sec: float = 10.0


@dataclass
class CorridorFrictionConfig:
    """Operational friction points along the EDSA corridor."""
    enable_u_turn_friction: bool = True
    u_turn_stop_probability: float = 0.45  # Probability of delay at Bagong Barrio U-turn slot
    u_turn_delay_range_sec: Tuple[float, float] = (15.0, 45.0)  # Stop delay range in seconds
    monumento_stacking_capacity: int = 15  # Terminal bus stacking bay capacity
    pitx_stacking_capacity: int = 15
    terminal_turnaround_sec: float = 300.0  # 5 min layover/recovery at terminals
    # Rogue actor lingering behavior ("nagpupuno" driver lingering to fill up)
    enable_rogue_actors: bool = True
    rogue_actor_probability: float = 0.12  # Chance per station dwell that bus lingers to fill up
    rogue_extra_dwell_sec: Tuple[float, float] = (90.0, 270.0)  # 1.5 to 4.5 min extra lingering at berth


@dataclass
class RushHourWindow:
    start_hour: float
    end_hour: float
    label: str

    def __post_init__(self):
        if not (0.0 <= self.start_hour < self.end_hour <= 24.0):
            raise ValueError("Invalid rush hour window times")


@dataclass
class DemandConfig:
    is_weekend: bool = False
    rush_hour_windows: List[RushHourWindow] = field(default_factory=list)
    base_passenger_arrival_rate: float = 2.0  # Default off-peak pax/min per station
    # Nested dict: {window_label: {station_name: multiplier}}
    rush_hour_multipliers: Dict[str, Dict[str, float]] = field(default_factory=dict)
    alighting_fraction_range: Tuple[float, float] = (0.08, 0.28)

    def __post_init__(self):
        if not (0.0 <= self.alighting_fraction_range[0] <= self.alighting_fraction_range[1] <= 1.0):
            raise ValueError("Invalid alighting fraction range")

    def get_multiplier(self, window_label: str, station_name: str) -> float:
        """Return the surge multiplier for a station during a specific window."""
        window_map = self.rush_hour_multipliers.get(window_label, {})
        return window_map.get(station_name, 1.0)


@dataclass
class SimulationConfig:
    network: NetworkConfig
    fleet: FleetConfig
    dwell: DwellConfig
    demand: DemandConfig
    friction: CorridorFrictionConfig
    stations: List[StationDefinition]
    simulation_duration_hours: float = 24.0
    random_seed: int = 42
    enable_overtaking: bool = False


def get_default_stations() -> List[StationDefinition]:
    """Returns the calibrated 24-station EDSA Carousel route from Monumento to PITX."""
    return [
        # 0. Monumento: Northern Terminus (multiple buses naturally stacked in staging queue)
        StationDefinition(
            name="Monumento", lat=14.6573, lon=120.9840, platform_type='Terminal',
            berth_capacity=6, is_terminal=True, is_hotspot=False
        ),
        # 1. Bagong Barrio: Caloocan / NLEX gateway (U-turn slot nearby)
        StationDefinition(
            name="Bagong Barrio", lat=14.6571, lon=120.9920, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=False
        ),
        # 2. Balintawak: Cloverleaf, LRT-1 interchange, public market
        StationDefinition(
            name="Balintawak", lat=14.6573, lon=121.0000, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=False
        ),
        # 3. Kaingin: Intermediate QC stop
        StationDefinition(
            name="Kaingin", lat=14.6576, lon=121.0102, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=False
        ),
        # 4. Fernando Poe Jr. (Roosevelt): Major transfer hub (LRT-1 FPJ / Muñoz)
        StationDefinition(
            name="Fernando Poe Jr. (Roosevelt)", lat=14.6575, lon=121.0204, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=False
        ),
        # 5. SM North EDSA: Mall & commuter hub (2 berths, peak 12PM & 5PM weekdays, 5-7PM weekends)
        StationDefinition(
            name="SM North EDSA", lat=14.6567, lon=121.0285, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=True
        ),
        # 6. North Avenue: Common offloading and unloading zone, Trinoma & MRT-3 interchange
        StationDefinition(
            name="North Avenue", lat=14.6520, lon=121.0324, platform_type='Median',
            berth_capacity=3, is_terminal=False, is_hotspot=False
        ),
        # 7. Philam: Between North Ave and Quezon Ave (low traffic, rarely offloaded and onloaded)
        StationDefinition(
            name="Philam", lat=14.6470, lon=121.0355, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=False,
            base_arrival_rate=0.25, alighting_share_multiplier=0.15
        ),
        # 8. Quezon Avenue: HOTSPOT (Centris, Commonwealth/Fairview commuter feeder, MRT-3)
        StationDefinition(
            name="Quezon Avenue", lat=14.6425, lon=121.0378, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=True
        ),
        # 9. Kamuning: GMA Network Center / Timog Ave
        StationDefinition(
            name="Kamuning", lat=14.6350, lon=121.0425, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=False
        ),
        # 10. Nepa Q-Mart: Market feeder between Kamuning & Cubao
        StationDefinition(
            name="Nepa Q-Mart", lat=14.6275, lon=121.0465, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=False
        ),
        # 11. Main Avenue (Cubao): HOTSPOT (Araneta City, provincial terminal interchange)
        StationDefinition(
            name="Main Avenue (Cubao)", lat=14.6187, lon=121.0505, platform_type='Median',
            berth_capacity=3, is_terminal=False, is_hotspot=True
        ),
        # 12. Santolan: Camp Crame, Greenhills feeder
        StationDefinition(
            name="Santolan", lat=14.6060, lon=121.0535, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=False
        ),
        # 13. Ortigas: Major business district, SM Megamall, Robinsons Galleria
        StationDefinition(
            name="Ortigas", lat=14.5875, lon=121.0565, platform_type='Median',
            berth_capacity=3, is_terminal=False, is_hotspot=False
        ),
        # 14. Guadalupe: HOTSPOT (Pasig river bridge approach, Taguig/Pateros feeder, severe bottleneck)
        StationDefinition(
            name="Guadalupe", lat=14.5670, lon=121.0460, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=True
        ),
        # 15. Buendia: Makati CBD northern access (Sen. Gil Puyat Ave)
        StationDefinition(
            name="Buendia", lat=14.5540, lon=121.0340, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=False
        ),
        # 16. One Ayala (Ayala): HOTSPOT (One Ayala transport hub, Makati CBD, massive commuter lines)
        StationDefinition(
            name="One Ayala (Ayala)", lat=14.5490, lon=121.0280, platform_type='Median',
            berth_capacity=4, is_terminal=False, is_hotspot=True
        ),
        # 17. Tramo: Pasay / EDSA-Tramo interchange
        StationDefinition(
            name="Tramo", lat=14.5405, lon=121.0100, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=False
        ),
        # 18. Taft Avenue: Pasay Rotonda, LRT-1 & MRT-3 interchange, airport feeder
        StationDefinition(
            name="Taft Avenue", lat=14.5380, lon=121.0005, platform_type='Median',
            berth_capacity=3, is_terminal=False, is_hotspot=False
        ),
        # 19. Roxas Boulevard: Heritage / Roxas Blvd intersection
        StationDefinition(
            name="Roxas Boulevard", lat=14.5335, lon=120.9920, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=False
        ),
        # 20. SM Mall of Asia (MOA): Common offloading destination, minimal boarding lines
        StationDefinition(
            name="SM Mall of Asia (MOA)", lat=14.5310, lon=120.9850, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=False,
            base_arrival_rate=0.35, alighting_share_multiplier=2.5
        ),
        # 21. DFA Aseana: Aseana City commercial area
        StationDefinition(
            name="DFA Aseana", lat=14.5245, lon=120.9910, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=False
        ),
        # 22. City of Dreams: Entertainment City / Belle Ave
        StationDefinition(
            name="City of Dreams", lat=14.5180, lon=120.9945, platform_type='Median',
            berth_capacity=2, is_terminal=False, is_hotspot=False
        ),
        # 23. Parañaque Integrated Terminal Exchange (PITX): Southern Terminus
        StationDefinition(
            name="Parañaque Integrated Terminal Exchange (PITX)", lat=14.5095, lon=121.0030, platform_type='Terminal',
            berth_capacity=6, is_terminal=True, is_hotspot=False
        ),
    ]


def get_default_config(is_weekend: bool = False) -> SimulationConfig:
    """Builds the calibrated EDSA Carousel simulation configuration."""
    stations = get_default_stations()

    # ── Define station-specific rush-hour multipliers based on real-world behavior ──
    # AM Peak: 07:00 - 09:30 (Morning commute Southbound)
    am_multipliers: Dict[str, float] = {}
    for st in stations:
        if st.name == "Fernando Poe Jr. (Roosevelt)":
            am_multipliers[st.name] = 6.5  # Heavy morning commuter influx
        elif st.name in ("Quezon Avenue", "Main Avenue (Cubao)", "Guadalupe"):
            am_multipliers[st.name] = 5.5  # Major morning boarding hotspots
        elif st.name == "One Ayala (Ayala)":
            am_multipliers[st.name] = 3.5  # High transfer volume
        elif st.name == "SM North EDSA":
            am_multipliers[st.name] = 2.5  # Moderate morning traffic
        elif st.name == "North Avenue":
            am_multipliers[st.name] = 4.0  # High transfer
        elif st.name == "Philam":
            am_multipliers[st.name] = 0.3  # Minimal arrivals
        elif st.name == "SM Mall of Asia (MOA)":
            am_multipliers[st.name] = 0.4  # Minimal boarding
        elif st.name in ("Balintawak", "Monumento", "Taft Avenue"):
            am_multipliers[st.name] = 4.0  # Terminal and LRT interchanges
        else:
            am_multipliers[st.name] = 1.8

    # Midday Peak: 11:30 - 13:30 (Weekday lunch crowd, huge at SM North EDSA)
    midday_multipliers: Dict[str, float] = {}
    for st in stations:
        if st.name == "SM North EDSA":
            midday_multipliers[st.name] = 6.0  # 12 PM Mall lunch hotspot!
        elif st.name == "North Avenue":
            midday_multipliers[st.name] = 3.5  # High midday mall crowd
        elif st.name in ("Quezon Avenue", "Main Avenue (Cubao)", "Guadalupe", "One Ayala (Ayala)"):
            midday_multipliers[st.name] = 2.5  # Moderate midday business traffic
        elif st.name == "Philam":
            midday_multipliers[st.name] = 0.15
        elif st.name == "SM Mall of Asia (MOA)":
            midday_multipliers[st.name] = 0.6
        else:
            midday_multipliers[st.name] = 1.3

    # PM Peak: 17:00 - 20:00 (Evening commute Northbound)
    pm_multipliers: Dict[str, float] = {}
    for st in stations:
        if st.name == "One Ayala (Ayala)":
            pm_multipliers[st.name] = 7.0  # Massive evening queue of CBD workers
        elif st.name == "Guadalupe":
            pm_multipliers[st.name] = 6.5  # Huge evening line & bottleneck
        elif st.name in ("Main Avenue (Cubao)", "Quezon Avenue"):
            pm_multipliers[st.name] = 6.0  # Massive commuter lines
        elif st.name == "SM North EDSA":
            pm_multipliers[st.name] = 5.0  # 5 PM evening peak
        elif st.name == "North Avenue":
            pm_multipliers[st.name] = 4.0  # High evening transfer
        elif st.name == "Fernando Poe Jr. (Roosevelt)":
            pm_multipliers[st.name] = 2.0  # In PM, heavy alighting rather than boarding
        elif st.name == "Philam":
            pm_multipliers[st.name] = 0.25  # Rarely onloaded
        elif st.name == "SM Mall of Asia (MOA)":
            pm_multipliers[st.name] = 0.5  # Minimal boarding lines
        else:
            pm_multipliers[st.name] = 2.0

    # Weekend Evening Peak: 17:00 - 19:00 (Weekend mall surge)
    weekend_pm_multipliers: Dict[str, float] = {}
    for st in stations:
        if st.name == "SM North EDSA":
            weekend_pm_multipliers[st.name] = 5.5  # Weekend 5-7 PM rush
        elif st.name == "North Avenue":
            weekend_pm_multipliers[st.name] = 4.5
        elif st.name in ("Ortigas", "Main Avenue (Cubao)", "One Ayala (Ayala)"):
            weekend_pm_multipliers[st.name] = 3.5
        elif st.name == "SM Mall of Asia (MOA)":
            weekend_pm_multipliers[st.name] = 1.0  # Moderate weekend mall departures
        elif st.name == "Philam":
            weekend_pm_multipliers[st.name] = 0.2
        else:
            weekend_pm_multipliers[st.name] = 1.4

    if is_weekend:
        rush_hour_windows = [
            RushHourWindow(start_hour=17.0, end_hour=19.0, label="Weekend PM Peak"),
        ]
        rush_hour_multipliers = {
            "Weekend PM Peak": weekend_pm_multipliers,
        }
    else:
        rush_hour_windows = [
            RushHourWindow(start_hour=7.0, end_hour=9.5, label="AM Peak"),
            RushHourWindow(start_hour=11.5, end_hour=13.5, label="Midday Peak"),
            RushHourWindow(start_hour=17.0, end_hour=20.0, label="PM Peak"),
        ]
        rush_hour_multipliers = {
            "AM Peak": am_multipliers,
            "Midday Peak": midday_multipliers,
            "PM Peak": pm_multipliers,
        }

    return SimulationConfig(
        network=NetworkConfig(),
        fleet=FleetConfig(),
        dwell=DwellConfig(),
        friction=CorridorFrictionConfig(),
        demand=DemandConfig(
            is_weekend=is_weekend,
            rush_hour_windows=rush_hour_windows,
            rush_hour_multipliers=rush_hour_multipliers,
        ),
        stations=stations,
    )
