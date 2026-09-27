#!/usr/bin/env python3
"""Unified Interactive EDSA Busway Simulation Dashboard Generator.

Features:
- Square-oriented transit wayfinding graphic design (DOTr / Metro Manila signage standard).
- Transit signage colors: Canary Yellow (#FFCC00), Obsidian Black (#111215), LRT-2 Purple (#7C3AED), Busway Blue (#2563EB).
- Black-fill developer information footer with info from artemiui.vercel.app (Artemio Arcega).
- Dual Visualizations:
  1. Concentric Rings (Circular Carousel): Inner & Outer concentric circles representing Northbound (↺ counter-clockwise)
     and Southbound (↻ clockwise) with stations at equal angular spacing (15° apart), and smaller nodes representing each bus.
  2. Calibrated Route Map: True geometric schematic alignment matching the official EDSA Carousel Transit Map attachment.
- Hover description overlays (tooltips) for all transit simulation variables.
- Demand trend chart with ONLY the peak numerically labeled (no vertical highlight lines).
- Complete calibrated 24-station route from Monumento to PITX with accurate OSM & schematic coordinates.
- Dual-direction circulation: live Southbound (SB) and Northbound (NB) rotation with reverse checklist.
- Dynamic floating chip & beacon ripple tracking active rogue actor / chokepoint per direction.
- Zero-passenger free-flow rule: platforms without demand do not cause artificial clogging.
- Absolutely zero emojis (pure SVG icons and clean typography throughout).
"""

from __future__ import annotations
import sys
import os
import json
import math
import logging

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from edsa_carousel_sim.config import get_default_stations
from edsa_carousel_sim.simulator_api import run_simulation_window

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("Generating pre-baked simulation presets with randomized rogue actor dynamics...")

    # Preset 1: AM Peak (08:00 - 11:00)
    logger.info("Simulating Preset 1: AM Peak (08:00 - 11:00)...")
    am_snaps, am_meta = run_simulation_window({'start_hour': 8.0, 'end_hour': 11.0, 'step_minutes': 2.0, 'rogue_probability': 0.12})

    # Preset 2: Midday Peak (11:30 - 14:30)
    logger.info("Simulating Preset 2: Midday Peak (11:30 - 14:30)...")
    midday_snaps, midday_meta = run_simulation_window({'start_hour': 11.5, 'end_hour': 14.5, 'step_minutes': 2.0, 'rogue_probability': 0.12})

    # Preset 3: PM Peak (17:00 - 20:00)
    logger.info("Simulating Preset 3: PM Peak (17:00 - 20:00)...")
    pm_snaps, pm_meta = run_simulation_window({'start_hour': 17.0, 'end_hour': 20.0, 'step_minutes': 2.0, 'rogue_probability': 0.15})

    presets = {
        'am_peak': {
            'label': 'AM Peak (8:00 - 11:00 AM)',
            'start_hour': 8.0,
            'end_hour': 11.0,
            'meta': am_meta,
            'snapshots': am_snaps,
        },
        'midday_peak': {
            'label': 'Midday (11:30 - 2:30 PM)',
            'start_hour': 11.5,
            'end_hour': 14.5,
            'meta': midday_meta,
            'snapshots': midday_snaps,
        },
        'pm_peak': {
            'label': 'PM Peak (5:00 - 8:00 PM)',
            'start_hour': 17.0,
            'end_hour': 20.0,
            'meta': pm_meta,
            'snapshots': pm_snaps,
        }
    }

    raw_stations = get_default_stations()

    # Fixed geographic route coordinates matching the official EDSA Carousel Transit Map attachment
    schematic_coords = {
        "Monumento": (75.0, 32.0),
        "Bagong Barrio": (115.0, 32.0),
        "Balintawak": (155.0, 32.0),
        "Kaingin": (195.0, 32.0),
        "Fernando Poe Jr. (Roosevelt)": (235.0, 32.0),
        "SM North EDSA": (275.0, 38.0),
        "North Avenue": (310.0, 56.0),
        "Philam": (335.0, 76.0),
        "Quezon Avenue": (360.0, 98.0),
        "Kamuning": (385.0, 120.0),
        "Nepa Q-Mart": (410.0, 144.0),
        "Main Avenue (Cubao)": (435.0, 172.0),
        "Santolan": (445.0, 198.0),
        "Ortigas": (440.0, 224.0),
        "Guadalupe": (405.0, 252.0),
        "Buendia": (365.0, 268.0),
        "One Ayala (Ayala)": (320.0, 276.0),
        "Tramo": (270.0, 278.0),
        "Taft Avenue": (220.0, 278.0),
        "Roxas Boulevard": (170.0, 278.0),
        "SM Mall of Asia (MOA)": (125.0, 278.0),
        "DFA Aseana": (148.0, 294.0),
        "City of Dreams": (148.0, 308.0),
        "Parañaque Integrated Terminal Exchange (PITX)": (148.0, 324.0),
    }

    # Station line codes (Metro transit signage format e.g. YL02 / PL08)
    station_codes = {
        "Monumento": "ED01",
        "Bagong Barrio": "ED02",
        "Balintawak": "ED03",
        "Kaingin": "ED04",
        "Fernando Poe Jr. (Roosevelt)": "ED05",
        "SM North EDSA": "ED06",
        "North Avenue": "ED07",
        "Philam": "ED08",
        "Quezon Avenue": "ED09",
        "Kamuning": "ED10",
        "Nepa Q-Mart": "ED11",
        "Main Avenue (Cubao)": "ED12",
        "Santolan": "ED13",
        "Ortigas": "ED14",
        "Guadalupe": "ED15",
        "Buendia": "ED16",
        "One Ayala (Ayala)": "ED17",
        "Tramo": "ED18",
        "Taft Avenue": "ED19",
        "Roxas Boulevard": "ED20",
        "SM Mall of Asia (MOA)": "ED21",
        "DFA Aseana": "ED22",
        "City of Dreams": "ED23",
        "Parañaque Integrated Terminal Exchange (PITX)": "ED24",
    }

    # Circular Carousel: concentric circles (Outer = Southbound, Inner = Northbound)
    circle_cx = 270.0
    circle_cy = 160.0
    r_outer = 115.0  # Southbound (Clockwise)
    r_inner = 85.0   # Northbound (Counter-Clockwise)

    station_svg_nodes = []
    num_st = len(raw_stations)  # 24
    for i, s in enumerate(raw_stations):
        rx, ry = schematic_coords.get(s.name, (100.0, 100.0))
        code = station_codes.get(s.name, f"ED{i+1:02d}")

        # Equal-distance circular coordinates (starting from Monumento at 12 o'clock, progressing clockwise)
        theta = -math.pi / 2.0 + (i / num_st) * (2.0 * math.pi)
        cx_out = round(circle_cx + r_outer * math.cos(theta), 1)
        cy_out = round(circle_cy + r_outer * math.sin(theta), 1)
        cx_in = round(circle_cx + r_inner * math.cos(theta), 1)
        cy_in = round(circle_cy + r_inner * math.sin(theta), 1)

        station_svg_nodes.append({
            'name': s.name,
            'code': code,
            'x': rx,
            'y': ry,
            'circle_x_out': cx_out,
            'circle_y_out': cy_out,
            'circle_x_in': cx_in,
            'circle_y_in': cy_in,
            'theta': theta,
            'is_hotspot': s.is_hotspot,
            'is_terminal': s.is_terminal,
            'berths': s.berth_capacity,
            'platform': s.platform_type,
        })

    route_path_d = 'M ' + ' L '.join(f"{s['x']} {s['y']}" for s in station_svg_nodes)

    out_file = os.path.abspath("output/dashboard.html")
    logger.info("Rendering clean UI template to %s...", out_file)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EDSA Carousel: Dual-Rotation Transit Simulation Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-page: #F7F4EB;
      --bg-card: #FFFFFF;
      --border-subtle: #E4E0D5;
      --border-dark: #27272A;
      
      /* Transit Wayfinding Palette */
      --signage-black: #111215;
      --signage-dark-card: #18191E;
      --signage-yellow: #FFCC00;
      --signage-yellow-hover: #E6B800;
      --signage-purple: #7C3AED;
      --signage-blue: #2563EB;
      --signage-cyan: #0284C7;
      --signage-orange: #EA580C;
      --signage-green: #10B981;
      
      --text-main: #111215;
      --text-muted: #52525B;
      --text-light: #8E8E93;
      
      /* Square-oriented radii */
      --radius-sm: 4px;
      --radius-md: 6px;
      --radius-lg: 8px;
      
      --shadow-soft: 0 2px 10px rgba(17, 18, 21, 0.04);
      --shadow-floating: 0 10px 25px rgba(17, 18, 21, 0.08);
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}

    body {{
      background-color: var(--bg-page);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: space-between;
      padding: 0;
      -webkit-font-smoothing: antialiased;
    }}

    /* Global Workspace Layout: Full Width without Sidebar */
    .dashboard-layout {{
      width: 100%;
      max-width: 1400px;
      display: flex;
      flex-direction: column;
      gap: 18px;
      padding: 24px 24px 0 24px;
      flex: 1;
    }}

    /* Main Content Container */
    .main-canvas {{
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }}

    /* Top Action Bar (Compact Icon-Only Actions + Clock Time Range) */
    .canvas-header {{
      display: flex;
      align-items: center;
      justify-content: center;
      flex-wrap: wrap;
      gap: 12px;
      background: #FFFFFF;
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 10px 16px;
      box-shadow: var(--shadow-soft);
    }}
    .header-actions {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }}
    .square-icon-btn {{
      width: 36px;
      height: 36px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: var(--radius-sm);
      background: #FFFFFF;
      border: 1px solid var(--border-subtle);
      color: var(--text-main);
      cursor: pointer;
      box-shadow: var(--shadow-soft);
      transition: all 0.15s ease;
      flex-shrink: 0;
      padding: 0;
    }}
    .square-icon-btn:hover {{
      border-color: #A1A1AA;
      background: #FAF8F2;
      transform: translateY(-1px);
    }}
    .square-icon-btn.yellow {{
      background: var(--signage-yellow);
      color: var(--signage-black);
      border-color: var(--signage-yellow);
    }}
    .square-icon-btn.yellow:hover {{
      background: #FACC15;
      border-color: #EAB308;
    }}
    .time-window-pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 14px;
      border-radius: var(--radius-sm);
      font-size: 0.82rem;
      font-weight: 700;
      background: #FFFFFF;
      border: 1px solid var(--border-subtle);
      color: var(--text-main);
      cursor: pointer;
      box-shadow: var(--shadow-soft);
      transition: all 0.15s ease;
      font-family: inherit;
      font-variant-numeric: tabular-nums;
    }}
    .time-window-pill:hover {{
      border-color: #A1A1AA;
      background: #FAF8F2;
      transform: translateY(-1px);
    }}
    .time-window-pill svg {{
      color: var(--text-muted);
      flex-shrink: 0;
    }}
    .square-btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      border-radius: var(--radius-md);
      font-size: 0.82rem;
      font-weight: 700;
      background: #FFFFFF;
      border: 1px solid var(--border-subtle);
      color: var(--text-main);
      cursor: pointer;
      box-shadow: var(--shadow-soft);
      transition: all 0.15s ease;
    }}
    .square-btn:hover {{
      border-color: #A1A1AA;
      background: #FAF8F2;
    }}
    .square-btn.dark {{
      background: var(--signage-black);
      color: #FFFFFF;
      border-color: var(--signage-black);
    }}
    .square-btn.dark:hover {{
      background: #27272A;
    }}
    .square-btn.yellow {{
      background: var(--signage-yellow);
      color: var(--signage-black);
      border-color: var(--signage-yellow);
    }}
    .square-btn.yellow:hover {{
      background: var(--signage-yellow-hover);
    }}

    /* Row 1: Square-Oriented Bento Metric Cards */
    .bento-metrics {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
    }}
    .bento-card {{
      border-radius: var(--radius-lg);
      padding: 18px 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
      overflow: hidden;
      box-shadow: var(--shadow-soft);
      min-height: 125px;
      transition: transform 0.15s ease, box-shadow 0.15s ease;
      cursor: default;
      border: 1px solid var(--border-subtle);
      background: #FFFFFF;
    }}
    .bento-card:hover {{
      transform: translateY(-2px);
      box-shadow: var(--shadow-floating);
    }}

    /* Card Themes with Square Badges */
    .bento-yellow {{
      border-left: 5px solid var(--signage-yellow);
      background: #FEFCE8;
    }}
    .bento-pink {{
      border-left: 5px solid #3F3F46;
      background: #FAFAFA;
    }}
    .bento-green {{
      border-left: 5px solid var(--signage-green);
      background: #ECFDF5;
    }}
    .bento-blue {{
      border-left: 5px solid var(--signage-blue);
      background: #EFF6FF;
    }}

    /* Card Top Typography */
    .bento-top {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
    }}
    .bento-label {{
      font-size: 0.78rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-main);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .bento-num {{
      font-size: 1.85rem;
      font-weight: 800;
      line-height: 1.1;
      letter-spacing: -0.03em;
      color: var(--text-main);
    }}
    .bento-unit {{
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--text-muted);
    }}
    .bento-sub {{
      font-size: 0.74rem;
      font-weight: 600;
      color: var(--text-muted);
      margin-top: 4px;
    }}

    /* Square Badge Label */
    .card-square-tag {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 0.68rem;
      font-weight: 800;
      padding: 2px 6px;
      border-radius: var(--radius-sm);
      letter-spacing: 0.04em;
    }}
    .card-square-tag.yellow {{ background: var(--signage-yellow); color: #111215; }}
    .card-square-tag.pink {{ background: #DB2777; color: #FFFFFF; }}
    .card-square-tag.green {{ background: var(--signage-green); color: #FFFFFF; }}
    .card-square-tag.blue {{ background: var(--signage-blue); color: #FFFFFF; }}

    /* Mini Bars for Waiting Pax */
    .bento-bars {{
      display: flex;
      align-items: flex-end;
      gap: 3px;
      height: 32px;
    }}
    .bento-bar {{
      width: 5px;
      border-radius: 2px;
      background: var(--signage-black);
      opacity: 0.25;
      transition: height 0.3s ease;
    }}
    .bento-bar.active {{
      background: var(--signage-yellow);
      opacity: 1;
    }}

    /* Embedded Demand Line Chart */
    .demand-chart-box {{
      position: relative;
      width: 100%;
      height: 56px;
      margin-top: 6px;
    }}
    .chart-breakdown-tags {{
      display: flex;
      align-items: center;
      gap: 5px;
      font-size: 0.68rem;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }}
    .clickable-demand-card {{
      cursor: pointer;
      position: relative;
      transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
    }}
    .clickable-demand-card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
      border-color: #71717A;
    }}
    .demand-expand-badge {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 0.62rem;
      font-weight: 800;
      letter-spacing: 0.04em;
      color: var(--text-muted);
      background: rgba(24, 24, 27, 0.06);
      padding: 2px 6px;
      border-radius: 3px;
      transition: all 0.15s ease;
      user-select: none;
    }}
    .clickable-demand-card:hover .demand-expand-badge {{
      background: var(--signage-black);
      color: var(--signage-yellow);
    }}
    .trend-tag {{
      padding: 2px 6px;
      border-radius: 3px;
      cursor: pointer;
      user-select: none;
      transition: all 0.15s ease;
      border: 1px solid transparent;
      display: inline-flex;
      align-items: center;
      gap: 3px;
    }}
    .trend-tag:hover {{
      transform: translateY(-1px);
    }}
    .trend-tag.cum {{
      color: #18181B;
      background: rgba(24, 24, 27, 0.08);
      border-color: rgba(24, 24, 27, 0.18);
    }}
    .trend-tag.sb {{
      color: #1D4ED8;
      background: rgba(37, 99, 235, 0.12);
      border-color: rgba(37, 99, 235, 0.25);
    }}
    .trend-tag.nb {{
      color: #047857;
      background: rgba(16, 185, 129, 0.14);
      border-color: rgba(16, 185, 129, 0.25);
    }}
    .trend-tag.series-disabled {{
      opacity: 0.38 !important;
      background: transparent !important;
      border-color: #D4D4D8 !important;
      color: #71717A !important;
      text-decoration: line-through;
    }}
    .trend-chart-legend {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .legend-dot-label {{
      display: inline-flex;
      align-items: center;
      gap: 3px;
      font-size: 0.65rem;
      font-weight: 700;
      color: var(--text-muted);
      cursor: pointer;
      user-select: none;
      padding: 1px 4px;
      border-radius: 3px;
      transition: all 0.15s ease;
    }}
    .legend-dot-label:hover {{
      color: var(--text-main);
      background: rgba(0, 0, 0, 0.04);
    }}
    .legend-dot-label.series-disabled {{
      opacity: 0.35 !important;
      text-decoration: line-through;
    }}
    .legend-line {{
      display: inline-block;
      width: 9px;
      height: 2.5px;
      border-radius: 1px;
    }}
    .legend-line.cum {{
      background: #18181B;
    }}
    .legend-line.sb {{
      background: #2563EB;
    }}
    .legend-line.nb {{
      background: #10B981;
    }}

    /* Row 2: Main Workspace Grid (Checkpoints + Map) */
    .workspace-grid {{
      display: grid;
      grid-template-columns: 370px 1fr;
      gap: 18px;
      align-items: stretch;
      min-height: 540px;
    }}

    /* Left Card: 24-Station Checkpoint Timeline */
    .white-card {{
      background: var(--bg-card);
      border-radius: var(--radius-lg);
      border: 1px solid var(--border-subtle);
      box-shadow: var(--shadow-soft);
      padding: 20px;
      display: flex;
      flex-direction: column;
      position: relative;
    }}

    .card-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 14px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-subtle);
    }}
    .card-header-title {{
      font-size: 1.05rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: var(--text-main);
    }}
    .card-header-sub {{
      font-size: 0.74rem;
      color: var(--text-muted);
      font-weight: 500;
      margin-top: 2px;
    }}

    /* Square Direction Toggle Switcher */
    .square-toggle-group {{
      display: inline-flex;
      background: #EDEAE1;
      padding: 3px;
      border-radius: var(--radius-sm);
      gap: 3px;
    }}
    .square-toggle-btn {{
      border: none;
      background: transparent;
      padding: 4px 10px;
      border-radius: 3px;
      font-size: 0.74rem;
      font-weight: 800;
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .square-toggle-btn.active {{
      background: var(--signage-black);
      color: var(--signage-yellow);
      box-shadow: 0 1px 4px rgba(0,0,0,0.15);
    }}

    /* Scrollable Station List */
    .station-list-container {{
      flex: 1;
      overflow-y: auto;
      max-height: 440px;
      padding-right: 6px;
      margin-right: -4px;
    }}
    .station-list-container::-webkit-scrollbar {{
      width: 5px;
    }}
    .station-list-container::-webkit-scrollbar-thumb {{
      background: #D4D4D8;
      border-radius: 3px;
    }}

    /* Wayfinding Signage Station Row */
    .station-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 7px 9px;
      border-radius: var(--radius-sm);
      transition: background 0.15s ease;
      cursor: pointer;
      margin-bottom: 3px;
      border: 1px solid transparent;
    }}
    .station-row:hover {{
      background: #FAF8F2;
      border-color: #E2DDD0;
    }}
    .station-left {{
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
    }}

    /* Square Pictograms & Station Codes (like YL02 / PL08 in attachment) */
    .signage-badge {{
      width: 26px;
      height: 26px;
      border-radius: 3px;
      background: var(--signage-black);
      color: var(--signage-yellow);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.72rem;
      font-weight: 800;
      flex-shrink: 0;
      font-family: monospace;
      border: 1px solid #27272A;
    }}
    .signage-badge.terminal {{
      background: var(--signage-yellow);
      color: var(--signage-black);
      border-color: var(--signage-yellow);
    }}
    .signage-badge.hotspot {{
      background: var(--signage-purple);
      color: #FFFFFF;
      border-color: var(--signage-purple);
    }}
    .signage-icon-box {{
      width: 24px;
      height: 24px;
      border-radius: 3px;
      background: var(--signage-yellow);
      color: #111215;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}
    .signage-icon-box.purple {{
      background: var(--signage-purple);
      color: #FFFFFF;
    }}
    .station-code-pill {{
      font-size: 0.64rem;
      font-weight: 800;
      color: var(--signage-yellow);
      background: var(--signage-black);
      border: 1px solid var(--signage-yellow);
      padding: 1px 4px;
      border-radius: 3px;
      font-family: monospace;
      letter-spacing: 0.04em;
    }}

    .st-name {{
      font-size: 0.8rem;
      font-weight: 700;
      color: var(--text-main);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 155px;
    }}
    .st-sub {{
      font-size: 0.68rem;
      color: var(--text-muted);
      font-weight: 500;
    }}
    .st-time {{
      font-size: 0.74rem;
      font-weight: 700;
      color: var(--text-muted);
      font-family: inherit;
      font-variant-numeric: tabular-nums;
      flex-shrink: 0;
    }}

    /* Bottom Info Banner */
    .checklist-footer {{
      margin-top: 12px;
      padding: 8px 12px;
      border-radius: var(--radius-sm);
      background: var(--signage-black);
      color: var(--signage-yellow);
      font-size: 0.74rem;
      font-weight: 700;
      text-align: center;
      letter-spacing: 0.03em;
    }}

    /* Right Card: Map Card with Concentric Rings & Fixed Route Map */
    .map-card {{
      background: var(--bg-card);
      border-radius: var(--radius-lg);
      border: 1px solid var(--border-subtle);
      box-shadow: var(--shadow-soft);
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
      overflow: hidden;
    }}

    /* Dynamic Overlaid Dual-Lane Status HUD over Map */
    .map-status-overlay {{
      position: absolute;
      bottom: 10px;
      left: 10px;
      z-index: 20;
      display: flex;
      flex-direction: row;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px;
      pointer-events: none;
      max-width: calc(100% - 20px);
    }}
    .map-status-chip {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 5px 11px;
      border-radius: var(--radius-sm);
      background: rgba(17, 18, 21, 0.92);
      backdrop-filter: blur(8px);
      border: 1px solid #27272A;
      color: #FFFFFF;
      font-size: 0.72rem;
      font-weight: 700;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
      cursor: pointer;
      pointer-events: auto;
      transition: all 0.15s ease;
      width: fit-content;
      user-select: none;
    }}
    .map-status-chip:hover {{
      background: #18191E;
      border-color: #3F3F46;
      transform: translateY(-1px);
    }}
    .map-status-chip.sb.active-dir {{
      border-color: rgba(37, 99, 235, 0.85);
      box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.35), 0 2px 8px rgba(0, 0, 0, 0.3);
    }}
    .map-status-chip.nb.active-dir {{
      border-color: rgba(16, 185, 129, 0.85);
      box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.35), 0 2px 8px rgba(0, 0, 0, 0.3);
    }}
    .status-beacon-dot {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--signage-green);
      flex-shrink: 0;
      transition: background 0.2s ease;
    }}
    .status-sep {{
      color: #71717A;
      margin: 0 4px;
      font-weight: 400;
    }}
    .map-top-bar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 10px;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .map-section-title {{
      font-size: 0.82rem;
      font-weight: 800;
      color: var(--text-strong);
      letter-spacing: -0.01em;
      text-transform: uppercase;
    }}

    /* Map Legend */
    .map-legend-bar {{
      display: flex;
      align-items: center;
      justify-content: flex-end;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--text-muted);
      margin-bottom: 8px;
    }}
    .legend-item {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }}

    /* Visualization Canvas Wrapper with Zoom & Pan */
    .map-canvas-wrapper {{
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      background: #FAF8F2;
      border-radius: var(--radius-md);
      border: none;
      padding: 8px;
      margin-bottom: 12px;
      min-height: 350px;
      overflow: hidden;
      cursor: grab;
      user-select: none;
    }}
    .map-canvas-wrapper:active {{
      cursor: grabbing;
    }}

    /* Floating Square Wayfinding Map Zoom Toolbar */
    .map-zoom-controls {{
      position: absolute;
      top: 12px;
      right: 12px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      background: rgba(17, 18, 21, 0.94);
      backdrop-filter: blur(8px);
      border: 1px solid #27272A;
      border-radius: var(--radius-sm);
      padding: 5px;
      z-index: 25;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
    }}
    .zoom-btn {{
      width: 28px;
      height: 28px;
      background: #18191E;
      color: var(--signage-yellow);
      border: 1px solid #3F3F46;
      border-radius: 3px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 0.88rem;
      font-weight: 800;
      transition: all 0.15s ease;
    }}
    .zoom-btn:hover {{
      background: #27272A;
      color: #FFFFFF;
      border-color: var(--signage-yellow);
      transform: scale(1.05);
    }}
    .zoom-level-badge {{
      font-size: 0.65rem;
      font-weight: 800;
      color: #D4D4D8;
      font-family: monospace;
      padding: 2px 2px;
      letter-spacing: 0.02em;
    }}

    /* Bottom Scrubber Controller */
    .scrubber-dock {{
      display: flex;
      align-items: center;
      gap: 12px;
      background: #FFFFFF;
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 8px 14px;
    }}
    .play-square-btn {{
      width: 32px;
      height: 32px;
      border-radius: var(--radius-sm);
      background: var(--signage-black);
      color: var(--signage-yellow);
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
      transition: background 0.15s ease;
      flex-shrink: 0;
    }}
    .play-square-btn:hover {{
      background: #27272A;
    }}
    .clock-tag {{
      font-size: 1.15rem;
      font-weight: 800;
      font-family: monospace;
      color: var(--text-main);
      min-width: 90px;
    }}
    .time-slider {{
      flex: 1;
      height: 6px;
      -webkit-appearance: none;
      background: #E4E4E7;
      border-radius: 2px;
      outline: none;
    }}
    .time-slider::-webkit-slider-thumb {{
      -webkit-appearance: none;
      width: 16px;
      height: 16px;
      border-radius: 2px;
      background: var(--signage-black);
      cursor: pointer;
      border: 2px solid var(--signage-yellow);
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
    }}
    .speed-pill {{
      padding: 4px 10px;
      border-radius: var(--radius-sm);
      background: #FFFFFF;
      border: 1px solid var(--border-subtle);
      font-size: 0.74rem;
      font-weight: 800;
      color: var(--text-main);
      cursor: pointer;
    }}

    /* Global Tooltip Popover for Variables */
    #var-tooltip {{
      position: fixed;
      display: none;
      background: var(--signage-black);
      color: #FFFFFF;
      padding: 8px 14px;
      border-radius: var(--radius-sm);
      font-size: 0.74rem;
      line-height: 1.35;
      max-width: 250px;
      pointer-events: none;
      z-index: 9999;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
      border: 1px solid var(--signage-yellow);
      transition: opacity 0.15s ease;
    }}
    #var-tooltip strong {{
      display: block;
      color: var(--signage-yellow);
      font-weight: 800;
      margin-bottom: 2px;
      letter-spacing: -0.01em;
    }}

    /* Station Map Tooltip */
    #map-tooltip {{
      position: absolute;
      display: none;
      background: var(--signage-black);
      color: #FFFFFF;
      padding: 8px 12px;
      border-radius: var(--radius-sm);
      font-size: 0.72rem;
      font-weight: 600;
      pointer-events: none;
      z-index: 20;
      box-shadow: 0 4px 14px rgba(0,0,0,0.2);
      border: 1px solid #3F3F46;
      line-height: 1.35;
    }}

    /* Entire Full-Fill Footer (Edge to Edge) */
    .site-footer {{
      width: 100%;
      background: var(--signage-black);
      border-top: 1px solid #27272A;
      padding: 22px 0;
      margin-top: 36px;
    }}
    .footer-inner {{
      width: 100%;
      max-width: 1400px;
      margin: 0 auto;
      padding: 0 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .footer-brand {{
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}
    .footer-name {{
      font-size: 1.05rem;
      font-weight: 800;
      letter-spacing: -0.01em;
      color: #FFFFFF;
    }}
    .footer-how-btn {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 5px 12px;
      border-radius: var(--radius-sm);
      background: var(--signage-dark-card);
      border: 1px solid #27272A;
      color: #E4E4E7;
      font-size: 0.75rem;
      font-weight: 700;
      text-decoration: none;
      transition: all 0.15s ease;
      width: fit-content;
      margin-top: 4px;
    }}
    .footer-how-btn:hover {{
      background: #27272A;
      border-color: var(--signage-yellow);
      color: var(--signage-yellow);
      transform: translateY(-1px);
    }}
    .footer-how-btn .q-mark {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 15px;
      height: 15px;
      border-radius: 50%;
      background: var(--signage-yellow);
      color: var(--signage-black);
      font-size: 0.65rem;
      font-weight: 900;
      line-height: 1;
    }}
    .footer-links {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .footer-icon-link {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      border-radius: var(--radius-sm);
      background: var(--signage-dark-card);
      border: 1px solid #27272A;
      color: #A1A1AA;
      transition: all 0.15s ease;
      text-decoration: none;
    }}
    .footer-icon-link:hover {{
      background: #27272A;
      color: var(--signage-yellow);
      border-color: var(--signage-yellow);
      transform: translateY(-2px);
    }}

    /* Modal Styling */
    .modal-backdrop {{
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(17, 18, 21, 0.55);
      backdrop-filter: blur(4px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }}
    .modal-card {{
      background: #FFFFFF;
      border-radius: var(--radius-lg);
      padding: 26px 30px;
      width: 100%;
      max-width: 500px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.2);
      border: 1px solid var(--border-subtle);
    }}
    .modal-title {{
      font-size: 1.25rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: var(--text-main);
      margin-bottom: 4px;
    }}
    .modal-sub {{
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-bottom: 20px;
    }}
    .form-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      margin-bottom: 24px;
    }}
    .form-field label {{
      display: block;
      font-size: 0.72rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-muted);
      margin-bottom: 5px;
    }}
    .form-field input, .form-field select {{
      width: 100%;
      padding: 9px 12px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-subtle);
      font-size: 0.86rem;
      outline: none;
      background: #FAF8F2;
      color: var(--text-main);
    }}
    .form-field input:focus, .form-field select:focus {{
      border-color: var(--signage-black);
      background: #FFFFFF;
    }}
    .modal-actions {{
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }}
    .modal-card-wide {{
      max-width: 880px;
      width: 95%;
      padding: 24px 26px;
    }}
    .modal-close-btn {{
      background: transparent;
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      width: 32px;
      height: 32px;
      font-size: 1.35rem;
      font-weight: 700;
      color: var(--text-muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      line-height: 1;
      transition: all 0.15s ease;
    }}
    .modal-close-btn:hover {{
      background: #EDEAE1;
      color: var(--text-main);
      border-color: #3F3F46;
    }}
    .modal-demand-hud {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 10px;
      background: #FAF8F2;
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: 10px 14px;
      margin-bottom: 14px;
    }}
    .modal-hud-item {{
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}
    .modal-hud-label {{
      font-size: 0.65rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-muted);
    }}
    .modal-hud-val {{
      font-size: 0.95rem;
      font-weight: 800;
      color: var(--text-main);
      font-variant-numeric: tabular-nums;
    }}
    .modal-hud-sub {{
      font-size: 0.7rem;
      font-weight: 600;
      color: var(--text-muted);
    }}
    .modal-series-toolbar {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;
      flex-wrap: wrap;
    }}
    .modal-series-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 11px;
      border-radius: var(--radius-sm);
      font-size: 0.74rem;
      font-weight: 800;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.15s ease;
      background: transparent;
      user-select: none;
    }}
    .modal-series-pill:hover {{
      transform: translateY(-1px);
    }}
    .modal-series-pill.cum {{
      color: #18181B;
      background: rgba(24, 24, 27, 0.08);
      border-color: rgba(24, 24, 27, 0.2);
    }}
    .modal-series-pill.sb {{
      color: #1D4ED8;
      background: rgba(37, 99, 235, 0.12);
      border-color: rgba(37, 99, 235, 0.25);
    }}
    .modal-series-pill.nb {{
      color: #047857;
      background: rgba(16, 185, 129, 0.14);
      border-color: rgba(16, 185, 129, 0.25);
    }}
    .modal-series-pill.series-disabled {{
      opacity: 0.35 !important;
      background: transparent !important;
      border-color: #D4D4D8 !important;
      color: #71717A !important;
      text-decoration: line-through;
    }}
    .modal-chart-box {{
      position: relative;
      width: 100%;
      height: 280px;
      background: #FFFFFF;
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      overflow: hidden;
      cursor: crosshair;
      user-select: none;
    }}
    .modal-chart-tooltip {{
      position: absolute;
      display: none;
      background: var(--signage-black);
      color: #FFFFFF;
      padding: 6px 11px;
      border-radius: var(--radius-sm);
      font-size: 0.72rem;
      font-weight: 700;
      pointer-events: none;
      z-index: 10;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
      border: 1px solid #3F3F46;
      line-height: 1.4;
      white-space: nowrap;
      transform: translate(-50%, -115%);
    }}

    /* Loading Overlay */
    .loading-overlay {{
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(17, 18, 21, 0.7);
      backdrop-filter: blur(8px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 2000;
      transition: opacity 0.3s ease;
    }}
    .loading-box {{
      background: #FFFFFF;
      border-radius: var(--radius-lg);
      padding: 36px 40px;
      width: 100%;
      max-width: 460px;
      text-align: center;
      box-shadow: 0 24px 48px rgba(0, 0, 0, 0.25);
      border: 1px solid var(--border-subtle);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 14px;
    }}
    .spinner-ring {{
      width: 44px;
      height: 44px;
      border-radius: 50%;
      border: 4px solid #F4F1E8;
      border-top-color: var(--signage-yellow);
      border-right-color: var(--signage-black);
      animation: spin 0.9s linear infinite;
    }}
    @keyframes spin {{
      to {{ transform: rotate(360deg); }}
    }}
    .progress-bar-box {{
      width: 100%;
      background: #F4F1E8;
      height: 6px;
      border-radius: 2px;
      overflow: hidden;
      margin-top: 6px;
    }}
    .progress-bar-fill {{
      height: 100%;
      width: 0%;
      background: var(--signage-black);
      border-radius: 2px;
      transition: width 0.3s ease;
    }}

    /* Interactive hover cursor indicator */
    .has-var-tooltip {{
      cursor: help;
      position: relative;
    }}
    .has-var-tooltip::after {{
      content: '';
      position: absolute;
      bottom: -1px;
      left: 0;
      right: 0;
      border-bottom: 1px dotted currentColor;
      opacity: 0.5;
    }}
  </style>
</head>
<body>

  <!-- Floating Global Tooltip Overlay for Variables -->
  <div id="var-tooltip">
    <strong id="tt-title">Variable</strong>
    <span id="tt-desc">Description</span>
  </div>

  <!-- Simulation Loading Overlay -->
  <div class="loading-overlay" id="loading-overlay">
    <div class="loading-box">
      <div class="spinner-ring"></div>
      <div style="font-size:1.25rem; font-weight:800; color:var(--text-main);">Running Corridor Simulation</div>
      <div style="font-size:0.82rem; color:var(--text-muted);" id="loading-step-text">Simulating passenger arrivals and platform dwell dynamics...</div>
      <div class="progress-bar-box">
        <div class="progress-bar-fill" id="loading-progress-bar"></div>
      </div>
      <div style="font-size:0.72rem; color:var(--text-light); font-weight:800; text-transform:uppercase;" id="loading-stage-label">Step 1 of 4: Calibrating 24 Stations</div>
    </div>
  </div>

  <div class="dashboard-layout">

    <!-- Main Workspace Canvas -->
    <main class="main-canvas">

      <!-- Compact Top Control Bar: Action Icons + Variable Time Window -->
      <header class="canvas-header">
        <div class="header-actions">
          <!-- Parameters [Settings Icon] -->
          <button class="square-icon-btn has-var-tooltip" id="btn-parameters" onclick="openModal()" data-tooltip-title="Parameters" data-tooltip="Configure simulation parameters (headway, active fleet, capacity, and rogue actor lingering probability)." aria-label="Parameters" title="Parameters">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
          </button>

          <!-- Run Simulation [Play Icon] -->
          <button class="square-icon-btn yellow has-var-tooltip" id="btn-run-sim" onclick="runDirectSimulation()" data-tooltip-title="Run Simulation" data-tooltip="Execute real-time SimPy discrete-event simulation across the 24-station corridor." aria-label="Run Simulation" title="Run Simulation">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
          </button>

          <!-- Export Data [Download Icon] -->
          <button class="square-icon-btn has-var-tooltip" id="btn-export-telemetry" onclick="exportSimulationData()" data-tooltip-title="Export Data" data-tooltip="Export comprehensive simulation time-slices, station queues, delays, and telemetry logs in JSON format for extended analysis." aria-label="Export Data" title="Export Data">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
          </button>
        </div>

        <!-- Dynamic Time Window -->
        <button class="time-window-pill has-var-tooltip" id="btn-time-window" onclick="openModal()" data-tooltip-title="Simulation Time Window" data-tooltip="Observation window: Click to change simulation start and end hours." aria-label="Simulation Time Window" title="Observation Window: Click to change">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          <span id="btn-time-label">08:00 AM – 11:00 AM</span>
        </button>
      </header>

      <!-- Main Workspace Grid (Checkpoints + Map) -->
      <section class="workspace-grid">
        
        <!-- Left: 24-Station Corridor Checkpoints -->
        <div class="white-card">
          <div class="card-header">
            <div>
              <div class="card-header-title has-var-tooltip" data-tooltip-title="Corridor Stations" data-tooltip="24 calibrated stations along EDSA featuring accurate coordinates and berth capacities.">
                Corridor Checkpoints
              </div>
              <div class="card-header-sub" id="dir-sub-title">Route Orientation: Monumento → PITX</div>
            </div>

            <!-- Direction Toggle Switcher -->
            <div class="square-toggle-group">
              <button class="square-toggle-btn active" id="btn-dir-sb" onclick="setCorridorDirection('southbound')" data-tooltip-title="Southbound (SB)" data-tooltip="Circulate from Monumento terminal to PITX terminal.">SB</button>
              <button class="square-toggle-btn" id="btn-dir-nb" onclick="setCorridorDirection('northbound')" data-tooltip-title="Northbound (NB)" data-tooltip="Circulate from PITX terminal to Monumento terminal.">NB</button>
            </div>
          </div>

          <!-- Scrollable Station Timeline List -->
          <div class="station-list-container">
            <div id="timeline-checkpoint-list">
              <!-- Rendered via JS -->
            </div>
          </div>

          <div class="checklist-footer" id="route-duration-pill">
            Southbound Cycle: ~1h 35m
          </div>
        </div>

        <!-- Right: Map Card with Concentric Rings & Fixed Route Map -->
        <div class="map-card">
          
          <!-- Card Top Bar: Stylistic Transit Emblem & View Mode Switcher -->
          <div class="map-top-bar">
            <div class="map-style-badge" title="EDSA Carousel Corridor">
              <svg width="46" height="22" viewBox="0 0 46 22" fill="none">
                <rect x="0.5" y="0.5" width="45" height="21" rx="4" fill="#18181B" stroke="#27272A"/>
                <circle cx="11" cy="11" r="3.5" fill="#FFCC00"/>
                <line x1="16" y1="11" x2="30" y2="11" stroke="#3F3F46" stroke-width="1.8" stroke-dasharray="2 2"/>
                <circle cx="35" cy="11" r="3.5" fill="#2563EB"/>
              </svg>
            </div>

            <!-- Dual-View Switcher: Concentric Rings vs Route Map (Route Map Default) -->
            <div class="square-toggle-group">
              <button class="square-toggle-btn" id="btn-view-circle" onclick="setVisualMode('circle')" data-tooltip-title="Concentric Circles View" data-tooltip="Inner (NB ↺) & outer (SB ↻) concentric circles with equal-distance station nodes and circulating bus nodes.">
                Concentric Rings
              </button>
              <button class="square-toggle-btn active" id="btn-view-route" onclick="setVisualMode('route')" data-tooltip-title="Route Map View" data-tooltip="Calibrated EDSA corridor path matching the official transit alignment from the attachment.">
                Route Map
              </button>
            </div>
          </div>

          <!-- Map Legend -->
          <div class="map-legend-bar">
            <span class="legend-item has-var-tooltip" data-tooltip-title="Terminal Station" data-tooltip="Start / End Hub (Monumento & PITX) with high passenger exchange.">
              <svg width="14" height="14" viewBox="0 0 14 14" style="vertical-align:middle;"><circle cx="7" cy="7" r="6" fill="#FFCC00" stroke="#111215" stroke-width="1.8"/><circle cx="7" cy="7" r="2.2" fill="#111215"/></svg>
              Terminal
            </span>
            <span class="legend-item has-var-tooltip" data-tooltip-title="Major Transfer Hub" data-tooltip="Key interchange node connected to MRT-3 or LRT-2.">
              <svg width="14" height="14" viewBox="0 0 14 14" style="vertical-align:middle;"><circle cx="7" cy="7" r="5.5" fill="#7C3AED" stroke="#111215" stroke-width="1.6"/><circle cx="7" cy="7" r="1.8" fill="#FFFFFF"/></svg>
              Transfer Hub
            </span>
            <span class="legend-item has-var-tooltip" data-tooltip-title="Regular Busway Station" data-tooltip="Calibrated median busway berth along EDSA.">
              <svg width="14" height="14" viewBox="0 0 14 14" style="vertical-align:middle;"><circle cx="7" cy="7" r="5" fill="#FFFFFF" stroke="#111215" stroke-width="1.6"/><circle cx="7" cy="7" r="2" fill="#FFCC00"/></svg>
              Station
            </span>
            <span class="legend-item has-var-tooltip" data-tooltip-title="Southbound Bus" data-tooltip="Bus circulating southbound (outer ring / clockwise).">
              <span style="color:#2563EB; font-size:13px;">●</span> SB Bus
            </span>
            <span class="legend-item has-var-tooltip" data-tooltip-title="Northbound Bus" data-tooltip="Bus circulating northbound (inner ring / counter-clockwise).">
              <span style="color:#10B981; font-size:13px;">●</span> NB Bus
            </span>
            <span class="legend-item has-var-tooltip" data-tooltip-title="Rogue / Queued Bus" data-tooltip="Bus lingering to fill up or delayed in berth queue.">
              <span style="color:#EA580C; font-size:13px;">●</span> Rogue / Queue
            </span>
          </div>

          <!-- Visualization Canvas Wrapper -->
          <div class="map-canvas-wrapper" id="map-container-el">
            <div id="map-tooltip"></div>

            <!-- Overlaid Dual-Direction Corridor Status HUD -->
            <div class="map-status-overlay" id="map-status-overlay">
              <div class="map-status-chip sb active-dir" id="sb-status-chip" onclick="setCorridorDirection('southbound')" title="Click to inspect Southbound circulation">
                <div class="status-beacon-dot" id="sb-status-dot"></div>
                <span class="map-status-text" id="sb-status-text">[SB Lane] Corridor Flow: Clear <span class="status-sep">|</span> <span style="color:var(--signage-green);">Nominal flow</span></span>
              </div>
              <div class="map-status-chip nb" id="nb-status-chip" onclick="setCorridorDirection('northbound')" title="Click to inspect Northbound circulation">
                <div class="status-beacon-dot" id="nb-status-dot"></div>
                <span class="map-status-text" id="nb-status-text">[NB Lane] Corridor Flow: Clear <span class="status-sep">|</span> <span style="color:var(--signage-green);">Nominal flow</span></span>
              </div>
            </div>

            <!-- Floating Map Zoom Controls -->
            <div class="map-zoom-controls">
              <button class="zoom-btn" onclick="zoomIn()" title="Zoom In" aria-label="Zoom In">
                +
              </button>
              <button class="zoom-btn" onclick="zoomOut()" title="Zoom Out" aria-label="Zoom Out">
                −
              </button>
              <button class="zoom-btn" onclick="resetZoom()" title="Reset View" aria-label="Reset View" style="font-size:0.78rem;">
                ↺
              </button>
              <span class="zoom-level-badge" id="zoom-level-badge">100%</span>
            </div>

            <!-- 1. Dual Concentric Circles (Circular Carousel View) -->
            <svg id="circle-canvas-svg" width="100%" height="330" viewBox="0 0 540 330" style="display:none;">
              <!-- Radial spoke connecting lines between inner and outer rings -->
              <g id="circle-spokes-layer"></g>

              <!-- Outer Track Ring (Southbound - Clockwise ↻) -->
              <circle cx="270" cy="160" r="{r_outer}" fill="none" stroke="#CBD5E1" stroke-width="2.5" stroke-dasharray="3 4"/>
              
              <!-- Inner Track Ring (Northbound - Counter-Clockwise ↺) -->
              <circle cx="270" cy="160" r="{r_inner}" fill="none" stroke="#CBD5E1" stroke-width="2.5" stroke-dasharray="3 4"/>

              <!-- Central Hub Badge -->
              <rect x="215" y="130" width="110" height="60" rx="4" fill="#111215" stroke="#27272A" stroke-width="1.5"/>
              <rect x="220" y="135" width="22" height="15" rx="2" fill="#FFCC00"/>
              <text x="231" y="146" font-size="8" font-weight="800" text-anchor="middle" fill="#111215">ED</text>
              <text x="280" y="147" font-size="9.5" font-weight="800" text-anchor="middle" fill="#FFFFFF" letter-spacing="0.05em">CAROUSEL</text>
              <text x="270" y="166" font-size="7.5" font-weight="700" text-anchor="middle" fill="#A1A1AA">Outer: ↻ SB | Inner: ↺ NB</text>
              <text x="270" y="180" font-size="7.5" font-weight="800" text-anchor="middle" fill="#FFCC00">24 Station Berths</text>

              <!-- Dynamic Beacon Ripple Group for Circle View -->
              <g id="circle-beacon-group" style="display:none;">
                <circle id="circle-beacon-ring" cx="0" cy="0" r="16" fill="rgba(234, 88, 12, 0.25)">
                  <animate attributeName="r" values="10;20;10" dur="2s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.8;0.2;0.8" dur="2s" repeatCount="indefinite" />
                </circle>
                <circle id="circle-beacon-mid" cx="0" cy="0" r="9" fill="rgba(234, 88, 12, 0.35)"/>
                <circle id="circle-beacon-core" cx="0" cy="0" r="4.5" fill="#EA580C"/>
              </g>

              <!-- Smaller Bus Nodes Layer for Circle View -->
              <g id="circle-bus-layer"></g>

              <!-- Station Nodes Layer for Circle View -->
              <g id="circle-stations-layer"></g>

              <!-- Perimeter Station Text Annotations -->
              <g id="circle-labels-layer"></g>
            </svg>

            <!-- 2. Fixed Geographic Route Map (Matching Attachment - Default View) -->
            <svg id="route-vector-svg" width="100%" height="330" viewBox="0 0 540 330">
              <!-- Main Route Transit Polyline -->
              <path id="route-path" d="{route_path_d}" 
                    stroke="#18181B" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
              <path d="{route_path_d}" 
                    stroke="#FFCC00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="5 7" fill="none"/>

              <!-- Dynamic Rogue Actor / Chokepoint Beacon for Route Map -->
              <g id="dynamic-beacon-group" style="display:none;">
                <circle id="beacon-ring" cx="0" cy="0" r="18" fill="rgba(234, 88, 12, 0.2)">
                  <animate attributeName="r" values="12;22;12" dur="2s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.8;0.2;0.8" dur="2s" repeatCount="indefinite" />
                </circle>
                <circle id="beacon-mid" cx="0" cy="0" r="10" fill="rgba(234, 88, 12, 0.35)"/>
                <circle id="beacon-core" cx="0" cy="0" r="5" fill="#EA580C"/>
              </g>

              <!-- Dynamic Bus Marker Layer -->
              <g id="bus-layer"></g>

              <!-- Station Node Dots Layer -->
              <g id="station-dots-layer"></g>

              <!-- Key Station Text Labels along Route -->
              <text x="75.0" y="20" font-size="8.5" font-weight="700" text-anchor="middle" fill="#71717A">Monumento</text>
              <text x="155.0" y="20" font-size="8" font-weight="700" text-anchor="middle" fill="#71717A">Balintawak</text>
              <text x="235.0" y="20" font-size="8" font-weight="700" text-anchor="middle" fill="#71717A">FPJ / Muñoz</text>
              <text x="275.0" y="24" font-size="8.5" font-weight="700" text-anchor="middle" fill="#71717A">SM North</text>
              <text x="372.0" y="96" font-size="8" font-weight="700" fill="#71717A">Quezon Ave</text>
              <text x="445.0" y="172" font-size="8" font-weight="700" fill="#71717A">Cubao</text>
              <text x="450.0" y="224" font-size="8" font-weight="700" fill="#71717A">Ortigas</text>
              <text x="415.0" y="252" font-size="8" font-weight="700" fill="#71717A">Guadalupe</text>
              <text x="320.0" y="292" font-size="8" font-weight="700" text-anchor="middle" fill="#71717A">One Ayala</text>
              <text x="220.0" y="294" font-size="8" font-weight="700" text-anchor="middle" fill="#71717A">Taft</text>
              <text x="115.0" y="282" font-size="8" font-weight="700" text-anchor="end" fill="#71717A">MOA</text>
              <text x="135.0" y="328" font-size="8.5" font-weight="800" text-anchor="end" fill="#18181B">PITX</text>
            </svg>
          </div>

          <!-- Bottom Scrubber Controller -->
          <div class="scrubber-dock">
            <button class="play-square-btn" id="btn-play" onclick="togglePlay()" data-tooltip-title="Play / Pause" data-tooltip="Control automated minute-by-minute playback.">
              <svg id="play-icon-svg" width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="6,4 20,12 6,20"/>
              </svg>
            </button>
            <div class="clock-tag has-var-tooltip" id="clock-display" data-tooltip-title="Simulated Time" data-tooltip="Current simulation clock timestamp.">08:00 AM</div>
            <input type="range" class="time-slider" id="time-slider" min="0" max="{len(am_snaps)-1}" value="0" oninput="onSlide(this.value)">
            <button class="speed-pill has-var-tooltip" id="btn-speed" onclick="toggleSpeed()" data-tooltip-title="Playback Speed" data-tooltip="Toggle playback rate between 1x, 2x, and 4x speed.">1x</button>
          </div>
        </div>

      </section>

      <!-- Four Metric Panels below Corridor Checkpoints & Map -->
      <section class="bento-metrics">
        
        <!-- Card 1: Waiting Passengers -->
        <div class="bento-card bento-yellow">
          <div class="bento-top">
            <span class="bento-label has-var-tooltip" data-tooltip-title="Waiting Passengers (pax_q)" data-tooltip="Total commuters queued at all 24 station platforms awaiting bus arrival.">
              Waiting Commuters
            </span>
            <span class="card-square-tag yellow">PAX</span>
          </div>
          <div>
            <div class="bento-num" id="kpi-pax">4,839</div>
            <div class="bento-sub has-var-tooltip" data-tooltip-title="Directional Queues" data-tooltip="Commuters split across Southbound (Monumento → PITX) and Northbound (PITX → Monumento) lanes.">
              <span id="kpi-pax-sb-split">SB: 2,640</span> &nbsp;|&nbsp; <span id="kpi-pax-nb-split">NB: 2,199</span>
            </div>
          </div>
        </div>

        <!-- Card 2: Demand Trend Line Chart (NB, SB, and Cumulative) -->
        <div class="bento-card bento-pink clickable-demand-card" onclick="openDemandModal()" title="Click to open high-resolution demand trend overlay">
          <div class="bento-top">
            <span class="bento-label has-var-tooltip" data-tooltip-title="Demand Trend Line Chart" data-tooltip="Corridor passenger waiting demand over time split by Southbound (SB), Northbound (NB), and Cumulative total. Click card to open full-screen overlay, or click pills to toggle graphs.">
              Demand Trend
            </span>
            <span class="demand-expand-badge" title="Expand high-resolution view">
              <svg width="10" height="10" viewBox="0 0 16 16" fill="currentColor">
                <path d="M1.5 1a.5.5 0 0 0-.5.5v4a.5.5 0 0 0 1 0V2.707l3.146 3.147a.5.5 0 0 0 .708-.708L2.707 2H5.5a.5.5 0 0 0 0-1h-4zm13 0a.5.5 0 0 0-.5.5V5.5a.5.5 0 0 0 1 0V2.707l-3.146 3.147a.5.5 0 0 0 .708.708L14.707 2h2.793a.5.5 0 0 0 0-1h-4zm0 14a.5.5 0 0 0 .5-.5v-4a.5.5 0 0 0-1 0v2.793l-3.146-3.147a.5.5 0 0 0-.708.708L13.293 14H10.5a.5.5 0 0 0 0 1h4zm-13 0a.5.5 0 0 0 .5-.5v-2.793l3.146-3.147a.5.5 0 0 0-.708-.708L2 13.293V10.5a.5.5 0 0 0-1 0v4a.5.5 0 0 0 .5.5h4a.5.5 0 0 0 0-1H2.707z"/>
              </svg>
              EXPAND
            </span>
            <div class="chart-breakdown-tags">
              <span class="trend-tag cum" id="tag-cum" onclick="toggleDemandSeries('cum', event)" title="Click to toggle ALL Demand"><strong id="chart-live-cum">ALL: 4,839</strong></span>
              <span class="trend-tag sb" id="tag-sb" onclick="toggleDemandSeries('sb', event)" title="Click to toggle Southbound Demand"><strong id="chart-live-sb">SB: 2,640</strong></span>
              <span class="trend-tag nb" id="tag-nb" onclick="toggleDemandSeries('nb', event)" title="Click to toggle Northbound Demand"><strong id="chart-live-nb">NB: 2,199</strong></span>
            </div>
          </div>
          
          <div class="demand-chart-box">
            <svg id="pax-trend-svg" width="100%" height="100%" viewBox="0 0 240 60" preserveAspectRatio="none">
              <defs>
                <linearGradient id="cumGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stop-color="#18181B" stop-opacity="0.08"/>
                  <stop offset="100%" stop-color="#18181B" stop-opacity="0.0"/>
                </linearGradient>
              </defs>
              <path id="pax-area-path" fill="url(#cumGrad)" d=""/>
              <path id="pax-line-sb" fill="none" stroke="#2563EB" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d=""/>
              <path id="pax-line-nb" fill="none" stroke="#10B981" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d=""/>
              <path id="pax-line-cum" fill="none" stroke="#18181B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d=""/>
              <!-- Peak Marker Layer: Only peak labeled, NO vertical line -->
              <g id="peak-marker-group"></g>
              <!-- Live Time Cursor Dots for all 3 series -->
              <circle id="chart-cursor-sb" cx="0" cy="0" r="2.8" fill="#2563EB" stroke="#FFFFFF" stroke-width="1" style="display:none;"/>
              <circle id="chart-cursor-nb" cx="0" cy="0" r="2.8" fill="#10B981" stroke="#FFFFFF" stroke-width="1" style="display:none;"/>
              <circle id="chart-cursor-cum" cx="0" cy="0" r="3.4" fill="#18181B" stroke="#FFFFFF" stroke-width="1.2" style="display:none;"/>
            </svg>
          </div>

          <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.68rem; font-weight:800; opacity:0.85; margin-top:4px;">
            <span id="chart-time-start">08:00 AM</span>
            <div class="trend-chart-legend">
              <span class="legend-dot-label cum" id="legend-btn-cum" onclick="toggleDemandSeries('cum', event)" title="Click to toggle ALL line"><span class="legend-line cum"></span> ALL</span>
              <span class="legend-dot-label sb" id="legend-btn-sb" onclick="toggleDemandSeries('sb', event)" title="Click to toggle SB line"><span class="legend-line sb"></span> SB</span>
              <span class="legend-dot-label nb" id="legend-btn-nb" onclick="toggleDemandSeries('nb', event)" title="Click to toggle NB line"><span class="legend-line nb"></span> NB</span>
            </div>
            <span id="chart-time-end">11:00 AM</span>
          </div>
        </div>

        <!-- Card 3: Operating Fleet -->
        <div class="bento-card bento-green">
          <div class="bento-top">
            <span class="bento-label has-var-tooltip" data-tooltip-title="Operating Fleet (fleet_size)" data-tooltip="Total active transit buses circulating inside the segregated median busway.">
              Operating Fleet
            </span>
            <span class="card-square-tag green">FLEET</span>
          </div>
          <div>
            <div class="bento-num" id="kpi-fleet">100 <span class="bento-unit">buses</span></div>
            <div class="bento-sub has-var-tooltip" data-tooltip-title="Active Lane Allocation" data-tooltip="Buses segregated in physical median lanes with dedicated bypass overtaking paths.">
              Active in dedicated median busway
            </div>
          </div>
        </div>

        <!-- Card 4: Cycle Time & Reliability -->
        <div class="bento-card bento-blue">
          <div class="bento-top">
            <span class="bento-label has-var-tooltip" data-tooltip-title="Cycle Time & Headway Reliability" data-tooltip="Round-trip loop duration and headway consistency score (stability vs bunching).">
              Cycle & Score
            </span>
            <span class="card-square-tag blue">SCORE</span>
          </div>
          <div>
            <div class="bento-num" id="kpi-cycle">91.2 <span class="bento-unit">min</span></div>
            <div class="bento-sub has-var-tooltip" data-tooltip-title="Reliability Index" data-tooltip="Percentage of bus arrivals adhering to scheduled dispatch headway tolerances.">
              <span id="kpi-reliability" style="font-weight:800; color:var(--signage-blue);">94%</span> Headway Stability
            </div>
          </div>
        </div>

      </section>

    </main>

  </div>

  <!-- Simplified Full-Fill Footer (Edge to Edge) -->
  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-brand">
        <span class="footer-name">A Project by Artemio Arcega</span>
        <a href="https://artemiui.vercel.app/blog/article10" target="_blank" rel="noopener noreferrer" class="footer-how-btn" title="How it Works: Technical Simulation Writeup">
          <span class="q-mark">?</span>
          <span>How it Works</span>
        </a>
      </div>
      <div class="footer-links">
        <a href="https://artemiui.vercel.app" target="_blank" rel="noopener noreferrer" class="footer-icon-link" title="Portfolio (artemiui.vercel.app)" aria-label="Portfolio">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="2" y1="12" x2="22" y2="12"></line>
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
          </svg>
        </a>
        <a href="https://github.com/artemiui" target="_blank" rel="noopener noreferrer" class="footer-icon-link" title="GitHub" aria-label="GitHub">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.1-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z"/>
          </svg>
        </a>
        <a href="https://linkedin.com/in/artemioarcega" target="_blank" rel="noopener noreferrer" class="footer-icon-link" title="LinkedIn" aria-label="LinkedIn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/>
          </svg>
        </a>
        <a href="https://instagram.com/virtualsarili" target="_blank" rel="noopener noreferrer" class="footer-icon-link" title="Instagram" aria-label="Instagram">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
            <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
            <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
          </svg>
        </a>
      </div>
    </div>
  </footer>

  <!-- Tweakable Simulation Parameter Modal -->
  <div class="modal-backdrop" id="sim-modal">
    <div class="modal-card">
      <div class="modal-title">Simulation Parameters</div>
      <div class="modal-sub">Set observation window and operational transit variables across all 24 stations.</div>

      <div class="form-grid">
        <div class="form-field">
          <label class="has-var-tooltip" data-tooltip-title="Start Hour" data-tooltip="Beginning hour of the simulation observation window (24h format).">Start Hour (0-24)</label>
          <input type="number" id="inp-start" value="8.0" min="0" max="23.5" step="0.5">
        </div>
        <div class="form-field">
          <label class="has-var-tooltip" data-tooltip-title="End Hour" data-tooltip="Concluding hour of the simulation observation window (24h format).">End Hour (0-24)</label>
          <input type="number" id="inp-end" value="11.0" min="0.5" max="24" step="0.5">
        </div>
        <div class="form-field">
          <label class="has-var-tooltip" data-tooltip-title="Active Fleet" data-tooltip="Total number of operational buses assigned to the EDSA busway.">Active Fleet</label>
          <input type="number" id="inp-fleet" value="100" min="40" max="150" step="10">
        </div>
        <div class="form-field">
          <label class="has-var-tooltip" data-tooltip-title="Dispatch Headway" data-tooltip="Target interval in seconds between successive bus dispatches from terminals.">Dispatch Headway (sec)</label>
          <input type="number" id="inp-headway" value="120" min="60" max="240" step="15">
        </div>
        <div class="form-field">
          <label class="has-var-tooltip" data-tooltip-title="Bus Capacity" data-tooltip="Rated passenger capacity per bus (seated + standing load).">Bus Capacity</label>
          <select id="inp-cap">
            <option value="50">50 pax (Seated)</option>
            <option value="60" selected>60 pax (Nominal)</option>
            <option value="70">70 pax (Crush)</option>
          </select>
        </div>
        <div class="form-field">
          <label class="has-var-tooltip" data-tooltip-title="Rogue Actor Probability" data-tooltip="Chance of a bus lingering beyond regular dwell to fill seats ('nagpupuno'), blocking downstream traffic.">Rogue Actor Chance ("Nagpupuno")</label>
          <select id="inp-rogue">
            <option value="0.0">0% (Strict Discipline / No Lingering)</option>
            <option value="0.10" selected>10% (Moderate Lingering)</option>
            <option value="0.20">20% (Frequent Lingering)</option>
            <option value="0.35">35% (Severe Unregulated Lingering)</option>
          </select>
        </div>
      </div>

      <div class="modal-actions">
        <button class="square-btn" onclick="closeModal()">Cancel</button>
        <button class="square-btn yellow" id="btn-submit-sim" onclick="executeCustomSimulation()">
          Run Simulation
        </button>
      </div>
    </div>
  </div>

  <!-- Expanded Demand Trend High-Resolution Data Overlay Modal -->
  <div class="modal-backdrop" id="demand-trend-modal" onclick="closeDemandModalOnBackdrop(event)">
    <div class="modal-card modal-card-wide" onclick="event.stopPropagation()">
      
      <!-- Modal Close Bar -->
      <div style="display:flex; justify-content:flex-end; margin-bottom:12px;">
        <button class="modal-close-btn" onclick="closeDemandModal()" title="Close overlay (Esc)" aria-label="Close modal">
          &times;
        </button>
      </div>

      <!-- Live Stat HUD Ribbon inside Modal -->
      <div class="modal-demand-hud">
        <div class="modal-hud-item">
          <span class="modal-hud-label">Corridor Observation Window</span>
          <span class="modal-hud-val" id="modal-hud-window">08:00 AM &ndash; 11:00 AM</span>
        </div>
        <div class="modal-hud-item">
          <span class="modal-hud-label">Peak Total Demand</span>
          <span class="modal-hud-val" id="modal-hud-peak-total">4,839 pax</span>
        </div>
        <div class="modal-hud-item">
          <span class="modal-hud-label">Peak Southbound (SB)</span>
          <span class="modal-hud-val" style="color:#2563EB;" id="modal-hud-peak-sb">2,640 pax</span>
        </div>
        <div class="modal-hud-item">
          <span class="modal-hud-label">Peak Northbound (NB)</span>
          <span class="modal-hud-val" style="color:#10B981;" id="modal-hud-peak-nb">2,199 pax</span>
        </div>
        <div class="modal-hud-item">
          <span class="modal-hud-label">Sim Time Demand</span>
          <span class="modal-hud-val" id="modal-hud-live-total">4,839 pax</span>
        </div>
      </div>

      <!-- Series Toggles Toolbar in Modal -->
      <div class="modal-series-toolbar">
        <span style="font-size:0.72rem; font-weight:800; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.04em;">
          Visible Graphs:
        </span>
        <button type="button" class="modal-series-pill cum" id="modal-toggle-cum" onclick="toggleDemandSeries('cum', event)" title="Toggle ALL demand graph">
          <span>●</span> ALL (Cumulative)
        </button>
        <button type="button" class="modal-series-pill sb" id="modal-toggle-sb" onclick="toggleDemandSeries('sb', event)" title="Toggle Southbound graph">
          <span>●</span> Southbound (SB)
        </button>
        <button type="button" class="modal-series-pill nb" id="modal-toggle-nb" onclick="toggleDemandSeries('nb', event)" title="Toggle Northbound graph">
          <span>●</span> Northbound (NB)
        </button>
        <div style="margin-left:auto; font-size:0.7rem; color:var(--text-muted); font-weight:600;">
          <span id="modal-hover-tip">Hover or drag across chart to inspect time</span>
        </div>
      </div>

      <!-- Big High-Resolution SVG Canvas Box -->
      <div class="modal-chart-box" id="modal-chart-container">
        <svg id="modal-pax-trend-svg" width="100%" height="280" viewBox="0 0 800 280">
          <defs>
            <linearGradient id="modalCumGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stop-color="#18181B" stop-opacity="0.14"/>
              <stop offset="100%" stop-color="#18181B" stop-opacity="0.01"/>
            </linearGradient>
          </defs>

          <!-- Background gridlines & Y-axis labels -->
          <g id="modal-gridlines-group"></g>

          <!-- Cumulative Area Fill -->
          <path id="modal-area-cum" fill="url(#modalCumGrad)" d=""/>

          <!-- High-Res Trend Lines -->
          <path id="modal-line-cum" fill="none" stroke="#18181B" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" d=""/>
          <path id="modal-line-sb" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d=""/>
          <path id="modal-line-nb" fill="none" stroke="#10B981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d=""/>

          <!-- Peak Callouts Layer -->
          <g id="modal-peaks-group"></g>

          <!-- Live Scrubber Vertical Line & Series Dots -->
          <line id="modal-scrub-line" x1="0" y1="25" x2="0" y2="245" stroke="#18181B" stroke-width="1.2" stroke-dasharray="3 3" style="display:none;"/>
          <circle id="modal-dot-cum" cx="0" cy="0" r="4.2" fill="#18181B" stroke="#FFFFFF" stroke-width="1.8" style="display:none;"/>
          <circle id="modal-dot-sb" cx="0" cy="0" r="3.8" fill="#2563EB" stroke="#FFFFFF" stroke-width="1.5" style="display:none;"/>
          <circle id="modal-dot-nb" cx="0" cy="0" r="3.8" fill="#10B981" stroke="#FFFFFF" stroke-width="1.5" style="display:none;"/>

          <!-- X-Axis Labels Layer -->
          <g id="modal-xaxis-group"></g>
        </svg>

        <!-- Floating Inspection Tooltip -->
        <div id="modal-chart-tooltip" class="modal-chart-tooltip"></div>
      </div>

      <!-- Modal Footer -->
      <div style="display:flex; justify-content:space-between; align-items:center; margin-top:14px; padding-top:12px; border-top:1px solid var(--border-subtle);">
        <div style="font-size:0.72rem; color:var(--text-muted); font-weight:600;">
          Tip: Dragging on the chart scrubs simulation playback time in real time.
        </div>
        <button class="square-btn" style="padding:6px 16px; font-size:0.78rem;" onclick="closeDemandModal()">
          Close
        </button>
      </div>
    </div>
  </div>

  <script>
    const presets = {json.dumps(presets)};
    const stationDefs = {json.dumps(station_svg_nodes)};
    let activePreset = 'am_peak';
    let snapshots = presets['am_peak'].snapshots;
    let metadata = presets['am_peak'].meta;

    let currentIndex = 0;
    let isPlaying = false;
    let playInterval = null;
    let playSpeed = 1;
    let progressTimer = null;
    let currentDirection = 'southbound';
    let currentVisualMode = 'route';

    // Camera state for Zoom & Pan on SVG Maps
    const mapCameras = {{
      circle: {{ scale: 1.0, x: 0, y: 0 }},
      route: {{ scale: 1.0, x: 0, y: 0 }}
    }};

    function zoomIn() {{
      const cam = mapCameras[currentVisualMode];
      cam.scale = Math.min(4.0, Math.round(cam.scale * 1.25 * 100) / 100);
      applyCamera();
    }}

    function zoomOut() {{
      const cam = mapCameras[currentVisualMode];
      cam.scale = Math.max(0.6, Math.round((cam.scale / 1.25) * 100) / 100);
      applyCamera();
    }}

    function resetZoom() {{
      const cam = mapCameras[currentVisualMode];
      cam.scale = 1.0;
      cam.x = 0;
      cam.y = 0;
      applyCamera();
    }}

    function applyCamera() {{
      const mode = currentVisualMode;
      const cam = mapCameras[mode];
      const svg = (mode === 'circle') 
        ? document.getElementById('circle-canvas-svg') 
        : document.getElementById('route-vector-svg');
      if (!svg) return;

      const baseW = 540;
      const baseH = 330;
      const curW = baseW / cam.scale;
      const curH = baseH / cam.scale;

      const minX = (baseW / 2) - (curW / 2) - cam.x;
      const minY = (baseH / 2) - (curH / 2) - cam.y;

      svg.setAttribute('viewBox', `${{minX.toFixed(2)}} ${{minY.toFixed(2)}} ${{curW.toFixed(2)}} ${{curH.toFixed(2)}}`);

      const badge = document.getElementById('zoom-level-badge');
      if (badge) {{
        badge.innerText = `${{Math.round(cam.scale * 100)}}%`;
      }}
    }}

    // Toggle between Concentric Rings and Route Map views
    function setVisualMode(mode) {{
      currentVisualMode = mode;
      document.getElementById('btn-view-circle').classList.toggle('active', mode === 'circle');
      document.getElementById('btn-view-route').classList.toggle('active', mode === 'route');

      const circleSvg = document.getElementById('circle-canvas-svg');
      const routeSvg = document.getElementById('route-vector-svg');
      if (mode === 'circle') {{
        if (circleSvg) circleSvg.style.display = 'block';
        if (routeSvg) routeSvg.style.display = 'none';
      }} else {{
        if (circleSvg) circleSvg.style.display = 'none';
        if (routeSvg) routeSvg.style.display = 'block';
      }}
      applyCamera();
    }}

    // Tooltip System for Variables
    function initVariableTooltips() {{
      const tt = document.getElementById('var-tooltip');
      const ttTitle = document.getElementById('tt-title');
      const ttDesc = document.getElementById('tt-desc');

      document.body.addEventListener('mousemove', (e) => {{
        const target = e.target.closest('[data-tooltip]');
        if (target) {{
          const title = target.getAttribute('data-tooltip-title') || 'Transit Variable';
          const desc = target.getAttribute('data-tooltip') || '';
          ttTitle.innerText = title;
          ttDesc.innerText = desc;
          tt.style.display = 'block';

          let x = e.clientX + 14;
          let y = e.clientY + 14;
          if (x + 260 > window.innerWidth) x = e.clientX - 260;
          if (y + 80 > window.innerHeight) y = e.clientY - 80;
          tt.style.left = x + 'px';
          tt.style.top = y + 'px';
        }} else {{
          tt.style.display = 'none';
        }}
      }});
    }}

    // Direction Rotation Switcher
    function setCorridorDirection(dir) {{
      currentDirection = dir;
      document.getElementById('btn-dir-sb').classList.toggle('active', dir === 'southbound');
      document.getElementById('btn-dir-nb').classList.toggle('active', dir === 'northbound');
      
      const sbChip = document.getElementById('sb-status-chip');
      const nbChip = document.getElementById('nb-status-chip');
      if (sbChip) sbChip.classList.toggle('active-dir', dir === 'southbound');
      if (nbChip) nbChip.classList.toggle('active-dir', dir === 'northbound');

      const subTitle = document.getElementById('dir-sub-title');
      const durPill = document.getElementById('route-duration-pill');
      if (dir === 'southbound') {{
        subTitle.innerText = "Route Orientation: Monumento → PITX";
        durPill.innerText = "Southbound Cycle: ~1h 35m";
      }} else {{
        subTitle.innerText = "Route Orientation: PITX → Monumento";
        durPill.innerText = "Northbound Cycle: ~1h 35m";
      }}
      initChecklist();
      renderSnapshot(currentIndex);
    }}

    // Build Station Nodes for both Concentric Rings and Route Map (Bigger & High-Contrast Transit Wayfinding Colors)
    function initStationDots() {{
      // 1. Concentric Circles View
      const circleSpokes = document.getElementById('circle-spokes-layer');
      const circleStLayer = document.getElementById('circle-stations-layer');
      const circleLblLayer = document.getElementById('circle-labels-layer');

      if (circleSpokes && circleStLayer && circleLblLayer) {{
        let spokesHtml = '';
        let dotsHtml = '';
        let labelsHtml = '';

        stationDefs.forEach((st, i) => {{
          // Spoke connector line
          spokesHtml += `<line x1="${{st.circle_x_in}}" y1="${{st.circle_y_in}}" x2="${{st.circle_x_out}}" y2="${{st.circle_y_out}}" stroke="#CBD5E1" stroke-width="1.3" stroke-dasharray="2 2" />`;

          // Outer station berth (Southbound)
          // Terminal: r=8.5 (Canary Yellow, bold obsidian stroke, dark bullseye)
          // Transfer Hub: r=7.5 (Transit Purple, bold obsidian stroke, white core)
          // Regular Station: r=6.5 (Porcelain White, bold obsidian stroke, yellow core)
          const rOut = st.is_terminal ? 8.5 : (st.is_hotspot ? 7.5 : 6.5);
          const fillOut = st.is_terminal ? '#FFCC00' : (st.is_hotspot ? '#7C3AED' : '#FFFFFF');
          const strokeWOut = st.is_terminal ? 2.4 : 2.0;
          const innerCoreROut = st.is_terminal ? 3.2 : (st.is_hotspot ? 2.6 : 2.2);
          const innerCoreFillOut = st.is_terminal ? '#111215' : (st.is_hotspot ? '#FFFFFF' : '#FFCC00');

          dotsHtml += `
            <g class="station-node-group" onmouseenter="showStationTooltip(event, ${{i}})" onmouseleave="hideStationTooltip()" onclick="highlightStationDot(${{i}})" style="cursor:pointer;">
              <circle id="circle-dot-out-${{i}}" cx="${{st.circle_x_out}}" cy="${{st.circle_y_out}}" r="${{rOut}}" fill="${{fillOut}}" stroke="#111215" stroke-width="${{strokeWOut}}" />
              <circle cx="${{st.circle_x_out}}" cy="${{st.circle_y_out}}" r="${{innerCoreROut}}" fill="${{innerCoreFillOut}}" pointer-events="none" />
            </g>
          `;

          // Inner station berth (Northbound)
          const rIn = st.is_terminal ? 8.5 : (st.is_hotspot ? 7.5 : 6.5);
          const fillIn = st.is_terminal ? '#FFCC00' : (st.is_hotspot ? '#7C3AED' : '#FFFFFF');
          const strokeWIn = st.is_terminal ? 2.4 : 2.0;
          const innerCoreRIn = st.is_terminal ? 3.2 : (st.is_hotspot ? 2.6 : 2.2);
          const innerCoreFillIn = st.is_terminal ? '#111215' : (st.is_hotspot ? '#FFFFFF' : '#FFCC00');

          dotsHtml += `
            <g class="station-node-group" onmouseenter="showStationTooltip(event, ${{i}})" onmouseleave="hideStationTooltip()" onclick="highlightStationDot(${{i}})" style="cursor:pointer;">
              <circle id="circle-dot-in-${{i}}" cx="${{st.circle_x_in}}" cy="${{st.circle_y_in}}" r="${{rIn}}" fill="${{fillIn}}" stroke="#111215" stroke-width="${{strokeWIn}}" />
              <circle cx="${{st.circle_x_in}}" cy="${{st.circle_y_in}}" r="${{innerCoreRIn}}" fill="${{innerCoreFillIn}}" pointer-events="none" />
            </g>
          `;

          // Perimeter label for key stations
          const keyStationIndices = [0, 2, 4, 5, 8, 11, 13, 14, 15, 16, 18, 20, 23];
          if (keyStationIndices.includes(i)) {{
            const rLbl = 139.0;
            const lx = round(270.0 + rLbl * Math.cos(st.theta), 1);
            const ly = round(160.0 + rLbl * Math.sin(st.theta), 1);
            const cosVal = Math.cos(st.theta);
            const anchor = cosVal > 0.3 ? "start" : (cosVal < -0.3 ? "end" : "middle");
            const shortName = st.name.replace(' (Roosevelt)', '').replace(' (Cubao)', '').replace(' (Ayala)', '').replace('Parañaque Integrated Terminal Exchange ', '').replace(' (MOA)', '');
            labelsHtml += `<text x="${{lx}}" y="${{ly + 3}}" font-size="7.5" font-weight="800" fill="#27272A" text-anchor="${{anchor}}">${{shortName}}</text>`;
          }}
        }});

        circleSpokes.innerHTML = spokesHtml;
        circleStLayer.innerHTML = dotsHtml;
        circleLblLayer.innerHTML = labelsHtml;
      }}

      // 2. Fixed Route Map View (Enlarged with Distinctive Badges)
      const routeLayer = document.getElementById('station-dots-layer');
      if (routeLayer) {{
        let html = '';
        stationDefs.forEach((st, i) => {{
          const r = st.is_terminal ? 10.5 : (st.is_hotspot ? 8.8 : 7.5);
          const fill = st.is_terminal ? '#FFCC00' : (st.is_hotspot ? '#7C3AED' : '#FFFFFF');
          const strokeW = st.is_terminal ? 2.8 : (st.is_hotspot ? 2.4 : 2.2);
          const innerR = st.is_terminal ? 4.2 : (st.is_hotspot ? 3.0 : 2.6);
          const innerFill = st.is_terminal ? '#111215' : (st.is_hotspot ? '#FFFFFF' : '#FFCC00');

          html += `
            <g class="station-node-group" onmouseenter="showStationTooltip(event, ${{i}})" onmouseleave="hideStationTooltip()" onclick="highlightStationDot(${{i}})" style="cursor:pointer;">
              <circle id="dot-${{i}}" cx="${{st.x}}" cy="${{st.y}}" r="${{r}}" fill="${{fill}}" stroke="#111215" stroke-width="${{strokeW}}" />
              <circle cx="${{st.x}}" cy="${{st.y}}" r="${{innerR}}" fill="${{innerFill}}" pointer-events="none" />
              ${{st.is_terminal ? `<circle cx="${{st.x}}" cy="${{st.y}}" r="1.6" fill="#FFFFFF" pointer-events="none" />` : ''}}
            </g>
          `;
        }});
        routeLayer.innerHTML = html;
      }}
    }}

    function round(val, dec = 1) {{
      const factor = Math.pow(10, dec);
      return Math.round(val * factor) / factor;
    }}

    // Build 24-Station Checklist with Transit Wayfinding Signage Design
    function initChecklist() {{
      const list = document.getElementById('timeline-checkpoint-list');
      if (!list) return;
      let html = '';
      
      const orderedIndices = currentDirection === 'southbound'
        ? stationDefs.map((_, i) => i)
        : stationDefs.map((_, i) => i).reverse();

      orderedIndices.forEach((stIdx, displaySeq) => {{
        const st = stationDefs[stIdx];
        const badgeClass = st.is_terminal ? 'terminal' : (st.is_hotspot ? 'hotspot' : '');
        const iconClass = st.is_terminal ? '' : (st.is_hotspot ? 'purple' : 'blue');
        const seqNum = String(displaySeq + 1).padStart(2, '0');
        
        html += `
          <div class="station-row" id="chk-item-${{stIdx}}" onclick="highlightStationDot(${{stIdx}})" data-tooltip-title="${{st.name}}" data-tooltip="Platform: ${{st.platform}} | Capacity: ${{st.berths}} Berths">
            <div class="station-left">
              <div class="signage-badge ${{badgeClass}}">${{seqNum}}</div>
              <div class="signage-icon-box ${{iconClass}}">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="4" y="3" width="16" height="16" rx="2"/>
                  <circle cx="8" cy="15" r="1.5" fill="#111215"/>
                  <circle cx="16" cy="15" r="1.5" fill="#111215"/>
                </svg>
              </div>
              <div>
                <div style="display:flex; align-items:center; gap:6px;">
                  <span class="st-name">${{st.name}}</span>
                </div>
                <div class="st-sub" id="chk-sub-${{stIdx}}">${{st.berths}} Berths | ${{st.platform}}</div>
              </div>
            </div>
            <div class="st-time" id="chk-time-${{stIdx}}">--</div>
          </div>
        `;
      }});
      list.innerHTML = html;
    }}

    function highlightStationDot(idx) {{
      const dot = document.getElementById('dot-' + idx);
      const cDotOut = document.getElementById('circle-dot-out-' + idx);
      const cDotIn = document.getElementById('circle-dot-in-' + idx);
      const st = stationDefs[idx];

      [dot, cDotOut, cDotIn].forEach(d => {{
        if (d) {{
          d.setAttribute('r', '13.5');
          setTimeout(() => {{
            const baseR = (d === dot)
              ? (st.is_terminal ? '10.5' : (st.is_hotspot ? '8.8' : '7.5'))
              : (st.is_terminal ? '8.5' : (st.is_hotspot ? '7.5' : '6.5'));
            d.setAttribute('r', baseR);
          }}, 800);
        }}
      }});
    }}

    function showStationTooltip(e, idx) {{
      const tip = document.getElementById('map-tooltip');
      const container = document.getElementById('map-container-el');
      if (!tip || !container) return;
      const rect = container.getBoundingClientRect();
      const st = stationDefs[idx];
      const snap = snapshots[currentIndex];
      const stData = snap?.stations[st.name] || {{ pax_q_total: 0, pax_q_forward: 0, pax_q_reverse: 0, buses_queuing: 0, avg_delay_min: 0, has_rogue_bus: false }};

      const rogueTag = stData.has_rogue_bus ? '<br><span style="color:#EA580C; font-weight:700;">[Rogue Bus Lingering]</span>' : '';

      tip.innerHTML = `
        <div style="color:#FFCC00; font-weight:800; font-size:0.78rem;">${{st.name}}</div>
        Type: ${{st.platform}} (${{st.berths}} berths)<br>
        SB Waiting: ${{stData.pax_q_forward || 0}} | NB Waiting: ${{stData.pax_q_reverse || 0}}<br>
        Buses Queued: ${{stData.buses_queuing || 0}} (${{stData.avg_delay_min || 0}}m delay)
        ${{rogueTag}}
      `;

      let tipX = e.clientX - rect.left + 15;
      let tipY = e.clientY - rect.top - 20;
      if (tipX + 220 > rect.width) tipX = e.clientX - rect.left - 220;
      if (tipY < 10) tipY = 10;

      tip.style.left = tipX + 'px';
      tip.style.top = tipY + 'px';
      tip.style.display = 'block';
    }}

    function hideStationTooltip() {{
      const tip = document.getElementById('map-tooltip');
      if (tip) tip.style.display = 'none';
    }}

    window.demandSeriesVisibility = {{ cum: true, sb: true, nb: true }};

    function toggleDemandSeries(key, e) {{
      if (e) e.stopPropagation();
      const current = window.demandSeriesVisibility[key];
      const activeCount = Object.values(window.demandSeriesVisibility).filter(Boolean).length;
      if (current && activeCount <= 1) return; // Prevent disabling all graphs

      window.demandSeriesVisibility[key] = !current;
      applyDemandSeriesVisibility();
    }}

    function applyDemandSeriesVisibility() {{
      const vis = window.demandSeriesVisibility || {{ cum: true, sb: true, nb: true }};

      // 1. Mini Card Tags and Legend
      const tagCum = document.getElementById('tag-cum');
      const tagSB = document.getElementById('tag-sb');
      const tagNB = document.getElementById('tag-nb');
      if (tagCum) tagCum.classList.toggle('series-disabled', !vis.cum);
      if (tagSB) tagSB.classList.toggle('series-disabled', !vis.sb);
      if (tagNB) tagNB.classList.toggle('series-disabled', !vis.nb);

      const legCum = document.getElementById('legend-btn-cum');
      const legSB = document.getElementById('legend-btn-sb');
      const legNB = document.getElementById('legend-btn-nb');
      if (legCum) legCum.classList.toggle('series-disabled', !vis.cum);
      if (legSB) legSB.classList.toggle('series-disabled', !vis.sb);
      if (legNB) legNB.classList.toggle('series-disabled', !vis.nb);

      // 2. Mini Card SVG Elements
      const lineCum = document.getElementById('pax-line-cum');
      const areaCum = document.getElementById('pax-area-path');
      const peakGroup = document.getElementById('peak-marker-group');
      const dotCum = document.getElementById('chart-cursor-cum');

      const lineSB = document.getElementById('pax-line-sb');
      const dotSB = document.getElementById('chart-cursor-sb');

      const lineNB = document.getElementById('pax-line-nb');
      const dotNB = document.getElementById('chart-cursor-nb');

      if (lineCum) lineCum.style.display = vis.cum ? 'inline' : 'none';
      if (areaCum) areaCum.style.display = vis.cum ? 'inline' : 'none';
      if (peakGroup) peakGroup.style.display = vis.cum ? 'inline' : 'none';
      if (dotCum) dotCum.style.display = vis.cum ? 'block' : 'none';

      if (lineSB) lineSB.style.display = vis.sb ? 'inline' : 'none';
      if (dotSB) dotSB.style.display = vis.sb ? 'block' : 'none';

      if (lineNB) lineNB.style.display = vis.nb ? 'inline' : 'none';
      if (dotNB) dotNB.style.display = vis.nb ? 'block' : 'none';

      // 3. Modal Toolbar Pills
      const modCum = document.getElementById('modal-toggle-cum');
      const modSB = document.getElementById('modal-toggle-sb');
      const modNB = document.getElementById('modal-toggle-nb');
      if (modCum) modCum.classList.toggle('series-disabled', !vis.cum);
      if (modSB) modSB.classList.toggle('series-disabled', !vis.sb);
      if (modNB) modNB.classList.toggle('series-disabled', !vis.nb);

      // 4. Modal SVG Elements
      const mLineCum = document.getElementById('modal-line-cum');
      const mAreaCum = document.getElementById('modal-area-cum');
      const mPeakCumEl = document.getElementById('modal-peak-cum-el');
      const mDotCum = document.getElementById('modal-dot-cum');

      const mLineSB = document.getElementById('modal-line-sb');
      const mPeakSBEl = document.getElementById('modal-peak-sb-el');
      const mDotSB = document.getElementById('modal-dot-sb');

      const mLineNB = document.getElementById('modal-line-nb');
      const mPeakNBEl = document.getElementById('modal-peak-nb-el');
      const mDotNB = document.getElementById('modal-dot-nb');

      if (mLineCum) mLineCum.style.display = vis.cum ? 'inline' : 'none';
      if (mAreaCum) mAreaCum.style.display = vis.cum ? 'inline' : 'none';
      if (mPeakCumEl) mPeakCumEl.style.display = vis.cum ? 'inline' : 'none';
      if (mDotCum) mDotCum.style.display = vis.cum ? 'block' : 'none';

      if (mLineSB) mLineSB.style.display = vis.sb ? 'inline' : 'none';
      if (mPeakSBEl) mPeakSBEl.style.display = vis.sb ? 'inline' : 'none';
      if (mDotSB) mDotSB.style.display = vis.sb ? 'block' : 'none';

      if (mLineNB) mLineNB.style.display = vis.nb ? 'inline' : 'none';
      if (mPeakNBEl) mPeakNBEl.style.display = vis.nb ? 'inline' : 'none';
      if (mDotNB) mDotNB.style.display = vis.nb ? 'block' : 'none';
    }}

    function openDemandModal() {{
      const modal = document.getElementById('demand-trend-modal');
      if (!modal) return;
      modal.style.display = 'flex';
      drawModalPaxChart();
      renderSnapshot(currentIndex);
    }}

    function closeDemandModal() {{
      const modal = document.getElementById('demand-trend-modal');
      if (modal) modal.style.display = 'none';
    }}

    function closeDemandModalOnBackdrop(e) {{
      if (e.target && e.target.id === 'demand-trend-modal') {{
        closeDemandModal();
      }}
    }}

    let isModalScrubbing = false;

    function initModalChartInteractions() {{
      const container = document.getElementById('modal-chart-container');
      if (!container || container._hasListener) return;
      container._hasListener = true;

      const tooltip = document.getElementById('modal-chart-tooltip');

      function getIdxFromEvent(e) {{
        if (!snapshots || snapshots.length === 0) return 0;
        const rect = container.getBoundingClientRect();
        const clientX = e.clientX !== undefined ? e.clientX : (e.touches && e.touches[0] ? e.touches[0].clientX : 0);
        const clientY = e.clientY !== undefined ? e.clientY : (e.touches && e.touches[0] ? e.touches[0].clientY : 0);

        const padLeft = 55;
        const padRight = 25;
        const chartW = 800 - padLeft - padRight;
        const scaleX = 800 / rect.width;
        const svgX = (clientX - rect.left) * scaleX;
        const clampedX = Math.max(padLeft, Math.min(800 - padRight, svgX));
        const frac = (clampedX - padLeft) / chartW;
        const idx = Math.min(snapshots.length - 1, Math.max(0, Math.round(frac * (snapshots.length - 1))));
        return {{ idx, clientX, clientY, rect }};
      }}

      function handleHoverOrScrub(e, isDrag) {{
        const {{ idx, clientX, clientY, rect }} = getIdxFromEvent(e);
        if (isDrag) {{
          pause();
          currentIndex = idx;
          renderSnapshot(idx);
        }}

        if (tooltip && window._demandData) {{
          const snap = snapshots[idx];
          const cum = window._demandData.cumSeries[idx];
          const sb = window._demandData.sbSeries[idx];
          const nb = window._demandData.nbSeries[idx];
          const vis = window.demandSeriesVisibility || {{ cum: true, sb: true, nb: true }};

          let html = `<div style="font-size:0.75rem; font-weight:800; margin-bottom:3px; color:#FFCC00;">${{snap.time_str}}</div>`;
          if (vis.cum) html += `<div>ALL: <strong>${{cum.toLocaleString()}}</strong> pax</div>`;
          if (vis.sb) html += `<div style="color:#60A5FA;">SB Lane: <strong>${{sb.toLocaleString()}}</strong> pax</div>`;
          if (vis.nb) html += `<div style="color:#34D399;">NB Lane: <strong>${{nb.toLocaleString()}}</strong> pax</div>`;

          tooltip.innerHTML = html;
          tooltip.style.display = 'block';

          const tipX = Math.min(rect.width - 90, Math.max(90, clientX - rect.left));
          const tipY = Math.max(30, clientY - rect.top);
          tooltip.style.left = tipX + 'px';
          tooltip.style.top = tipY + 'px';
        }}
      }}

      container.addEventListener('mousedown', (e) => {{
        isModalScrubbing = true;
        handleHoverOrScrub(e, true);
      }});

      window.addEventListener('mousemove', (e) => {{
        if (isModalScrubbing) {{
          handleHoverOrScrub(e, true);
        }}
      }});

      container.addEventListener('mousemove', (e) => {{
        if (!isModalScrubbing) {{
          handleHoverOrScrub(e, false);
        }}
      }});

      container.addEventListener('mouseleave', () => {{
        if (!isModalScrubbing && tooltip) {{
          tooltip.style.display = 'none';
          if (window._modalPtsCum && window._modalPtsCum[currentIndex]) {{
            const mScrubLine = document.getElementById('modal-scrub-line');
            if (mScrubLine) {{
              mScrubLine.setAttribute('x1', window._modalPtsCum[currentIndex].x);
              mScrubLine.setAttribute('x2', window._modalPtsCum[currentIndex].x);
            }}
          }}
        }}
      }});

      window.addEventListener('mouseup', () => {{
        if (isModalScrubbing) {{
          isModalScrubbing = false;
          if (tooltip) tooltip.style.display = 'none';
        }}
      }});

      container.addEventListener('touchstart', (e) => {{
        isModalScrubbing = true;
        handleHoverOrScrub(e, true);
      }}, {{ passive: true }});

      container.addEventListener('touchmove', (e) => {{
        if (isModalScrubbing) {{
          handleHoverOrScrub(e, true);
        }}
      }}, {{ passive: true }});

      window.addEventListener('touchend', () => {{
        if (isModalScrubbing) {{
          isModalScrubbing = false;
          if (tooltip) tooltip.style.display = 'none';
        }}
      }});
    }}

    function drawModalPaxChart() {{
      if (!window._demandData || !snapshots || snapshots.length === 0) return;
      const {{ cumSeries, sbSeries, nbSeries, n }} = window._demandData;

      const svgW = 800;
      const svgH = 280;
      const padLeft = 55;
      const padRight = 25;
      const padTop = 25;
      const padBottom = 35;
      const chartW = svgW - padLeft - padRight;
      const chartH = svgH - padTop - padBottom;

      const maxCum = Math.max(...cumSeries, 1);
      let step = 1000;
      if (maxCum <= 1200) step = 200;
      else if (maxCum <= 2500) step = 500;
      else if (maxCum <= 6000) step = 1000;
      else step = 2000;
      const niceMax = Math.ceil(maxCum / step) * step;
      const nSteps = Math.round(niceMax / step);

      // 1. Gridlines and Y-axis labels
      const gridlinesGroup = document.getElementById('modal-gridlines-group');
      if (gridlinesGroup) {{
        let gHtml = '';
        for (let s = 0; s <= nSteps; s++) {{
          const val = s * step;
          const y = Number(((svgH - padBottom) - (val / niceMax) * chartH).toFixed(1));
          gHtml += `<line x1="${{padLeft}}" y1="${{y}}" x2="${{svgW - padRight}}" y2="${{y}}" stroke="#E4E4E7" stroke-width="1" stroke-dasharray="3 3"/>`;
          gHtml += `<text x="${{padLeft - 8}}" y="${{y + 3.5}}" font-size="10" font-weight="700" fill="#71717A" text-anchor="end">${{val.toLocaleString()}}</text>`;
        }}
        gridlinesGroup.innerHTML = gHtml;
      }}

      // 2. X-axis time labels
      const xaxisGroup = document.getElementById('modal-xaxis-group');
      if (xaxisGroup) {{
        let xHtml = '';
        const numTicks = 6;
        for (let t = 0; t <= numTicks; t++) {{
          const snapIdx = Math.min(n - 1, Math.round((t / numTicks) * (n - 1)));
          const x = Number((padLeft + (snapIdx / Math.max(1, n - 1)) * chartW).toFixed(1));
          const timeStr = snapshots[snapIdx] ? snapshots[snapIdx].time_str : '';
          xHtml += `<line x1="${{x}}" y1="${{svgH - padBottom}}" x2="${{x}}" y2="${{svgH - padBottom + 4}}" stroke="#A1A1AA" stroke-width="1"/>`;
          xHtml += `<text x="${{x}}" y="${{svgH - padBottom + 16}}" font-size="10" font-weight="700" fill="#71717A" text-anchor="middle">${{timeStr}}</text>`;
        }}
        xaxisGroup.innerHTML = xHtml;
      }}

      // 3. Compute High-Resolution Points
      const ptsCum = [];
      const ptsSB = [];
      const ptsNB = [];

      let peakCumIdx = 0, peakCumVal = -1;
      let peakSBIdx = 0, peakSBVal = -1;
      let peakNBIdx = 0, peakNBVal = -1;

      for (let i = 0; i < n; i++) {{
        const x = Number((padLeft + (i / Math.max(1, n - 1)) * chartW).toFixed(1));

        const yCum = Number(((svgH - padBottom) - (cumSeries[i] / niceMax) * chartH).toFixed(1));
        ptsCum.push({{ x, y: yCum, val: cumSeries[i] }});
        if (cumSeries[i] > peakCumVal) {{ peakCumVal = cumSeries[i]; peakCumIdx = i; }}

        const ySB = Number(((svgH - padBottom) - (sbSeries[i] / niceMax) * chartH).toFixed(1));
        ptsSB.push({{ x, y: ySB, val: sbSeries[i] }});
        if (sbSeries[i] > peakSBVal) {{ peakSBVal = sbSeries[i]; peakSBIdx = i; }}

        const yNB = Number(((svgH - padBottom) - (nbSeries[i] / niceMax) * chartH).toFixed(1));
        ptsNB.push({{ x, y: yNB, val: nbSeries[i] }});
        if (nbSeries[i] > peakNBVal) {{ peakNBVal = nbSeries[i]; peakNBIdx = i; }}
      }}

      window._modalPtsCum = ptsCum;
      window._modalPtsSB = ptsSB;
      window._modalPtsNB = ptsNB;

      // 4. Build SVG Path Strings
      let dCum = `M ${{ptsCum[0].x}} ${{ptsCum[0].y}}`;
      let dSB = `M ${{ptsSB[0].x}} ${{ptsSB[0].y}}`;
      let dNB = `M ${{ptsNB[0].x}} ${{ptsNB[0].y}}`;

      for (let i = 1; i < n; i++) {{
        dCum += ` L ${{ptsCum[i].x}} ${{ptsCum[i].y}}`;
        dSB += ` L ${{ptsSB[i].x}} ${{ptsSB[i].y}}`;
        dNB += ` L ${{ptsNB[i].x}} ${{ptsNB[i].y}}`;
      }}

      const xEnd = ptsCum[n - 1].x;
      const xStart = ptsCum[0].x;
      const yBase = svgH - padBottom;
      const dArea = `${{dCum}} L ${{xEnd}} ${{yBase}} L ${{xStart}} ${{yBase}} Z`;

      const mLineCum = document.getElementById('modal-line-cum');
      const mAreaCum = document.getElementById('modal-area-cum');
      const mLineSB = document.getElementById('modal-line-sb');
      const mLineNB = document.getElementById('modal-line-nb');

      if (mLineCum) mLineCum.setAttribute('d', dCum);
      if (mAreaCum) mAreaCum.setAttribute('d', dArea);
      if (mLineSB) mLineSB.setAttribute('d', dSB);
      if (mLineNB) mLineNB.setAttribute('d', dNB);

      // 5. Render Peaks Layer in Modal
      const peaksGroup = document.getElementById('modal-peaks-group');
      if (peaksGroup && ptsCum[peakCumIdx]) {{
        const ptC = ptsCum[peakCumIdx];
        const ptS = ptsSB[peakSBIdx];
        const ptN = ptsNB[peakNBIdx];
        let pTextX = ptC.x;
        let pAnchor = "middle";
        if (pTextX < 90) {{ pTextX = padLeft + 10; pAnchor = "start"; }}
        else if (pTextX > svgW - 90) {{ pTextX = svgW - padRight - 10; pAnchor = "end"; }}

        peaksGroup.innerHTML = `
          <g id="modal-peak-cum-el">
            <circle cx="${{ptC.x}}" cy="${{ptC.y}}" r="4" fill="#18181B" stroke="#FFFFFF" stroke-width="1.6" />
            <rect x="${{pTextX - (pAnchor === 'middle' ? 52 : (pAnchor === 'end' ? 104 : 0))}}" y="${{Math.max(12, ptC.y - 22)}}" width="104" height="17" rx="3" fill="rgba(24, 24, 27, 0.88)"/>
            <text x="${{pTextX - (pAnchor === 'middle' ? 0 : (pAnchor === 'end' ? 52 : -52))}}" y="${{Math.max(24, ptC.y - 10)}}" font-size="9" font-weight="800" font-family="'Plus Jakarta Sans', sans-serif" text-anchor="middle" fill="#FFCC00">
              ${{peakCumVal.toLocaleString()}} peak Total
            </text>
          </g>
          <g id="modal-peak-sb-el">
            <circle cx="${{ptS.x}}" cy="${{ptS.y}}" r="3.4" fill="#2563EB" stroke="#FFFFFF" stroke-width="1.2" />
          </g>
          <g id="modal-peak-nb-el">
            <circle cx="${{ptN.x}}" cy="${{ptN.y}}" r="3.4" fill="#10B981" stroke="#FFFFFF" stroke-width="1.2" />
          </g>
        `;
      }}

      // 6. Update HUD Ribbon Stat Values in Modal
      const hudWin = document.getElementById('modal-hud-window');
      const hudPeakTotal = document.getElementById('modal-hud-peak-total');
      const hudPeakSB = document.getElementById('modal-hud-peak-sb');
      const hudPeakNB = document.getElementById('modal-hud-peak-nb');

      if (hudWin && snapshots[0] && snapshots[n - 1]) {{
        hudWin.innerText = `${{snapshots[0].time_str}} – ${{snapshots[n - 1].time_str}}`;
      }}
      if (hudPeakTotal && snapshots[peakCumIdx]) {{
        hudPeakTotal.innerHTML = `${{peakCumVal.toLocaleString()}} <span class="modal-hud-sub">(@ ${{snapshots[peakCumIdx].time_str}})</span>`;
      }}
      if (hudPeakSB && snapshots[peakSBIdx]) {{
        hudPeakSB.innerHTML = `${{peakSBVal.toLocaleString()}} <span class="modal-hud-sub">(@ ${{snapshots[peakSBIdx].time_str}})</span>`;
      }}
      if (hudPeakNB && snapshots[peakNBIdx]) {{
        hudPeakNB.innerHTML = `${{peakNBVal.toLocaleString()}} <span class="modal-hud-sub">(@ ${{snapshots[peakNBIdx].time_str}})</span>`;
      }}

      initModalChartInteractions();
      applyDemandSeriesVisibility();
    }}

    function drawPaxChart() {{
      if (!snapshots || snapshots.length === 0) return;
      const svgW = 240;
      const svgH = 60;
      const padTop = 16;
      const padBottom = 6;
      const chartH = svgH - padTop - padBottom;

      const n = snapshots.length;
      const cumSeries = [];
      const sbSeries = [];
      const nbSeries = [];

      for (let i = 0; i < n; i++) {{
        const s = snapshots[i];
        let sb = 0;
        let nb = 0;
        if (s.stations) {{
          for (const st of Object.values(s.stations)) {{
            sb += (st.pax_q_forward !== undefined ? st.pax_q_forward : Math.round((st.pax_q_total || 0) * 0.55));
            nb += (st.pax_q_reverse !== undefined ? st.pax_q_reverse : Math.round((st.pax_q_total || 0) * 0.45));
          }}
        }}
        const cum = s.total_waiting_pax !== undefined ? s.total_waiting_pax : (sb + nb);
        cumSeries.push(cum);
        sbSeries.push(sb);
        nbSeries.push(nb);
      }}

      // Shared vertical scale: baseline at 0 to highest cumulative peak
      const maxVal = Math.max(...cumSeries, 1);
      const minVal = 0;

      // Find peak index and value for cumulative
      let peakIdx = 0;
      let peakVal = -1;
      for (let i = 0; i < n; i++) {{
        if (cumSeries[i] > peakVal) {{
          peakVal = cumSeries[i];
          peakIdx = i;
        }}
      }}

      window._demandData = {{ cumSeries, sbSeries, nbSeries, maxVal, minVal, n, peakIdx, peakVal }};

      const ptsCum = [];
      const ptsSB = [];
      const ptsNB = [];

      for (let i = 0; i < n; i++) {{
        const x = Number(((i / Math.max(1, n - 1)) * svgW).toFixed(1));
        
        const normCum = (cumSeries[i] - minVal) / (maxVal - minVal);
        const yCum = Number(((svgH - padBottom) - (normCum * chartH)).toFixed(1));
        ptsCum.push({{ x, y: yCum, val: cumSeries[i] }});

        const normSB = (sbSeries[i] - minVal) / (maxVal - minVal);
        const ySB = Number(((svgH - padBottom) - (normSB * chartH)).toFixed(1));
        ptsSB.push({{ x, y: ySB, val: sbSeries[i] }});

        const normNB = (nbSeries[i] - minVal) / (maxVal - minVal);
        const yNB = Number(((svgH - padBottom) - (normNB * chartH)).toFixed(1));
        ptsNB.push({{ x, y: yNB, val: nbSeries[i] }});
      }}

      // Build SVG paths
      let dCum = `M ${{ptsCum[0].x}} ${{ptsCum[0].y}}`;
      let dSB = `M ${{ptsSB[0].x}} ${{ptsSB[0].y}}`;
      let dNB = `M ${{ptsNB[0].x}} ${{ptsNB[0].y}}`;

      for (let i = 1; i < n; i++) {{
        dCum += ` L ${{ptsCum[i].x}} ${{ptsCum[i].y}}`;
        dSB += ` L ${{ptsSB[i].x}} ${{ptsSB[i].y}}`;
        dNB += ` L ${{ptsNB[i].x}} ${{ptsNB[i].y}}`;
      }}

      const dArea = `${{dCum}} L ${{ptsCum[n - 1].x}} ${{svgH - padBottom}} L ${{ptsCum[0].x}} ${{svgH - padBottom}} Z`;

      const lineCumEl = document.getElementById('pax-line-cum');
      const lineSBEl = document.getElementById('pax-line-sb');
      const lineNBEl = document.getElementById('pax-line-nb');
      const areaEl = document.getElementById('pax-area-path');

      if (lineCumEl) lineCumEl.setAttribute('d', dCum);
      if (lineSBEl) lineSBEl.setAttribute('d', dSB);
      if (lineNBEl) lineNBEl.setAttribute('d', dNB);
      if (areaEl) areaEl.setAttribute('d', dArea);

      // Render Peak Marker and Label on Cumulative
      const peakGroup = document.getElementById('peak-marker-group');
      if (peakGroup && ptsCum[peakIdx]) {{
        const peakPt = ptsCum[peakIdx];
        let textX = peakPt.x;
        let anchor = "middle";
        if (textX < 32) {{ textX = 4; anchor = "start"; }}
        else if (textX > svgW - 32) {{ textX = svgW - 4; anchor = "end"; }}

        peakGroup.innerHTML = `
          <circle cx="${{peakPt.x}}" cy="${{peakPt.y}}" r="3.2" fill="#18181B" stroke="#FFFFFF" stroke-width="1.2" />
          <text x="${{textX}}" y="${{Math.max(10, peakPt.y - 4)}}" font-size="8.5" font-weight="800" font-family="'Plus Jakarta Sans', sans-serif" text-anchor="${{anchor}}" fill="#18181B">
            ${{peakVal.toLocaleString()}} peak
          </text>
        `;
      }}

      const startEl = document.getElementById('chart-time-start');
      const midEl = document.getElementById('chart-time-mid');
      const endEl = document.getElementById('chart-time-end');
      if (startEl && snapshots[0]) startEl.innerText = snapshots[0].time_str;
      if (midEl && snapshots[Math.floor(n / 2)]) midEl.innerText = snapshots[Math.floor(n / 2)].time_str;
      if (endEl && snapshots[n - 1]) endEl.innerText = snapshots[n - 1].time_str;

      window._chartPtsCum = ptsCum;
      window._chartPtsSB = ptsSB;
      window._chartPtsNB = ptsNB;

      applyDemandSeriesVisibility();
      const modal = document.getElementById('demand-trend-modal');
      if (modal && modal.style.display === 'flex') {{
        drawModalPaxChart();
      }}
    }}

    function renderSnapshot(idx) {{
      const snap = snapshots[idx];
      if (!snap) return;

      document.getElementById('clock-display').innerText = snap.time_str;
      document.getElementById('time-slider').value = idx;
      document.getElementById('kpi-pax').innerText = snap.total_waiting_pax.toLocaleString();
      document.getElementById('kpi-fleet').innerHTML = `${{metadata.fleet_size || 100}} <span class="bento-unit">buses</span>`;

      // Update Live Demand Trend Chart
      const vis = window.demandSeriesVisibility || {{ cum: true, sb: true, nb: true }};
      if (window._chartPtsCum && window._chartPtsCum[idx]) {{
        const ptCum = window._chartPtsCum[idx];
        const ptSB = window._chartPtsSB[idx];
        const ptNB = window._chartPtsNB[idx];

        const dotCum = document.getElementById('chart-cursor-cum');
        const dotSB = document.getElementById('chart-cursor-sb');
        const dotNB = document.getElementById('chart-cursor-nb');

        if (dotCum) {{
          dotCum.style.display = vis.cum ? 'block' : 'none';
          dotCum.setAttribute('cx', ptCum.x);
          dotCum.setAttribute('cy', ptCum.y);
        }}
        if (dotSB) {{
          dotSB.style.display = vis.sb ? 'block' : 'none';
          dotSB.setAttribute('cx', ptSB.x);
          dotSB.setAttribute('cy', ptSB.y);
        }}
        if (dotNB) {{
          dotNB.style.display = vis.nb ? 'block' : 'none';
          dotNB.setAttribute('cx', ptNB.x);
          dotNB.setAttribute('cy', ptNB.y);
        }}

        // Live values in header breakdown
        const liveCumEl = document.getElementById('chart-live-cum');
        const liveSbEl = document.getElementById('chart-live-sb');
        const liveNbEl = document.getElementById('chart-live-nb');
        if (liveCumEl) liveCumEl.innerText = `ALL: ${{ptCum.val.toLocaleString()}}`;
        if (liveSbEl) liveSbEl.innerText = `SB: ${{ptSB.val.toLocaleString()}}`;
        if (liveNbEl) liveNbEl.innerText = `NB: ${{ptNB.val.toLocaleString()}}`;
      }}

      // Update Modal Live Scrubber Line, Dots, and HUD if modal is rendered
      if (window._modalPtsCum && window._modalPtsCum[idx]) {{
        const mPtCum = window._modalPtsCum[idx];
        const mPtSB = window._modalPtsSB[idx];
        const mPtNB = window._modalPtsNB[idx];

        const mDotCum = document.getElementById('modal-dot-cum');
        const mDotSB = document.getElementById('modal-dot-sb');
        const mDotNB = document.getElementById('modal-dot-nb');
        const mScrubLine = document.getElementById('modal-scrub-line');

        if (mDotCum) {{
          mDotCum.style.display = vis.cum ? 'block' : 'none';
          mDotCum.setAttribute('cx', mPtCum.x);
          mDotCum.setAttribute('cy', mPtCum.y);
        }}
        if (mDotSB) {{
          mDotSB.style.display = vis.sb ? 'block' : 'none';
          mDotSB.setAttribute('cx', mPtSB.x);
          mDotSB.setAttribute('cy', mPtSB.y);
        }}
        if (mDotNB) {{
          mDotNB.style.display = vis.nb ? 'block' : 'none';
          mDotNB.setAttribute('cx', mPtNB.x);
          mDotNB.setAttribute('cy', mPtNB.y);
        }}
        if (mScrubLine) {{
          mScrubLine.style.display = 'block';
          mScrubLine.setAttribute('x1', mPtCum.x);
          mScrubLine.setAttribute('x2', mPtCum.x);
        }}

        const mLiveTotal = document.getElementById('modal-hud-live-total');
        if (mLiveTotal) {{
          mLiveTotal.innerHTML = `${{snap.total_waiting_pax.toLocaleString()}} <span class="modal-hud-sub">(${{snap.time_str}})</span>`;
        }}
      }}

      // Directional Split Calculation
      const isSB = (currentDirection === 'southbound');
      let totalSBWait = 0;
      let totalNBWait = 0;
      for (const stData of Object.values(snap.stations)) {{
        totalSBWait += (stData.pax_q_forward !== undefined ? stData.pax_q_forward : Math.round(stData.pax_q_total * 0.55));
        totalNBWait += (stData.pax_q_reverse !== undefined ? stData.pax_q_reverse : Math.round(stData.pax_q_total * 0.45));
      }}
      const sbSplitEl = document.getElementById('kpi-pax-sb-split');
      const nbSplitEl = document.getElementById('kpi-pax-nb-split');
      if (sbSplitEl) sbSplitEl.innerText = `SB: ${{totalSBWait.toLocaleString()}}`;
      if (nbSplitEl) nbSplitEl.innerText = `NB: ${{totalNBWait.toLocaleString()}}`;

      // Identify active rogue actor and primary chokepoint for BOTH SB and NB
      let sbWorstStation = null;
      let sbMaxQueue = 0;
      let sbHasRogue = false;
      let sbRogueStation = null;

      let nbWorstStation = null;
      let nbMaxQueue = 0;
      let nbHasRogue = false;
      let nbRogueStation = null;

      for (const [stName, stData] of Object.entries(snap.stations)) {{
        // Southbound (SB)
        const sbQ = stData.buses_queuing_sb !== undefined ? stData.buses_queuing_sb : (stData.buses_queuing || 0);
        const sbR = stData.has_rogue_bus_sb !== undefined ? stData.has_rogue_bus_sb : (stData.has_rogue_bus || false);
        if (sbR && !sbHasRogue) {{
          sbHasRogue = true;
          sbRogueStation = stName;
        }}
        if (sbQ > sbMaxQueue) {{
          sbMaxQueue = sbQ;
          sbWorstStation = stName;
        }}

        // Northbound (NB)
        const nbQ = stData.buses_queuing_nb !== undefined ? stData.buses_queuing_nb : 0;
        const nbR = stData.has_rogue_bus_nb !== undefined ? stData.has_rogue_bus_nb : false;
        if (nbR && !nbHasRogue) {{
          nbHasRogue = true;
          nbRogueStation = stName;
        }}
        if (nbQ > nbMaxQueue) {{
          nbMaxQueue = nbQ;
          nbWorstStation = stName;
        }}
      }}
      if (sbHasRogue && sbRogueStation) sbWorstStation = sbRogueStation;
      if (nbHasRogue && nbRogueStation) nbWorstStation = nbRogueStation;

      // Active direction reference for KPIs and map beacon
      const worstStationName = isSB ? (sbWorstStation || nbWorstStation) : (nbWorstStation || sbWorstStation);
      const maxBusQueue = isSB ? sbMaxQueue : nbMaxQueue;
      const hasRogue = isSB ? sbHasRogue : nbHasRogue;

      // Overlaid Dual Status HUD over Map (Both SB and NB)
      const sbDot = document.getElementById('sb-status-dot');
      const sbText = document.getElementById('sb-status-text');
      const nbDot = document.getElementById('nb-status-dot');
      const nbText = document.getElementById('nb-status-text');
      const sbChip = document.getElementById('sb-status-chip');
      const nbChip = document.getElementById('nb-status-chip');

      if (sbChip) sbChip.classList.toggle('active-dir', isSB);
      if (nbChip) nbChip.classList.toggle('active-dir', !isSB);

      // SB Status Text
      if (sbText) {{
        if (sbHasRogue && sbRogueStation) {{
          sbText.innerHTML = `[SB Lane] Rogue Bus: ${{sbRogueStation}} <span class="status-sep">|</span> <span style="color:var(--signage-yellow);">Lingering (${{sbMaxQueue}} buses queued)</span>`;
          if (sbDot) sbDot.style.background = "var(--signage-orange)";
        }} else if (sbMaxQueue > 2 && sbWorstStation) {{
          sbText.innerHTML = `[SB Lane] Chokepoint: ${{sbWorstStation}} <span class="status-sep">|</span> <span style="color:var(--signage-yellow);">${{sbMaxQueue}} buses queued (~${{sbMaxQueue * 12}}m backup)</span>`;
          if (sbDot) sbDot.style.background = "var(--signage-orange)";
        }} else {{
          sbText.innerHTML = `[SB Lane] Corridor Flow: Clear <span class="status-sep">|</span> <span style="color:var(--signage-green);">Nominal flow</span>`;
          if (sbDot) sbDot.style.background = "var(--signage-green)";
        }}
      }}

      // NB Status Text
      if (nbText) {{
        if (nbHasRogue && nbRogueStation) {{
          nbText.innerHTML = `[NB Lane] Rogue Bus: ${{nbRogueStation}} <span class="status-sep">|</span> <span style="color:var(--signage-yellow);">Lingering (${{nbMaxQueue}} buses queued)</span>`;
          if (nbDot) nbDot.style.background = "var(--signage-orange)";
        }} else if (nbMaxQueue > 2 && nbWorstStation) {{
          nbText.innerHTML = `[NB Lane] Chokepoint: ${{nbWorstStation}} <span class="status-sep">|</span> <span style="color:var(--signage-yellow);">${{nbMaxQueue}} buses queued (~${{nbMaxQueue * 12}}m backup)</span>`;
          if (nbDot) nbDot.style.background = "var(--signage-orange)";
        }} else {{
          nbText.innerHTML = `[NB Lane] Corridor Flow: Clear <span class="status-sep">|</span> <span style="color:var(--signage-green);">Nominal flow</span>`;
          if (nbDot) nbDot.style.background = "var(--signage-green)";
        }}
      }}

      // Dynamic Beacon Ripple on SVG maps (Circle View & Route View)
      const beaconGroup = document.getElementById('dynamic-beacon-group');
      const beaconRing = document.getElementById('beacon-ring');
      const beaconMid = document.getElementById('beacon-mid');
      const beaconCore = document.getElementById('beacon-core');

      const circleBeaconGroup = document.getElementById('circle-beacon-group');
      const circleBeaconRing = document.getElementById('circle-beacon-ring');
      const circleBeaconMid = document.getElementById('circle-beacon-mid');
      const circleBeaconCore = document.getElementById('circle-beacon-core');

      if ((hasRogue || maxBusQueue > 2) && worstStationName) {{
        const stNode = stationDefs.find(s => s.name === worstStationName);
        if (stNode) {{
          // Update Route Map Beacon
          if (beaconGroup) {{
            beaconGroup.style.display = 'block';
            beaconRing.setAttribute('cx', stNode.x);
            beaconRing.setAttribute('cy', stNode.y);
            beaconMid.setAttribute('cx', stNode.x);
            beaconMid.setAttribute('cy', stNode.y);
            beaconCore.setAttribute('cx', stNode.x);
            beaconCore.setAttribute('cy', stNode.y);
            beaconCore.setAttribute('fill', hasRogue ? '#EA580C' : (isSB ? '#2563EB' : '#10B981'));
          }}

          // Update Concentric Circles Beacon
          if (circleBeaconGroup) {{
            circleBeaconGroup.style.display = 'block';
            const cx = isSB ? stNode.circle_x_out : stNode.circle_x_in;
            const cy = isSB ? stNode.circle_y_out : stNode.circle_y_in;
            circleBeaconRing.setAttribute('cx', cx);
            circleBeaconRing.setAttribute('cy', cy);
            circleBeaconMid.setAttribute('cx', cx);
            circleBeaconMid.setAttribute('cy', cy);
            circleBeaconCore.setAttribute('cx', cx);
            circleBeaconCore.setAttribute('cy', cy);
            circleBeaconCore.setAttribute('fill', hasRogue ? '#EA580C' : (isSB ? '#2563EB' : '#10B981'));
          }}
        }}
      }} else {{
        if (beaconGroup) beaconGroup.style.display = 'none';
        if (circleBeaconGroup) circleBeaconGroup.style.display = 'none';
      }}

      // Dynamic Cycle Time estimate
      const worstStData = worstStationName ? (snap.stations[worstStationName] || {{ avg_delay_min: 0 }}) : {{ avg_delay_min: 0 }};
      const cycleMin = (86.0 + (worstStData.avg_delay_min * 0.75) + (snap.total_buses_queuing * 0.12)).toFixed(1);
      document.getElementById('kpi-cycle').innerHTML = `${{cycleMin}} <span class="bento-unit">min</span>`;

      // Dynamic Reliability score
      const relScore = Math.max(68, Math.min(99, Math.round(98 - (maxBusQueue * 0.5) - (worstStData.avg_delay_min * 0.5))));
      document.getElementById('kpi-reliability').innerText = `${{relScore}}%`;

      // Update 24 Stations in Checkpoints List
      const orderedIndices = currentDirection === 'southbound'
        ? stationDefs.map((_, i) => i)
        : stationDefs.map((_, i) => i).reverse();

      orderedIndices.forEach((stIdx, displaySeq) => {{
        const st = stationDefs[stIdx];
        const stData = snap.stations[st.name] || {{ pax_q_total: 0, pax_q_forward: 0, pax_q_reverse: 0, buses_queuing: 0, avg_delay_min: 0, has_rogue_bus: false }};
        const subEl = document.getElementById(`chk-sub-${{stIdx}}`);
        const timeEl = document.getElementById(`chk-time-${{stIdx}}`);

        const dirPax = isSB
          ? (stData.pax_q_forward !== undefined ? stData.pax_q_forward : Math.round(stData.pax_q_total * 0.55))
          : (stData.pax_q_reverse !== undefined ? stData.pax_q_reverse : Math.round(stData.pax_q_total * 0.45));

        const dirQueue = isSB
          ? (stData.buses_queuing_sb !== undefined ? stData.buses_queuing_sb : (stData.buses_queuing || 0))
          : (stData.buses_queuing_nb !== undefined ? stData.buses_queuing_nb : 0);

        const dirRogue = isSB
          ? (stData.has_rogue_bus_sb !== undefined ? stData.has_rogue_bus_sb : stData.has_rogue_bus)
          : (stData.has_rogue_bus_nb !== undefined ? stData.has_rogue_bus_nb : false);

        const dirDelay = isSB
          ? (stData.avg_delay_min_sb !== undefined ? stData.avg_delay_min_sb : stData.avg_delay_min)
          : (stData.avg_delay_min_nb !== undefined ? stData.avg_delay_min_nb : 0);

        const dirLabel = isSB ? 'SB' : 'NB';

        if (subEl) {{
          if (dirRogue) {{
            subEl.innerHTML = `<span style="color:#EA580C; font-weight:800;">[Rogue Bus Lingering]</span> | ${{dirPax}} pax in line`;
          }} else if (dirQueue > 2) {{
            subEl.innerHTML = `<span style="color:#EA580C; font-weight:800;">${{dirQueue}} buses queued (${{dirDelay}}m delay)</span> | ${{dirPax}} pax`;
          }} else if (dirPax === 0) {{
            subEl.innerHTML = `<span style="color:var(--signage-green); font-weight:700;">Free Flow (0 pax)</span> | ${{st.berths}} berths`;
          }} else {{
            subEl.innerText = `${{dirPax}} waiting pax (${{dirLabel}}) | ${{st.berths}} berths`;
            subEl.style.color = 'var(--text-muted)';
            subEl.style.fontWeight = 'normal';
          }}
        }}

        if (timeEl) {{
          const progressFraction = displaySeq / (orderedIndices.length - 1);
          const currentHourDec = snap.hour + (progressFraction * 1.5);
          const hh = Math.floor(currentHourDec % 24);
          const mm = Math.floor(((currentHourDec % 24) - hh) * 60);
          const ampm = (hh < 12 || hh === 24) ? "AM" : "PM";
          const dispH = (hh <= 12) ? (hh === 0 ? 12 : hh) : hh - 12;
          timeEl.innerText = `${{String(dispH).padStart(2, '0')}}:${{String(mm).padStart(2, '0')}} ${{ampm}}`;
        }}
      }});

      // Render Dynamic Moving Buses for both Concentric Circles & Route Map
      updateBusLayer(snap, idx);
    }}

    function updateBusLayer(snap, idx) {{
      const totalFleet = 24;
      const nSteps = Math.max(1, snapshots.length);
      const frac = idx / nSteps;

      // Identify choke points
      let rogueSB = snap.has_active_rogue_sb || false;
      let rogueNB = snap.has_active_rogue_nb || false;
      let maxQueueSB = snap.max_bus_queue_sb || 0;
      let maxQueueNB = snap.max_bus_queue_nb || 0;

      // ─────────────────────────────────────────────────────────────
      // A. CONCENTRIC RINGS BUS LAYER
      // ─────────────────────────────────────────────────────────────
      const circleBusLayer = document.getElementById('circle-bus-layer');
      if (circleBusLayer) {{
        let circleBusHtml = '';
        const cx = 270.0;
        const cy = 160.0;
        const rOut = {r_outer}; // 115px (Outer circle - Southbound)
        const rIn = {r_inner};   // 85px (Inner circle - Northbound)

        // Continuous circulation loop: Southbound (outer ring, clockwise, Blue) -> Northbound (inner ring, counter-clockwise, Green)
        for (let b = 0; b < totalFleet; b++) {{
          const busCycle = ((b / totalFleet) + (frac * 2.2)) % 1.0;
          const isSB = busCycle < 0.5;
          const p = isSB ? (busCycle / 0.5) : ((busCycle - 0.5) / 0.5);

          // Transition smoothly between outer and inner ring at turnaround zones
          let r = isSB ? rOut : rIn;
          if (p > 0.94) {{
            const bridge = (p - 0.94) / 0.06;
            r = isSB ? (rOut - bridge * (rOut - rIn)) : (rIn + bridge * (rOut - rIn));
          }}

          const theta = isSB
            ? (-Math.PI / 2.0 + (p * 2.0 * Math.PI))
            : (-Math.PI / 2.0 - (p * 2.0 * Math.PI));

          const bx = round(cx + r * Math.cos(theta), 1);
          const by = round(cy + r * Math.sin(theta), 1);

          let dotColor = isSB ? '#2563EB' : '#10B981';
          if (isSB && rogueSB && b === 0) dotColor = '#EA580C';
          else if (!isSB && rogueNB && b === 12) dotColor = '#EA580C';

          circleBusHtml += `<circle cx="${{bx}}" cy="${{by}}" r="3.4" fill="${{dotColor}}" stroke="#111215" stroke-width="1.2" />`;
        }}

        circleBusLayer.innerHTML = circleBusHtml;
      }}

      // ─────────────────────────────────────────────────────────────
      // B. ROUTE MAP BUS LAYER
      // ─────────────────────────────────────────────────────────────
      const busLayer = document.getElementById('bus-layer');
      const pathEl = document.getElementById('route-path');
      if (busLayer && pathEl) {{
        const totalLen = pathEl.getTotalLength();
        let chokeDistSB = -1;
        let chokeDistNB = -1;

        for (const [stName, stData] of Object.entries(snap.stations)) {{
          if (stData.has_rogue_bus_sb || (stData.buses_queuing_sb && stData.buses_queuing_sb > 2)) {{
            const stIdx = stationDefs.findIndex(s => s.name === stName);
            if (stIdx >= 0) {{
              chokeDistSB = totalLen * (stIdx / (stationDefs.length - 1));
              break;
            }}
          }}
        }}

        for (const [stName, stData] of Object.entries(snap.stations)) {{
          if (stData.has_rogue_bus_nb || (stData.buses_queuing_nb && stData.buses_queuing_nb > 2)) {{
            const stIdx = stationDefs.findIndex(s => s.name === stName);
            if (stIdx >= 0) {{
              chokeDistNB = totalLen * (stIdx / (stationDefs.length - 1));
              break;
            }}
          }}
        }}

        let routeBusHtml = '';

        // Single fleet circulating continuously:
        // When traveling Southbound (Monumento -> PITX), bus is Blue (#2563EB).
        // Upon rotating at PITX terminal, it turns around and changes color to Green (#10B981) heading Northbound!
        // Upon rotating at Monumento terminal, it turns around and changes back to Blue (#2563EB).
        for (let b = 0; b < totalFleet; b++) {{
          const busCycle = ((b / totalFleet) + (frac * 2.2)) % 1.0;
          const isSB = busCycle < 0.5;
          const p = isSB ? (busCycle / 0.5) : ((busCycle - 0.5) / 0.5);

          // Southbound moves 0 -> totalLen, Northbound moves totalLen -> 0
          const dist = isSB ? (p * totalLen) : ((1.0 - p) * totalLen);

          // If trapped at choke point queue, skip drawing regular moving bus
          if (isSB && chokeDistSB >= 0 && maxQueueSB > 2 && Math.abs(dist - chokeDistSB) < 14) continue;
          if (!isSB && chokeDistNB >= 0 && maxQueueNB > 2 && Math.abs(dist - chokeDistNB) < 14) continue;

          // Lane lateral offset with terminal turnaround rotation curve
          let xOff = isSB ? -1.5 : 1.5;
          let yOff = isSB ? -1.5 : 1.5;
          if (p > 0.95) {{
            const turn = (p - 0.95) / 0.05;
            if (isSB) {{
              // Rotating at PITX turnaround: moves from SB lane (-1.5) to NB lane (+1.5)
              xOff = -1.5 + (3.0 * turn);
              yOff = -1.5 + (3.0 * turn);
            }} else {{
              // Rotating at Monumento turnaround: moves from NB lane (+1.5) to SB lane (-1.5)
              xOff = 1.5 - (3.0 * turn);
              yOff = 1.5 - (3.0 * turn);
            }}
          }}

          const clampedDist = Math.max(0, Math.min(totalLen, dist));
          const pt = pathEl.getPointAtLength(clampedDist);

          let dotColor = isSB ? '#2563EB' : '#10B981';
          if (isSB && rogueSB && b === 0) dotColor = '#EA580C';
          else if (!isSB && rogueNB && b === 12) dotColor = '#EA580C';

          routeBusHtml += `<circle cx="${{(pt.x + xOff).toFixed(1)}}" cy="${{(pt.y + yOff).toFixed(1)}}" r="3.8" fill="${{dotColor}}" stroke="#111215" stroke-width="1.2" />`;
        }}

        // Queued Stack SB (Orange / Blue)
        if (chokeDistSB >= 0 && (maxQueueSB > 0 || rogueSB)) {{
          const qCount = Math.min(6, Math.max(rogueSB ? 2 : 1, Math.ceil(maxQueueSB / 4)));
          for (let q = 1; q <= qCount; q++) {{
            const qDist = Math.max(0, chokeDistSB - (q * 7));
            const qPt = pathEl.getPointAtLength(qDist);
            const dotColor = rogueSB && q === 1 ? '#EA580C' : '#F97316';
            routeBusHtml += `<circle cx="${{(qPt.x - 1.5).toFixed(1)}}" cy="${{(qPt.y - 1.5).toFixed(1)}}" r="4.5" fill="${{dotColor}}" stroke="#FFFFFF" stroke-width="1.4">
                               <animate attributeName="opacity" values="0.7;1;0.7" dur="1.5s" repeatCount="indefinite" />
                             </circle>`;
          }}
        }}

        // Queued Stack NB (Orange / Green)
        if (chokeDistNB >= 0 && (maxQueueNB > 0 || rogueNB)) {{
          const qCount = Math.min(6, Math.max(rogueNB ? 2 : 1, Math.ceil(maxQueueNB / 4)));
          for (let q = 1; q <= qCount; q++) {{
            const qDist = Math.min(totalLen, chokeDistNB + (q * 7));
            const qPt = pathEl.getPointAtLength(qDist);
            const dotColor = rogueNB && q === 1 ? '#EA580C' : '#10B981';
            routeBusHtml += `<circle cx="${{(qPt.x + 1.5).toFixed(1)}}" cy="${{(qPt.y + 1.5).toFixed(1)}}" r="4.5" fill="${{dotColor}}" stroke="#FFFFFF" stroke-width="1.4">
                               <animate attributeName="opacity" values="0.7;1;0.7" dur="1.5s" repeatCount="indefinite" />
                             </circle>`;
          }}
        }}

        busLayer.innerHTML = routeBusHtml;
      }}
    }}

    function switchPreset(key) {{
      pause();
      activePreset = key;

      const preset = presets[key];
      snapshots = preset.snapshots;
      metadata = preset.meta;

      document.getElementById('btn-time-label').innerText = `${{snapshots[0].time_str}} – ${{snapshots[snapshots.length - 1].time_str}}`;
      document.getElementById('time-slider').max = snapshots.length - 1;
      document.getElementById('time-slider').value = 0;
      currentIndex = 0;
      drawPaxChart();
      renderSnapshot(0);
    }}

    function onSlide(val) {{
      pause();
      currentIndex = parseInt(val);
      renderSnapshot(currentIndex);
    }}

    function togglePlay() {{
      if (isPlaying) pause();
      else play();
    }}

    function play() {{
      isPlaying = true;
      document.getElementById('btn-play').innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="4" width="4" height="16"/><rect x="15" y="4" width="4" height="16"/></svg>';
      playInterval = setInterval(() => {{
        if (currentIndex < snapshots.length - 1) {{
          currentIndex++;
          renderSnapshot(currentIndex);
        }} else {{
          pause();
        }}
      }}, 500 / playSpeed);
    }}

    function pause() {{
      isPlaying = false;
      document.getElementById('btn-play').innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="6,4 20,12 6,20"/></svg>';
      if (playInterval) clearInterval(playInterval);
    }}

    function toggleSpeed() {{
      playSpeed = (playSpeed === 1) ? 2 : ((playSpeed === 2) ? 4 : 1);
      document.getElementById('btn-speed').innerText = playSpeed + "x";
      if (isPlaying) {{ pause(); play(); }}
    }}

    function openModal() {{
      document.getElementById('sim-modal').style.display = 'flex';
    }}

    function closeModal() {{
      document.getElementById('sim-modal').style.display = 'none';
    }}

    function showLoading() {{
      const overlay = document.getElementById('loading-overlay');
      overlay.style.display = 'flex';
      overlay.style.opacity = '1';
      
      const bar = document.getElementById('loading-progress-bar');
      const stepText = document.getElementById('loading-step-text');
      const stageLabel = document.getElementById('loading-stage-label');
      
      bar.style.width = '8%';
      stepText.innerText = "Initializing SimPy transit engine & calibrated 24 stations...";
      stageLabel.innerText = "Step 1 of 4: Calibrating 24 Stations";

      let progress = 8;
      const stages = [
        {{ at: 25, text: "Simulating 24 station queues, passenger boarding, and TCQSM crowding friction...", stage: "Step 2 of 4: Processing Stations" }},
        {{ at: 55, text: "Simulating randomized rogue actors lingering to fill up & queue propagation...", stage: "Step 3 of 4: Evaluating Rogue Dwell" }},
        {{ at: 80, text: "Compiling trajectory snapshots and headway reliability metrics...", stage: "Step 4 of 4: Compiling Snapshots" }}
      ];

      if (progressTimer) clearInterval(progressTimer);
      let stageIdx = 0;
      progressTimer = setInterval(() => {{
        if (progress < 90) {{
          progress += (90 - progress) * 0.08 + 1;
          bar.style.width = `${{Math.min(90, Math.round(progress))}}%`;
          
          if (stageIdx < stages.length && progress >= stages[stageIdx].at) {{
            stepText.innerText = stages[stageIdx].text;
            stageLabel.innerText = stages[stageIdx].stage;
            stageIdx++;
          }}
        }}
      }}, 250);
    }}

    function hideLoading(success = true) {{
      if (progressTimer) clearInterval(progressTimer);
      const bar = document.getElementById('loading-progress-bar');
      const stepText = document.getElementById('loading-step-text');
      const stageLabel = document.getElementById('loading-stage-label');
      
      if (success) {{
        bar.style.width = '100%';
        stepText.innerText = "Simulation complete! Updating 24-station corridor...";
        stageLabel.innerText = "Ready";
      }}

      setTimeout(() => {{
        const overlay = document.getElementById('loading-overlay');
        overlay.style.opacity = '0';
        setTimeout(() => {{
          overlay.style.display = 'none';
        }}, 300);
      }}, 400);
    }}

    function runDirectSimulation() {{
      executeCustomSimulation();
    }}

    async function executeCustomSimulation() {{
      closeModal();
      showLoading();

      const payload = {{
        start_hour: parseFloat(document.getElementById('inp-start').value),
        end_hour: parseFloat(document.getElementById('inp-end').value),
        fleet_size: parseInt(document.getElementById('inp-fleet').value),
        dispatch_interval: parseFloat(document.getElementById('inp-headway').value),
        bus_capacity: parseInt(document.getElementById('inp-cap').value),
        rogue_probability: parseFloat(document.getElementById('inp-rogue').value),
        step_minutes: 2.0
      }};

      const apiUrl = (window.location.protocol === 'file:') ? 'http://127.0.0.1:8000/api/simulate' : '/api/simulate';
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 25000);

      try {{
        const resp = await fetch(apiUrl, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload),
          signal: controller.signal
        }});
        clearTimeout(timeoutId);

        if (!resp.ok) throw new Error("HTTP " + resp.status);
        const data = await resp.json();

        if (data.status === 'success' && data.snapshots && data.snapshots.length > 0) {{
          hideLoading(true);
          snapshots = data.snapshots;
          metadata = data.meta;
          
          document.getElementById('btn-time-label').innerText = `${{snapshots[0].time_str}} – ${{snapshots[snapshots.length-1].time_str}}`;
          document.getElementById('time-slider').max = snapshots.length - 1;
          document.getElementById('time-slider').value = 0;
          currentIndex = 0;
          drawPaxChart();
          renderSnapshot(0);
          play();
          return;
        }} else {{
          throw new Error("Invalid simulation payload");
        }}
      }} catch (err) {{
        clearTimeout(timeoutId);
        console.warn("Live API unavailable or timed out; activating closest preset:", err);
        hideLoading(true);
        let targetPreset = 'am_peak';
        if (payload.start_hour >= 16) targetPreset = 'pm_peak';
        else if (payload.start_hour >= 11) targetPreset = 'midday_peak';
        switchPreset(targetPreset);
        play();
      }}
    }}

    // Zoom and Pan Handlers (Mouse Wheel + Click & Drag + Touch)
    function initMapZoomPan() {{
      const container = document.getElementById('map-container-el');
      if (!container) return;

      // Mouse Wheel Zoom
      container.addEventListener('wheel', (e) => {{
        e.preventDefault();
        const cam = mapCameras[currentVisualMode];
        const factor = e.deltaY < 0 ? 1.15 : (1 / 1.15);
        const newScale = Math.min(4.5, Math.max(0.6, cam.scale * factor));
        cam.scale = Math.round(newScale * 100) / 100;
        applyCamera();
      }}, {{ passive: false }});

      // Mouse Drag Panning
      let isDragging = false;
      let startX = 0;
      let startY = 0;
      let startCamX = 0;
      let startCamY = 0;

      container.addEventListener('mousedown', (e) => {{
        if (e.target.closest('.map-zoom-controls') || e.target.closest('#map-tooltip')) return;
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        const cam = mapCameras[currentVisualMode];
        startCamX = cam.x;
        startCamY = cam.y;
        container.style.cursor = 'grabbing';
      }});

      window.addEventListener('mousemove', (e) => {{
        if (!isDragging) return;
        const cam = mapCameras[currentVisualMode];
        const dx = (e.clientX - startX) * (1 / cam.scale);
        const dy = (e.clientY - startY) * (1 / cam.scale);
        cam.x = startCamX + dx;
        cam.y = startCamY + dy;
        applyCamera();
      }});

      window.addEventListener('mouseup', () => {{
        if (isDragging) {{
          isDragging = false;
          container.style.cursor = 'grab';
        }}
      }});

      // Touch Support
      let touchStartX = 0;
      let touchStartY = 0;
      container.addEventListener('touchstart', (e) => {{
        if (e.touches.length === 1) {{
          touchStartX = e.touches[0].clientX;
          touchStartY = e.touches[0].clientY;
          const cam = mapCameras[currentVisualMode];
          startCamX = cam.x;
          startCamY = cam.y;
        }}
      }}, {{ passive: true }});

      container.addEventListener('touchmove', (e) => {{
        if (e.touches.length === 1) {{
          const cam = mapCameras[currentVisualMode];
          const dx = (e.touches[0].clientX - touchStartX) * (1 / cam.scale);
          const dy = (e.touches[0].clientY - touchStartY) * (1 / cam.scale);
          cam.x = startCamX + dx;
          cam.y = startCamY + dy;
          applyCamera();
        }}
      }}, {{ passive: true }});

      // Initialize camera view
      applyCamera();
    }}

    // Export Full Telemetric Dataset for Extended Transit & Circulation Analysis
    function exportSimulationData() {{
      const totalSnaps = snapshots ? snapshots.length : 0;
      let maxPaxWaiting = 0;
      let maxPaxTime = '';
      let maxBusesQueuing = 0;
      let maxBusesTime = '';
      let maxStationDelay = 0;
      let maxDelayStation = '';
      let maxDelayTime = '';

      // Compute aggregate station statistics
      const stationStats = {{}};
      stationDefs.forEach(s => {{
        stationStats[s.name] = {{
          name: s.name,
          platform: s.platform,
          berths: s.berths,
          is_terminal: !!s.is_terminal,
          is_hotspot: !!s.is_hotspot,
          peak_pax_queue: 0,
          peak_buses_queuing: 0,
          peak_delay_min: 0,
          rogue_lingering_incidents: 0,
          sum_pax_queue: 0,
          samples: 0
        }};
      }});

      if (snapshots) {{
        snapshots.forEach(sn => {{
          if (sn.total_pax_waiting > maxPaxWaiting) {{
            maxPaxWaiting = sn.total_pax_waiting;
            maxPaxTime = sn.time_str;
          }}
          if (sn.total_buses_queuing > maxBusesQueuing) {{
            maxBusesQueuing = sn.total_buses_queuing;
            maxBusesTime = sn.time_str;
          }}
          if (sn.stations) {{
            Object.keys(sn.stations).forEach(stName => {{
              const stSnap = sn.stations[stName];
              const stat = stationStats[stName];
              if (stat) {{
                stat.samples++;
                stat.sum_pax_queue += (stSnap.pax_q_total || 0);
                if ((stSnap.pax_q_total || 0) > stat.peak_pax_queue) {{
                  stat.peak_pax_queue = stSnap.pax_q_total;
                }}
                if ((stSnap.buses_queuing || 0) > stat.peak_buses_queuing) {{
                  stat.peak_buses_queuing = stSnap.buses_queuing;
                }}
                if ((stSnap.avg_delay_min || 0) > stat.peak_delay_min) {{
                  stat.peak_delay_min = stSnap.avg_delay_min;
                }}
                if (stSnap.has_rogue_bus) {{
                  stat.rogue_lingering_incidents++;
                }}
              }}
              if ((stSnap.avg_delay_min || 0) > maxStationDelay) {{
                maxStationDelay = stSnap.avg_delay_min;
                maxDelayStation = stName;
                maxDelayTime = sn.time_str;
              }}
            }});
          }}
        }});
      }}

      // Calculate averages
      Object.values(stationStats).forEach(stat => {{
        stat.avg_pax_queue = stat.samples > 0 ? Math.round((stat.sum_pax_queue / stat.samples) * 10) / 10 : 0;
        delete stat.sum_pax_queue;
      }});

      const exportPayload = {{
        system: "EDSA Busway Bus Rapid Transit System Simulation",
        generator: "EDSA CarouselSim Multi-Berth Circulation Engine",
        export_timestamp_iso: new Date().toISOString(),
        simulation_configuration: {{
          active_preset: activePreset,
          observation_window: metadata?.label || 'Custom Window',
          start_hour: metadata?.start_hour ?? 8.0,
          end_hour: metadata?.end_hour ?? 11.0,
          active_fleet_buses: metadata?.fleet ?? 100,
          dispatch_headway_seconds: metadata?.headway ?? 120,
          bus_rated_capacity_pax: metadata?.capacity ?? 60,
          rogue_lingering_probability: metadata?.rogue_prob ?? 0.10
        }},
        corridor_telemetry_summary: {{
          total_stations: stationDefs.length,
          total_observation_slices: totalSnaps,
          peak_corridor_waiting_pax: maxPaxWaiting,
          peak_pax_timestamp: maxPaxTime,
          peak_buses_queuing: maxBusesQueuing,
          peak_buses_timestamp: maxBusesTime,
          max_station_delay_min: maxStationDelay,
          max_delayed_station: maxDelayStation,
          max_delay_timestamp: maxDelayTime
        }},
        stations_summary: Object.values(stationStats),
        telemetry_snapshots: snapshots
      }};

      const jsonStr = JSON.stringify(exportPayload, null, 2);
      const blob = new Blob([jsonStr], {{ type: 'application/json' }});
      const url = URL.createObjectURL(blob);
      const downloadLink = document.createElement('a');
      downloadLink.href = url;
      const safePreset = (activePreset || 'telemetry').replace(/[^a-z0-9_-]/gi, '_');
      const timeTag = new Date().toISOString().replace(/[:.]/g, '-');
      downloadLink.download = `edsa_carousel_telemetry_${{safePreset}}_${{timeTag}}.json`;
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
      URL.revokeObjectURL(url);
    }}

    // Global Escape Key Listener for Modals
    window.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape') {{
        closeDemandModal();
        closeModal();
      }}
    }});

    // Initial load
    initVariableTooltips();
    initStationDots();
    initChecklist();
    drawPaxChart();
    renderSnapshot(0);
    initMapZoomPan();
  </script>
</body>
</html>
"""
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    logger.info("Successfully generated dual-rotation rogue actor dashboard at %s", out_file)


if __name__ == "__main__":
    main()
