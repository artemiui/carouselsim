from __future__ import annotations
import math
import logging
from dataclasses import dataclass, field
from typing import Optional

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

try:
    import osmnx as ox
    HAS_OSMNX = True
except ImportError:
    HAS_OSMNX = False

from edsa_carousel_sim.config import SimulationConfig, StationDefinition

logger = logging.getLogger(__name__)


@dataclass
class StationNode:
    """A station mapped to the road network."""
    name: str
    lat: float
    lon: float
    osm_node_id: Optional[int] = None
    order_index: int = 0  # Position in route sequence


@dataclass 
class RouteSegment:
    """A segment between two consecutive stations."""
    from_station: str
    to_station: str
    distance_meters: float
    travel_time_seconds: float  # At free-flow speed


@dataclass
class EDSANetwork:
    """Processed EDSA busway network with stations and segments."""
    station_nodes: list[StationNode] = field(default_factory=list)
    segments_forward: list[RouteSegment] = field(default_factory=list)  # Monumento -> PITX
    segments_reverse: list[RouteSegment] = field(default_factory=list)  # PITX -> Monumento
    total_distance_meters: float = 0.0
    osm_graph: object = None  # networkx graph if available


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns distance in meters between two coordinates."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


import os
import xml.etree.ElementTree as ET


def parse_osm_xml_nodes_and_ways(xml_path: str) -> tuple[dict[int, tuple[float, float]], list[dict]]:
    """
    Parses a local OSM XML (.osm / .xml) file to extract road nodes and highway segments.
    Works with standard Python library (no external C-extensions required).
    """
    logger.info(f"Parsing local OSM XML file: {xml_path}")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    nodes = {}
    for n in root.findall('node'):
        nid = int(n.attrib['id'])
        lat = float(n.attrib['lat'])
        lon = float(n.attrib['lon'])
        nodes[nid] = (lat, lon)
        
    ways = []
    for w in root.findall('way'):
        tags = {t.attrib.get('k'): t.attrib.get('v') for t in w.findall('tag')}
        if 'highway' in tags:
            refs = [int(nd.attrib['ref']) for nd in w.findall('nd') if int(nd.attrib['ref']) in nodes]
            if len(refs) >= 2:
                ways.append({
                    'id': int(w.attrib['id']),
                    'name': tags.get('name', ''),
                    'highway': tags.get('highway', ''),
                    'refs': refs
                })
                
    logger.info(f"Extracted {len(nodes):,} nodes and {len(ways):,} highway ways from OSM XML.")
    return nodes, ways


def build_network(config: SimulationConfig) -> EDSANetwork:
    """Builds the EDSA network graph and segments.
    
    Priority order:
    1. Local OSM XML file (if config.network.osm_xml_path or local edsa.osm exists) -> 100% offline, zero API 403s!
    2. OSMnx Overpass API download (if osmnx is installed)
    3. Haversine distance with 1.3x road curvature factor
    """
    network = EDSANetwork()
    graph = None
    xml_nodes = None
    
    # ── Option 1: Check for Local OSM XML file ──
    xml_path = config.network.osm_xml_path
    if not xml_path:
        for candidate in ["edsa_corridor.osm", "edsa.osm", "edsa_corridor.xml", "edsa.xml"]:
            if os.path.exists(candidate):
                xml_path = candidate
                break
                
    if xml_path and os.path.exists(xml_path):
        logger.info(f"Found local OSM XML file: {xml_path}. Loading offline network...")
        if HAS_OSMNX:
            try:
                graph = ox.graph_from_xml(xml_path)
                network.osm_graph = graph
                logger.info("Successfully built NetworkX graph from OSM XML via OSMnx.")
            except Exception as e:
                logger.warning(f"OSMnx graph_from_xml failed: {e}. Using built-in XML parser.")
                
        if graph is None:
            # Fall back to built-in pure-Python XML parser
            try:
                xml_nodes, xml_ways = parse_osm_xml_nodes_and_ways(xml_path)
                if HAS_NETWORKX:
                    # Construct directed NetworkX graph directly from XML ways
                    G = nx.DiGraph()
                    for nid, (nlat, nlon) in xml_nodes.items():
                        G.add_node(nid, y=nlat, x=nlon)
                    for way in xml_ways:
                        refs = way['refs']
                        for u, v in zip(refs[:-1], refs[1:]):
                            u_lat, u_lon = xml_nodes[u]
                            v_lat, v_lon = xml_nodes[v]
                            seg_len = haversine_distance(u_lat, u_lon, v_lat, v_lon)
                            G.add_edge(u, v, length=seg_len, name=way.get('name', ''))
                            G.add_edge(v, u, length=seg_len, name=way.get('name', ''))
                    graph = G
                    network.osm_graph = graph
                    logger.info("Successfully constructed NetworkX graph directly from OSM XML.")
            except Exception as e:
                logger.warning(f"Failed to parse OSM XML file: {e}")
                
    # ── Option 2: OSMnx Overpass API (if no local XML) ──
    elif HAS_OSMNX:
        try:
            if hasattr(ox, 'settings'):
                ox.settings.user_agent = 'EDSA-Carousel-Sim/1.0 (Metro Manila Transportation Engineering Research)'
                ox.settings.timeout = 60
                ox.settings.use_cache = True
            logger.info(f"Downloading OSM network for bbox {config.network.osm_corridor_bbox}")
            n, s, e, w = config.network.osm_corridor_bbox
            try:
                graph = ox.graph_from_bbox(bbox=(n, s, e, w), network_type=config.network.osm_network_type)
            except TypeError:
                graph = ox.graph_from_bbox(n, s, e, w, network_type=config.network.osm_network_type)
            network.osm_graph = graph
            logger.info("Successfully downloaded OSM network.")
        except Exception as e:
            logger.warning(f"Failed to download OSM network: {e}. Falling back to haversine distances.")
    else:
        logger.info("Operating in standalone offline mode. Using haversine with 1.3x road factor.")
        
    stations = config.stations
    network.station_nodes = []
    
    for idx, stat_def in enumerate(stations):
        node_id = None
        if graph is not None:
            try:
                if HAS_OSMNX:
                    node_id = ox.nearest_nodes(graph, stat_def.lon, stat_def.lat)
                elif xml_nodes:
                    # Find nearest node among XML nodes
                    best_nid = min(xml_nodes.keys(), key=lambda nid: haversine_distance(stat_def.lat, stat_def.lon, xml_nodes[nid][0], xml_nodes[nid][1]))
                    node_id = best_nid
            except Exception as e:
                logger.warning(f"Failed to find nearest node for {stat_def.name}: {e}")
                
        node = StationNode(
            name=stat_def.name,
            lat=stat_def.lat,
            lon=stat_def.lon,
            osm_node_id=node_id,
            order_index=idx
        )
        network.station_nodes.append(node)
        
    speed_limit_ms = config.network.bus_lane_speed_limit_kmh * 1000.0 / 3600.0
    
    # Create segments forward
    total_dist_forward = 0.0
    for i in range(len(network.station_nodes) - 1):
        n1 = network.station_nodes[i]
        n2 = network.station_nodes[i+1]
        
        dist = None
        if graph is not None and n1.osm_node_id is not None and n2.osm_node_id is not None:
            try:
                dist = nx.shortest_path_length(graph, n1.osm_node_id, n2.osm_node_id, weight='length')
            except nx.NetworkXNoPath:
                logger.warning(f"No path found between {n1.name} and {n2.name}. Falling back to haversine.")
                
        if dist is None:
            dist = haversine_distance(n1.lat, n1.lon, n2.lat, n2.lon) * 1.3
            
        total_dist_forward += dist
        time_s = dist / speed_limit_ms
        
        seg = RouteSegment(from_station=n1.name, to_station=n2.name, distance_meters=dist, travel_time_seconds=time_s)
        network.segments_forward.append(seg)
        logger.debug(f"Forward Segment {n1.name} -> {n2.name}: {dist:.2f}m, {time_s:.2f}s")
        
    # Create segments reverse (PITX to Monumento)
    for i in range(len(network.station_nodes) - 1, 0, -1):
        n1 = network.station_nodes[i]
        n2 = network.station_nodes[i-1]
        
        dist = None
        if graph is not None and n1.osm_node_id is not None and n2.osm_node_id is not None:
            try:
                dist = nx.shortest_path_length(graph, n1.osm_node_id, n2.osm_node_id, weight='length')
            except nx.NetworkXNoPath:
                logger.warning(f"No path found between {n1.name} and {n2.name}. Falling back to haversine.")
                
        if dist is None:
            dist = haversine_distance(n1.lat, n1.lon, n2.lat, n2.lon) * 1.3
            
        time_s = dist / speed_limit_ms
        
        seg = RouteSegment(from_station=n1.name, to_station=n2.name, distance_meters=dist, travel_time_seconds=time_s)
        network.segments_reverse.append(seg)
        logger.debug(f"Reverse Segment {n1.name} -> {n2.name}: {dist:.2f}m, {time_s:.2f}s")
        
    network.total_distance_meters = total_dist_forward
    logger.info(f"Built network with {len(network.station_nodes)} stations. Total forward distance: {network.total_distance_meters:.2f}m")
    
    return network


def get_station_sequence(network: EDSANetwork, direction: str = 'forward') -> list[StationNode]:
    """Returns ordered station list for the given direction."""
    if direction.lower() == 'reverse':
        return network.station_nodes[::-1]
    return network.station_nodes


def get_travel_time(network: EDSANetwork, from_station: str, to_station: str) -> float:
    """Returns travel time in seconds between two consecutive stations."""
    for seg in network.segments_forward:
        if seg.from_station == from_station and seg.to_station == to_station:
            return seg.travel_time_seconds
            
    for seg in network.segments_reverse:
        if seg.from_station == from_station and seg.to_station == to_station:
            return seg.travel_time_seconds
            
    logger.error(f"No segment found from {from_station} to {to_station}")
    return 0.0
