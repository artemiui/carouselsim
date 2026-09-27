#!/usr/bin/env python3
"""Interactive 8:00 AM - 11:00 AM Visualization Dashboard Generator
for the EDSA Busway (Carousel) Simulation.

Extracts high-resolution 2-minute time-slice snapshots of passenger queues,
bus berth queuing, vehicle positions, and onloading/offloading dynamics.
Renders an interactive, standalone HTML dashboard with playback controls.
"""

from __future__ import annotations
import sys
import os

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import time
import json
import logging
import numpy as np

import simpy
from edsa_carousel_sim.config import get_default_config, SimulationConfig
from edsa_carousel_sim.osm_network import build_network, EDSANetwork
from edsa_carousel_sim.entities import StationQueue, Bus, BusState, SimulationState
from edsa_carousel_sim.engine import passenger_generator, bus_dispatcher, bus_process

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_and_record_8am_11am(config: SimulationConfig, network: EDSANetwork) -> tuple[list[dict], dict]:
    """
    Runs the simulation and records time-series snapshots every 2 minutes (120s)
    between 08:00 AM (28,800s) and 11:00 AM (39,600s).
    """
    env = simpy.Environment()
    rng = np.random.default_rng(config.random_seed)
    sim_state = SimulationState(env=env, config=config)

    # Terminals staging resources
    sim_state.monumento_staging_resource = simpy.Resource(env, capacity=config.friction.monumento_stacking_capacity)
    sim_state.pitx_staging_resource = simpy.Resource(env, capacity=config.friction.pitx_stacking_capacity)

    # Station berth resources
    for station_def in config.stations:
        sq = StationQueue(station_def=station_def)
        sq.berth_resource = simpy.Resource(env, capacity=station_def.berth_capacity)
        sim_state.stations[station_def.name] = sq

    env.process(passenger_generator(env, sim_state, rng))
    env.process(bus_dispatcher(env, sim_state, network, rng))

    snapshots = []
    station_names = [st.name for st in config.stations]

    # Snapshot collector process
    def snapshot_recorder():
        yield env.timeout(28800.0)  # Fast-forward to 8:00 AM
        
        while env.now <= 39600.0:   # Until 11:00 AM
            now_sec = env.now
            sim_hour = (now_sec / 3600.0) % 24.0
            hh = int(sim_hour)
            mm = int((sim_hour - hh) * 60)
            time_str = f"{hh:02d}:{mm:02d} {'AM' if hh < 12 else 'PM'}"

            # Station snapshot
            st_data = {}
            total_waiting_pax = 0
            total_buses_queuing = 0
            total_buses_dwelling = 0

            for name, sq in sim_state.stations.items():
                fw_q = len(sq.waiting_forward)
                rv_q = len(sq.waiting_reverse)
                tot_q = fw_q + rv_q
                total_waiting_pax += tot_q

                n_dwelling = sq.berth_resource.count
                n_queuing = len(sq.berth_resource.queue)
                total_buses_dwelling += n_dwelling
                total_buses_queuing += n_queuing

                # Peak bus queue delay at this station
                recent_delays = sq.bus_queue_delays[-10:] if sq.bus_queue_delays else [0.0]
                avg_recent_delay_min = float(np.mean(recent_delays)) / 60.0

                st_data[name] = {
                    'pax_q_forward': fw_q,
                    'pax_q_reverse': rv_q,
                    'pax_q_total': tot_q,
                    'buses_dwelling': n_dwelling,
                    'buses_queuing': n_queuing,
                    'max_bus_q': sq.max_bus_queue_count,
                    'avg_delay_min': round(avg_recent_delay_min, 1),
                    'total_arrived': sq.total_passengers_arrived,
                    'total_boarded': sq.total_passengers_boarded,
                }

            # Bus snapshots (sample of active buses on corridor)
            bus_samples = []
            for b_id, bus in list(sim_state.buses.items())[:60]:  # representative fleet sample
                bus_samples.append({
                    'id': bus.id,
                    'station': bus.current_station or 'En Route',
                    'dir': bus.direction,
                    'occupancy': bus.occupancy,
                    'remaining_cap': bus.remaining_capacity,
                    'state': bus.state.name,
                })

            snapshots.append({
                'time_sec': now_sec,
                'time_str': time_str,
                'hour': round(sim_hour, 2),
                'total_waiting_pax': total_waiting_pax,
                'total_buses_queuing': total_buses_queuing,
                'total_buses_dwelling': total_buses_dwelling,
                'stations': st_data,
                'buses': bus_samples,
            })

            yield env.timeout(120.0)  # Every 2 minutes

    env.process(snapshot_recorder())

    logger.info("Executing simulation up to 11:00 AM (39,600s)...")
    t0 = time.time()
    env.run(until=39600.0)
    logger.info("Simulation completed in %.2f seconds. Recorded %d snapshots.", time.time() - t0, len(snapshots))

    # Metadata
    meta = {
        'stations': [
            {
                'name': st.name,
                'lat': st.lat,
                'lon': st.lon,
                'berths': st.berth_capacity,
                'is_terminal': st.is_terminal,
                'is_hotspot': st.is_hotspot,
            }
            for st in config.stations
        ],
        'total_snapshots': len(snapshots),
        'fleet_size': config.fleet.fleet_size,
        'bus_capacity': config.fleet.bus_capacity,
    }

    return snapshots, meta


def generate_html_dashboard(snapshots: list[dict], meta: dict, output_file: str):
    """Generates the interactive HTML/JS dashboard."""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EDSA Carousel: 8:00 AM - 11:00 AM Interactive Operations Dashboard</title>
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --card-border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-hover: #0284c7;
      --danger: #ef4444;
      --warning: #f59e0b;
      --success: #10b981;
      --purple: #a855f7;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
    body {{ background-color: var(--bg); color: var(--text); padding: 20px; line-height: 1.5; }}
    
    .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 15px; border-bottom: 1px solid var(--card-border); padding-bottom: 16px; }}
    .title-box h1 {{ font-size: 1.5rem; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 10px; }}
    .badge {{ background: #0284c7; color: #fff; font-size: 0.75rem; padding: 3px 8px; border-radius: 4px; font-weight: 600; }}
    .title-box p {{ font-size: 0.88rem; color: var(--text-muted); margin-top: 4px; }}

    /* KPI Cards */
    .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-bottom: 20px; }}
    .kpi-card {{ background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 14px 18px; }}
    .kpi-title {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 6px; }}
    .kpi-val {{ font-size: 1.6rem; font-weight: 800; color: #fff; }}
    .kpi-sub {{ font-size: 0.8rem; margin-top: 4px; }}
    
    /* Playback Controller */
    .controller-card {{ background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 16px 20px; margin-bottom: 20px; }}
    .ctrl-row {{ display: flex; align-items: center; gap: 18px; flex-wrap: wrap; }}
    .clock-display {{ font-size: 1.8rem; font-weight: 800; font-family: monospace; color: var(--accent); min-width: 140px; }}
    .btn {{ background: #334155; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; cursor: pointer; transition: 0.15s; font-size: 0.88rem; display: flex; align-items: center; gap: 6px; }}
    .btn:hover {{ background: #475569; }}
    .btn.primary {{ background: var(--accent); color: #0f172a; }}
    .btn.primary:hover {{ background: var(--accent-hover); }}
    .slider-box {{ flex-grow: 1; display: flex; align-items: center; gap: 10px; min-width: 280px; }}
    input[type=range] {{ flex-grow: 1; height: 7px; border-radius: 5px; background: #334155; outline: none; -webkit-appearance: none; }}
    input[type=range]::-webkit-slider-thumb {{ -webkit-appearance: none; width: 18px; height: 18px; border-radius: 50%; background: var(--accent); cursor: pointer; border: 2px solid #fff; }}
    .phase-badge {{ font-size: 0.82rem; padding: 4px 10px; border-radius: 20px; font-weight: 700; background: rgba(56, 189, 248, 0.15); color: var(--accent); }}

    /* Layout Columns */
    .dashboard-layout {{ display: grid; grid-template-columns: 1.25fr 1fr; gap: 20px; }}
    @media (max-width: 1024px) {{ .dashboard-layout {{ grid-template-columns: 1fr; }} }}

    /* Schematic Strip */
    .schematic-card {{ background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 18px; overflow-x: auto; }}
    .section-title {{ font-size: 1.05rem; font-weight: 700; color: #fff; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }}
    .route-strip {{ display: flex; flex-direction: column; gap: 8px; max-height: 520px; overflow-y: auto; padding-right: 8px; }}
    .station-node {{ display: flex; align-items: center; justify-content: space-between; background: #0f172a; border: 1px solid #334155; padding: 10px 14px; border-radius: 8px; transition: 0.15s; cursor: pointer; }}
    .station-node:hover {{ border-color: var(--accent); background: #162032; }}
    .station-node.hotspot {{ border-left: 4px solid var(--danger); }}
    .station-node.minor {{ border-left: 4px solid #64748b; }}
    .st-left {{ display: flex; align-items: center; gap: 10px; }}
    .st-name {{ font-weight: 700; font-size: 0.88rem; }}
    .st-desc {{ font-size: 0.72rem; color: var(--text-muted); }}
    .st-metrics {{ display: flex; align-items: center; gap: 14px; font-size: 0.8rem; }}
    .pill {{ padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }}
    .pill-queue {{ background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
    .pill-bus {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
    .pill-berth {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}

    /* Right Charts & Details */
    .right-col {{ display: flex; flex-direction: column; gap: 20px; }}
    .panel-card {{ background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 18px; }}
    .station-detail-box {{ background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 14px; margin-top: 10px; }}

    /* Simple Pure SVG Bar Chart */
    .chart-container {{ height: 220px; width: 100%; position: relative; margin-top: 12px; }}
    svg text {{ font-size: 10px; fill: var(--text-muted); }}
  </style>
</head>
<body>

  <!-- Header -->
  <div class="header">
    <div class="title-box">
      <h1>EDSA Busway: 8:00 AM – 11:00 AM Operational Window <span class="badge">Live Discrete-Event Sim</span></h1>
      <p>Interactive analysis of AM peak tidal flows (Muñoz surge, SM North lunch buildup, single-berth queuing, and hotspot line dynamics)</p>
    </div>
  </div>

  <!-- KPI Cards -->
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-title">Current Clock Time</div>
      <div class="kpi-val" id="kpi-time">08:00 AM</div>
      <div class="kpi-sub" id="kpi-phase" style="color: var(--accent);">AM Peak Commute Influx</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Waiting Passengers in Line</div>
      <div class="kpi-val" id="kpi-pax-queue">0</div>
      <div class="kpi-sub" style="color: #f87171;" id="kpi-pax-surge">System-wide platform queues</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Buses Queued Behind Stations</div>
      <div class="kpi-val" id="kpi-bus-queue" style="color: var(--warning);">0</div>
      <div class="kpi-sub" id="kpi-bus-queue-sub">Buses delayed waiting for berth</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Primary Choke Point</div>
      <div class="kpi-val" id="kpi-worst-station" style="font-size: 1.25rem;">SM North EDSA</div>
      <div class="kpi-sub" id="kpi-worst-delay" style="color: var(--danger);">Peak bus backup: 0m</div>
    </div>
  </div>

  <!-- Interactive Controller -->
  <div class="controller-card">
    <div class="ctrl-row">
      <div class="clock-display" id="clock-display">08:00 AM</div>
      <button class="btn primary" id="btn-play">▶ Play</button>
      <button class="btn" id="btn-prev">⏮ -2m</button>
      <button class="btn" id="btn-next">⏭ +2m</button>
      <button class="btn" id="btn-speed">Speed: 1x</button>
      <div class="slider-box">
        <span style="font-size:0.8rem; color:var(--text-muted);">08:00</span>
        <input type="range" id="time-slider" min="0" max="{len(snapshots)-1}" value="0">
        <span style="font-size:0.8rem; color:var(--text-muted);">11:00</span>
      </div>
      <div class="phase-badge" id="traffic-phase-badge">Phase: Morning Peak Commute</div>
    </div>
  </div>

  <!-- Main Grid -->
  <div class="dashboard-layout">
    
    <!-- Left: 22 Stations Corridor Schematic -->
    <div class="schematic-card">
      <div class="section-title">
        <span>Corridor Line Schematic (Monumento to PITX)</span>
        <span style="font-size:0.75rem; color:var(--text-muted);">Click station to inspect</span>
      </div>
      <div class="route-strip" id="stations-list">
        <!-- Rendered by JS -->
      </div>
    </div>

    <!-- Right: Detail Panel & Analytics -->
    <div class="right-col">
      
      <!-- Selected Station Inspector -->
      <div class="panel-card">
        <div class="section-title">
          <span id="detail-title">Station Inspector: SM North EDSA</span>
          <span class="badge" id="detail-berth-badge">1 Berth</span>
        </div>
        <div id="station-detail-content">
          <!-- Populated by JS -->
        </div>
      </div>

      <!-- Real-Time Comparison Bar Chart -->
      <div class="panel-card">
        <div class="section-title">
          <span>Passenger Queue Comparison at Selected Stations</span>
        </div>
        <div class="chart-container" id="bar-chart-container">
          <svg id="bar-chart-svg" width="100%" height="100%" viewBox="0 0 450 200"></svg>
        </div>
      </div>

    </div>

  </div>

  <script>
    // Embedded simulation data
    const snapshots = {json.dumps(snapshots)};
    const metadata = {json.dumps(meta)};
    
    let currentIndex = 0;
    let isPlaying = false;
    let playInterval = null;
    let playSpeed = 1;
    let selectedStationName = "SM North EDSA";

    const keyStations = ["Munoz / FPJ", "SM North EDSA", "Trinoma / North Avenue", "Philam", "Quezon Avenue", "Cubao", "Guadalupe", "Ayala", "Macapagal / MOA"];

    function getPhaseText(hour) {{
      if (hour < 8.5) return "AM Peak Commute Influx (Heavy Southbound)";
      if (hour < 9.5) return "Peak Rush Congestion (Muñoz & Centris Surge)";
      if (hour < 10.2) return "Mid-Morning Offload & Dispersal";
      return "Pre-Midday Lunch Buildup (SM North Surge Begins)";
    }}

    function renderSnapshot(idx) {{
      const snap = snapshots[idx];
      if (!snap) return;

      // Update KPIs
      document.getElementById('clock-display').innerText = snap.time_str;
      document.getElementById('kpi-time').innerText = snap.time_str;
      document.getElementById('kpi-pax-queue').innerText = snap.total_waiting_pax.toLocaleString();
      document.getElementById('kpi-bus-queue').innerText = snap.total_buses_queuing + " buses";
      document.getElementById('traffic-phase-badge').innerText = getPhaseText(snap.hour);
      document.getElementById('kpi-phase').innerText = getPhaseText(snap.hour);
      document.getElementById('time-slider').value = idx;

      // Find worst bottleneck station in this snapshot
      let worstSt = "SM North EDSA";
      let maxDelay = 0;
      for (const [stName, st] of Object.entries(snap.stations)) {{
        if (st.avg_delay_min > maxDelay) {{
          maxDelay = st.avg_delay_min;
          worstSt = stName;
        }}
      }}
      document.getElementById('kpi-worst-station').innerText = worstSt;
      document.getElementById('kpi-worst-delay').innerText = `Queuing delay: ~${{maxDelay.toFixed(1)}} min | Line: ${{snap.stations[worstSt].buses_queuing}} buses`;

      // Render Stations List
      const listEl = document.getElementById('stations-list');
      listEl.innerHTML = '';

      metadata.stations.forEach(stMeta => {{
        const st = snap.stations[stMeta.name] || {{ pax_q_total: 0, buses_queuing: 0, buses_dwelling: 0, avg_delay_min: 0 }};
        const isSelected = (stMeta.name === selectedStationName);
        
        const node = document.createElement('div');
        node.className = `station-node ${{stMeta.is_hotspot ? 'hotspot' : 'minor'}}`;
        if (isSelected) node.style.borderColor = 'var(--accent)';
        if (isSelected) node.style.background = '#1e293b';

        let badgeHtml = '';
        if (stMeta.is_hotspot) badgeHtml = `<span style="font-size:0.65rem; background:#ef4444; color:#fff; padding:1px 5px; border-radius:3px;">HOTSPOT</span>`;
        if (stMeta.name === "Philam") badgeHtml = `<span style="font-size:0.65rem; background:#475569; color:#fff; padding:1px 5px; border-radius:3px;">MINIMAL</span>`;
        if (stMeta.name === "Macapagal / MOA") badgeHtml = `<span style="font-size:0.65rem; background:#0284c7; color:#fff; padding:1px 5px; border-radius:3px;">OFFLOAD</span>`;

        node.innerHTML = `
          <div class="st-left">
            <div>
              <div class="st-name">${{stMeta.name}} ${{badgeHtml}}</div>
              <div class="st-desc">${{stMeta.berths}} Berth(s) | ${{st.buses_dwelling}} bus inside bay</div>
            </div>
          </div>
          <div class="st-metrics">
            <span class="pill pill-queue" title="Waiting passengers">👤 ${{st.pax_q_total}}</span>
            <span class="pill pill-bus" title="Buses queued in line">🚌 ${{st.buses_queuing}} queued</span>
            ${{st.avg_delay_min > 3 ? `<span style="color:#ef4444; font-size:0.75rem; font-weight:700;">+${{st.avg_delay_min.toFixed(0)}}m</span>` : ''}}
          </div>
        `;

        node.onclick = () => {{
          selectedStationName = stMeta.name;
          renderSnapshot(currentIndex);
        }};

        listEl.appendChild(node);
      }});

      // Render Station Detail Box
      renderStationDetail(snap, selectedStationName);

      // Render Comparison Bar Chart
      renderBarChart(snap);
    }}

    function renderStationDetail(snap, name) {{
      const stMeta = metadata.stations.find(s => s.name === name) || {{ berths: 2, is_hotspot: false }};
      const st = snap.stations[name] || {{ pax_q_forward: 0, pax_q_reverse: 0, pax_q_total: 0, buses_queuing: 0, buses_dwelling: 0, avg_delay_min: 0 }};

      document.getElementById('detail-title').innerText = `Station Inspector: ${{name}}`;
      document.getElementById('detail-berth-badge').innerText = `${{stMeta.berths}} Berth(s) Capacity`;

      let note = "";
      if (name === "Munoz / FPJ") note = "High Southbound boarding origin during AM peak (8-9:30 AM). Evening returns alight heavily here.";
      else if (name === "SM North EDSA") note = "Constrained by single-berth bottleneck. High queuing when onloading/offloading exceeds headway.";
      else if (name === "Philam") note = "Quiet residential stop between North Ave & Quezon Ave. Minimal boarding lines, rarely offloaded.";
      else if (name === "Macapagal / MOA") note = "Primary destination offloading zone. High passenger alighting, but minimal platform boarding lines.";
      else if (name === "Quezon Avenue") note = "Hotspot passenger queue from Commonwealth & Centris commuters.";
      else if (name === "Guadalupe") note = "Narrow platform pinch point. High passenger transfers from Pasig & Taguig.";
      else if (name === "Monumento") note = "Northern terminus. Staging queue stacks buses before scheduled dispatch.";

      const box = document.getElementById('station-detail-content');
      box.innerHTML = `
        <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:12px;">${{note}}</div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
          <div class="station-detail-box">
            <div style="font-size:0.72rem; color:var(--text-muted);">SOUTHBOUND PLATFORM</div>
            <div style="font-size:1.4rem; font-weight:800; color:#38bdf8;">${{st.pax_q_forward}} <span style="font-size:0.8rem; font-weight:normal;">pax in line</span></div>
          </div>
          <div class="station-detail-box">
            <div style="font-size:0.72rem; color:var(--text-muted);">NORTHBOUND PLATFORM</div>
            <div style="font-size:1.4rem; font-weight:800; color:#a855f7;">${{st.pax_q_reverse}} <span style="font-size:0.8rem; font-weight:normal;">pax in line</span></div>
          </div>
          <div class="station-detail-box">
            <div style="font-size:0.72rem; color:var(--text-muted);">BUSES CURRENTLY QUEUED</div>
            <div style="font-size:1.4rem; font-weight:800; color:${{st.buses_queuing > 0 ? '#ef4444' : '#10b981'}};">${{st.buses_queuing}} <span style="font-size:0.8rem; font-weight:normal;">buses</span></div>
            <div style="font-size:0.75rem; color:var(--text-muted);">Est. backup: ~${{st.buses_queuing * 12}} meters</div>
          </div>
          <div class="station-detail-box">
            <div style="font-size:0.72rem; color:var(--text-muted);">RECENT BUS WAIT TIME</div>
            <div style="font-size:1.4rem; font-weight:800; color:#fbbf24;">${{st.avg_delay_min.toFixed(1)}} <span style="font-size:0.8rem; font-weight:normal;">min</span></div>
            <div style="font-size:0.75rem; color:var(--text-muted);">Dwell + Berth Queue delay</div>
          </div>
        </div>
      `;
    }}

    function renderBarChart(snap) {{
      const svg = document.getElementById('bar-chart-svg');
      svg.innerHTML = '';

      const chartW = 450;
      const chartH = 180;
      const barH = 14;
      const gap = 5;
      const leftPad = 130;
      const maxVal = Math.max(...keyStations.map(k => (snap.stations[k] ? snap.stations[k].pax_q_total : 0)), 150);

      keyStations.forEach((name, i) => {{
        const val = snap.stations[name] ? snap.stations[name].pax_q_total : 0;
        const w = (val / maxVal) * (chartW - leftPad - 50);
        const y = i * (barH + gap) + 12;

        const isHotspot = (name === "Quezon Avenue" || name === "Cubao" || name === "Guadalupe" || name === "Ayala" || name === "SM North EDSA");
        const color = isHotspot ? '#ef4444' : (name === 'Philam' ? '#64748b' : '#38bdf8');

        // Station label
        const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        txt.setAttribute('x', leftPad - 8);
        txt.setAttribute('y', y + 11);
        txt.setAttribute('text-anchor', 'end');
        txt.setAttribute('fill', '#cbd5e1');
        txt.textContent = name.length > 16 ? name.substring(0, 15) + '…' : name;
        svg.appendChild(txt);

        // Bar rect
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', leftPad);
        rect.setAttribute('y', y);
        rect.setAttribute('width', Math.max(w, 2));
        rect.setAttribute('height', barH);
        rect.setAttribute('rx', 3);
        rect.setAttribute('fill', color);
        svg.appendChild(rect);

        // Value text
        const valTxt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        valTxt.setAttribute('x', leftPad + w + 6);
        valTxt.setAttribute('y', y + 11);
        valTxt.setAttribute('fill', '#94a3b8');
        valTxt.textContent = val;
        svg.appendChild(valTxt);
      }});
    }}

    // Playback Controller Logic
    const slider = document.getElementById('time-slider');
    const playBtn = document.getElementById('btn-play');
    const speedBtn = document.getElementById('btn-speed');

    function stepNext() {{
      if (currentIndex < snapshots.length - 1) {{
        currentIndex++;
        renderSnapshot(currentIndex);
      }} else {{
        pause();
      }}
    }}

    function stepPrev() {{
      if (currentIndex > 0) {{
        currentIndex--;
        renderSnapshot(currentIndex);
      }}
    }}

    function play() {{
      isPlaying = true;
      playBtn.innerText = "⏸ Pause";
      playBtn.classList.remove('primary');
      playInterval = setInterval(stepNext, 500 / playSpeed);
    }}

    function pause() {{
      isPlaying = false;
      playBtn.innerText = "▶ Play";
      playBtn.classList.add('primary');
      if (playInterval) clearInterval(playInterval);
    }}

    playBtn.onclick = () => isPlaying ? pause() : play();
    document.getElementById('btn-next').onclick = stepNext;
    document.getElementById('btn-prev').onclick = stepPrev;

    slider.oninput = (e) => {{
      pause();
      currentIndex = parseInt(e.target.value);
      renderSnapshot(currentIndex);
    }};

    speedBtn.onclick = () => {{
      if (playSpeed === 1) playSpeed = 2;
      else if (playSpeed === 2) playSpeed = 4;
      else playSpeed = 1;
      speedBtn.innerText = `Speed: ${{playSpeed}}x`;
      if (isPlaying) {{
        pause();
        play();
      }}
    }};

    // Initial render
    renderSnapshot(0);
  </script>
</body>
</html>
"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    logger.info("Successfully generated interactive dashboard at %s", output_file)


def main():
    logger.info("Building network for 8:00 AM - 11:00 AM Interactive Dashboard...")
    cfg = get_default_config(is_weekend=False)
    net = build_network(cfg)
    snapshots, meta = run_and_record_8am_11am(cfg, net)

    out_file = os.path.abspath("output/dashboard_8am_11am.html")
    generate_html_dashboard(snapshots, meta, out_file)


if __name__ == "__main__":
    main()
