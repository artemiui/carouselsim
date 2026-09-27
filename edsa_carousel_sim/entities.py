"""Entity definitions module for the EDSA Busway simulation.

Defines all core entities (Bus, Station, Passenger, Platform Queues)
and simulation state structures.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict, Any
import numpy as np

from edsa_carousel_sim.config import SimulationConfig, StationDefinition, DwellConfig


@dataclass
class Passenger:
    """Represents an individual passenger commuting on the EDSA Carousel."""
    id: int
    origin_station: str
    destination_station: str
    direction: str  # 'forward' (Southbound) or 'reverse' (Northbound)
    arrival_time: float
    board_time: float = -1.0
    alight_time: float = -1.0
    denied: bool = False
    station_clog_delay_sec: float = 0.0  # Time stuck in queuing bus right outside destination


class BusState(Enum):
    """Possible states for a bus in service."""
    IDLE = auto()
    EN_ROUTE = auto()
    QUEUING_AT_STATION = auto()
    DWELLING = auto()
    AT_TERMINAL = auto()
    BROKEN_DOWN = auto()


class Bus:
    """Represents a bus operating on the EDSA Carousel route."""
    def __init__(self, id: int, capacity: int, length_meters: float, max_boarding_per_stop: Optional[int] = None):
        self.id = id
        self.capacity = capacity
        self.length_meters = length_meters
        self.max_boarding_per_stop = max_boarding_per_stop
        self.passengers: List[Passenger] = []
        self.state: BusState = BusState.IDLE
        self.current_station: Optional[str] = None
        self.direction: str = 'forward'  # 'forward' (Monumento->PITX) or 'reverse' (PITX->Monumento)
        self.trip_count: int = 0
        self.total_passengers_served: int = 0
        self.position_km: float = 0.0
        self.speed_kmh: float = 0.0
        self.current_trip_start_time: float = 0.0
        self.completed_trip_durations: List[float] = []
        self.event_log: List[Dict[str, Any]] = []

    @property
    def occupancy(self) -> int:
        """Current passenger count on board."""
        return len(self.passengers)

    @property
    def remaining_capacity(self) -> int:
        """Remaining seating/standing capacity."""
        return max(0, self.capacity - self.occupancy)

    def board_passengers(self, passengers: List[Passenger], sim_time: float):
        """Add boarding passengers and log boarding timestamp."""
        for p in passengers:
            p.board_time = sim_time
            self.passengers.append(p)
            self.total_passengers_served += 1

    def alight_passengers(
        self,
        station_name: str,
        is_terminal: bool,
        alighting_multiplier: float,
        rng: np.random.Generator,
        sim_time: float
    ) -> List[Passenger]:
        """
        Alight passengers at this station:
        1. All passengers with matching destination alight.
        2. Terminal stations: 100% alight.
        3. Background fraction adjusted by station alighting_multiplier.
        """
        if is_terminal or station_name.lower() in ("monumento", "pitx"):
            alighting = list(self.passengers)
            self.passengers = []
        else:
            # Match destination
            matching = [p for p in self.passengers if p.destination_station == station_name]
            remaining = [p for p in self.passengers if p.destination_station != station_name]

            # Background alighting if any passengers did not have explicit destination
            extra_fraction = min(0.35, 0.05 * alighting_multiplier)
            num_extra = int(len(remaining) * extra_fraction) if remaining else 0
            alighting = matching + remaining[:num_extra]
            self.passengers = remaining[num_extra:]

        for p in alighting:
            p.alight_time = sim_time

        return alighting

    def log_event(self, time: float, event_type: str, station: str = '', details: Optional[Dict[str, Any]] = None):
        """Append an event to this bus's event log."""
        self.event_log.append({
            'time': time,
            'event_type': event_type,
            'station': station,
            'details': details or {}
        })


class StationQueue:
    """
    Represents an EDSA Carousel station with directional platform queues
    (Southbound/Forward and Northbound/Reverse) and separate directional berth resources.
    """
    def __init__(self, station_def: StationDefinition):
        self.station_def = station_def
        self.waiting_forward: List[Passenger] = []  # Southbound (Monumento -> PITX)
        self.waiting_reverse: List[Passenger] = []  # Northbound (PITX -> Monumento)

        # Directional Berths: Southbound and Northbound are physically separate lanes in the median!
        self.berth_resource_forward: Any = None  # Southbound berths (Monumento -> PITX)
        self.berth_resource_reverse: Any = None  # Northbound berths (PITX -> Monumento)
        self.berth_resource: Any = None  # Backwards-compatible alias

        # Directional Rogue Actor tracking
        self.active_rogue_bus_forward: Optional[int] = None
        self.active_rogue_bus_reverse: Optional[int] = None

        # Directional Bus Queues & Delays
        self.bus_queue_delays_forward: List[float] = []
        self.bus_queue_delays_reverse: List[float] = []
        self.max_bus_queue_count_forward: int = 0
        self.max_bus_queue_count_reverse: int = 0
        self.cumulative_bus_delay_sec_forward: float = 0.0
        self.cumulative_bus_delay_sec_reverse: float = 0.0

        # General aggregate tracking
        self.bus_queue: List[int] = []
        self.cumulative_bus_delay_sec: float = 0.0
        self.max_queue_length: int = 0
        self.total_passengers_arrived: int = 0
        self.total_passengers_boarded: int = 0
        self.total_passengers_denied: int = 0
        self.passenger_wait_times: List[float] = []
        self.bus_arrival_times: List[float] = []
        self.bus_queue_delays: List[float] = []
        self.max_bus_queue_delay_sec: float = 0.0
        self.max_bus_queue_count: int = 0

    def get_berth_resource(self, direction: str) -> Any:
        """Returns the dedicated SimPy berth resource for this direction's lane."""
        if direction == 'forward':
            return self.berth_resource_forward if self.berth_resource_forward is not None else self.berth_resource
        return self.berth_resource_reverse if self.berth_resource_reverse is not None else self.berth_resource

    def get_active_rogue_bus(self, direction: str) -> Optional[int]:
        return self.active_rogue_bus_forward if direction == 'forward' else self.active_rogue_bus_reverse

    def set_active_rogue_bus(self, direction: str, bus_id: Optional[int]):
        if direction == 'forward':
            self.active_rogue_bus_forward = bus_id
        else:
            self.active_rogue_bus_reverse = bus_id

    @property
    def active_rogue_bus(self) -> Optional[int]:
        """Aggregate active rogue bus (either direction)."""
        return self.active_rogue_bus_forward or self.active_rogue_bus_reverse

    @active_rogue_bus.setter
    def active_rogue_bus(self, val: Optional[int]):
        self.active_rogue_bus_forward = val

    def board_additional(self, bus: Bus, sim_time: float) -> int:
        """Boards additional passengers arriving while a rogue bus lingers at berth."""
        target_queue = self.waiting_forward if bus.direction == 'forward' else self.waiting_reverse
        can_board = min(bus.remaining_capacity, len(target_queue))
        if can_board <= 0:
            return 0
        to_board = target_queue[:can_board]
        if bus.direction == 'forward':
            self.waiting_forward = self.waiting_forward[can_board:]
        else:
            self.waiting_reverse = self.waiting_reverse[can_board:]
        bus.board_passengers(to_board, sim_time)
        self.total_passengers_boarded += can_board
        for p in to_board:
            self.passenger_wait_times.append(sim_time - p.arrival_time)
        return can_board

    @property
    def queue_length(self) -> int:
        """Combined passenger queue across both directional platforms."""
        return len(self.waiting_forward) + len(self.waiting_reverse)

    def add_passenger(self, passenger: Passenger):
        """Directs arriving passenger to the correct directional platform queue."""
        if passenger.direction == 'forward':
            self.waiting_forward.append(passenger)
        else:
            self.waiting_reverse.append(passenger)

        self.total_passengers_arrived += 1
        total_q = self.queue_length
        if total_q > self.max_queue_length:
            self.max_queue_length = total_q

    def board_to_bus(
        self,
        bus: Bus,
        dwell_config: DwellConfig,
        rng: np.random.Generator,
        sim_time: float,
    ) -> Tuple[int, int, float]:
        """
        Executes onloading and offloading for an arriving bus:
        1. Offload (alight) passengers arriving at this destination.
        2. Onload (board) passengers from the appropriate directional platform queue.
        3. Calculate dynamic dwell time:
           T_dwell = T_overhead + max(N_on * t_board, N_off * t_alight)
        """
        # 1. Offloading (Alighting)
        alighted = bus.alight_passengers(
            station_name=self.station_def.name,
            is_terminal=self.station_def.is_terminal,
            alighting_multiplier=self.station_def.alighting_share_multiplier,
            rng=rng,
            sim_time=sim_time,
        )
        n_off = len(alighted)

        # 2. Select directional platform queue
        target_queue = self.waiting_forward if bus.direction == 'forward' else self.waiting_reverse

        # 3. Onloading (Boarding)
        available_slots = bus.remaining_capacity
        if bus.max_boarding_per_stop is not None:
            available_slots = min(available_slots, bus.max_boarding_per_stop)

        can_board = min(available_slots, len(target_queue))
        to_board = target_queue[:can_board]

        # Update remaining waiting queue
        if bus.direction == 'forward':
            self.waiting_forward = self.waiting_forward[can_board:]
            remaining_q = len(self.waiting_forward)
        else:
            self.waiting_reverse = self.waiting_reverse[can_board:]
            remaining_q = len(self.waiting_reverse)

        # If queue remains and bus is full, count unserved as denied/bypassed
        if remaining_q > 0 and bus.remaining_capacity == 0:
            self.total_passengers_denied += remaining_q

        bus.board_passengers(to_board, sim_time)
        n_on = len(to_board)
        self.total_passengers_boarded += n_on

        for p in to_board:
            self.passenger_wait_times.append(sim_time - p.arrival_time)

        # 4. Realistic Onloading/Offloading Dynamics:
        # Crowding Friction Factor (TCQSM Standard):
        # When a bus is already partially loaded (e.g. 30+ pax on board), aisle friction
        # increases boarding time per passenger because boarders must push past standees.
        occupancy_ratio = bus.occupancy / bus.capacity if bus.capacity > 0 else 0.0
        crowding_multiplier = 1.0 + 0.45 * (occupancy_ratio ** 2)  # up to 45% slower when packed
        
        # Stochastic variation in boarding & alighting rates (fumbling with cash, luggage, mobility)
        effective_board_sec = dwell_config.boarding_time_per_pax_sec * crowding_multiplier * rng.uniform(0.92, 1.15)
        effective_alight_sec = dwell_config.alighting_time_per_pax_sec * rng.uniform(0.90, 1.10)

        if n_on == 0 and n_off == 0:
            # Zero passengers boarding or alighting: bus does not dwell, zero door overhead.
            # "If there are no pax, it doesn't clog!"
            return 0, 0, 0.0

        t_dwell = dwell_config.door_overhead_sec + max(
            n_on * effective_board_sec,
            n_off * effective_alight_sec,
        )

        return n_on, n_off, float(t_dwell)

    def record_bus_arrival(self, sim_time: float):
        """Track bus arrival time for headway calculation."""
        self.bus_arrival_times.append(sim_time)

    def get_headway_stats(self) -> Dict[str, float]:
        """Compute headway statistics (mean, standard deviation, coefficient of variation)."""
        if len(self.bus_arrival_times) < 2:
            return {'mean': 0.0, 'std': 0.0, 'cv': 0.0}

        headways = np.diff(self.bus_arrival_times)
        mean_h = float(np.mean(headways))
        std_h = float(np.std(headways))
        cv_h = std_h / mean_h if mean_h > 0 else 0.0
        return {'mean': mean_h, 'std': std_h, 'cv': cv_h}


class InterventionEngine(ABC):
    """Abstract base class for extensible runtime interventions."""
    @abstractmethod
    def trigger(self, env: Any, sim_state: 'SimulationState', event_type: str, **kwargs):
        pass


class SimulationState:
    """Holds global runtime state, entities, and logs."""
    def __init__(self, env: Any, config: SimulationConfig):
        self.env = env
        self.config = config
        self.buses: Dict[int, Bus] = {}
        self.stations: Dict[str, StationQueue] = {}
        self.monumento_staging_resource: Any = None
        self.pitx_staging_resource: Any = None
        self.event_log: List[Dict[str, Any]] = []
        self.interventions: List[InterventionEngine] = []
        self.all_passengers: List[Passenger] = []

    def log_event(self, time: float, event_type: str, entity_id: str = '', details: Optional[Dict[str, Any]] = None):
        """Log a global simulation event."""
        self.event_log.append({
            'time': time,
            'event_type': event_type,
            'entity_id': entity_id,
            'details': details or {}
        })

    def get_sim_hour(self) -> float:
        """Current simulation hour of the 24-hour cycle (0.0 to 24.0)."""
        return (self.env.now / 3600.0) % 24.0
