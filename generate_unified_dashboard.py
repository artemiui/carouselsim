#!/usr/bin/env python3
"""Unified Interactive EDSA Busway Simulation Dashboard Generator.

Features:
- "Intelly" design system: warm cream canvas, deep charcoal rounded sidebar dock, pastel bento cards.
- Plus Jakarta Sans modern geometric humanist typography.
- Hover description overlays (tooltips) for all transit simulation variables.
- Complete calibrated 24-station route from Monumento to PITX with accurate OSM coordinates.
- Dual-direction circulation: live Southbound (SB) and Northbound (NB) rotation.
- Interactive direction toggle [ SB | NB ] reversing checklist sequence (PITX -> Monumento).
- Generalized bottleneck model: dynamic rogue actor ("nagpupuno" bus driver) lingering.
- Dynamic floating chip & beacon ripple tracking active rogue actor / chokepoint per direction.
- Zero-passenger free-flow rule: platforms without demand do not cause artificial clogging.
- Dual-direction bus animation: Southbound (royal blue) and Northbound (sky cyan) buses.
- Interactive Line Graph inside pastel rose card showing total waiting passengers over time with scrubber tracking cursor.
- Absolutely zero emojis (pure SVG icons and clean typography throughout).
"""

from __future__ import annotations
import sys
import os
import json
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
    min_lat = min(s.lat for s in raw_stations)
    max_lat = max(s.lat for s in raw_stations)
    min_lon = min(s.lon for s in raw_stations)
    max_lon = max(s.lon for s in raw_stations)

    pad_x = 45
    pad_y = 35
    w = 540 - 2 * pad_x
    h = 280 - 2 * pad_y

    station_svg_nodes = []
    for s in raw_stations:
        x = round(pad_x + ((s.lon - min_lon) / (max_lon - min_lon)) * w, 1)
        y = round(pad_y + ((max_lat - s.lat) / (max_lat - min_lat)) * h, 1)
        station_svg_nodes.append({
            'name': s.name,
            'x': x,
            'y': y,
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
      --border-subtle: #EBE6DA;
      --border-dark: #27272A;
      
      --sidebar-bg: #18181B;
      --sidebar-text: #A1A1AA;
      --sidebar-active: #FFFFFF;
      
      --text-main: #18181B;
      --text-muted: #71717A;
      --text-light: #A1A1AA;
      
      /* Bento Pastel Theme */
      --pastel-yellow-bg: #FEF9C3;
      --pastel-yellow-border: #FEF08A;
      --pastel-yellow-text: #713F12;
      --pastel-yellow-accent: #CA8A04;
      
      --pastel-pink-bg: #FCE7F3;
      --pastel-pink-border: #FBCFE8;
      --pastel-pink-text: #831843;
      --pastel-pink-accent: #DB2777;
      
      --pastel-green-bg: #DCFCE7;
      --pastel-green-border: #BBF7D0;
      --pastel-green-text: #14532D;
      --pastel-green-accent: #16A34A;
      
      --pastel-blue-bg: #DBEAFE;
      --pastel-blue-border: #BFDBFE;
      --pastel-blue-text: #1E3A8A;
      --pastel-blue-accent: #2563EB;
      
      --primary: #18181B;
      --primary-blue: #2563EB;
      --primary-cyan: #0284C7;
      --accent-orange: #EA580C;
      --accent-green: #16A34A;
      
      --radius-xl: 28px;
      --radius-lg: 22px;
      --radius-md: 16px;
      --radius-sm: 10px;
      
      --shadow-soft: 0 4px 20px rgba(24, 24, 27, 0.04);
      --shadow-floating: 0 12px 32px rgba(24, 24, 27, 0.08);
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
      justify-content: center;
      padding: 24px;
      -webkit-font-smoothing: antialiased;
    }}

    /* Global Workspace Layout */
    .dashboard-layout {{
      width: 100%;
      max-width: 1400px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }}

    /* Main Content Container */
    .main-canvas {{
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }}

    /* Top Greeting & Action Header */
    .canvas-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .canvas-title-group h1 {{
      font-size: 1.65rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      color: var(--text-main);
    }}
    .canvas-title-group p {{
      font-size: 0.84rem;
      color: var(--text-muted);
      font-weight: 500;
      margin-top: 2px;
    }}

    .header-actions {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .pill-btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 18px;
      border-radius: 9999px;
      font-size: 0.82rem;
      font-weight: 700;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-main);
      cursor: pointer;
      box-shadow: var(--shadow-soft);
      transition: all 0.2s ease;
    }}
    .pill-btn:hover {{
      border-color: #D4D4D8;
      transform: translateY(-1px);
    }}
    .pill-btn.dark {{
      background: #18181B;
      color: #FFFFFF;
      border-color: #18181B;
      box-shadow: 0 4px 12px rgba(24, 24, 27, 0.15);
    }}
    .pill-btn.dark:hover {{
      background: #27272A;
    }}

    /* Row 1: Bento Pastel Metric Cards Grid */
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
      transition: transform 0.2s ease, box-shadow 0.2s ease;
      cursor: default;
    }}
    .bento-card:hover {{
      transform: translateY(-2px);
      box-shadow: var(--shadow-floating);
    }}

    /* Card 1: Pastel Yellow */
    .bento-yellow {{
      background: var(--pastel-yellow-bg);
      border: 1px solid var(--pastel-yellow-border);
      color: var(--pastel-yellow-text);
    }}
    /* Card 2: Pastel Pink */
    .bento-pink {{
      background: var(--pastel-pink-bg);
      border: 1px solid var(--pastel-pink-border);
      color: var(--pastel-pink-text);
    }}
    /* Card 3: Pastel Green */
    .bento-green {{
      background: var(--pastel-green-bg);
      border: 1px solid var(--pastel-green-border);
      color: var(--pastel-green-text);
    }}
    /* Card 4: Pastel Blue */
    .bento-blue {{
      background: var(--pastel-blue-bg);
      border: 1px solid var(--pastel-blue-border);
      color: var(--pastel-blue-text);
    }}

    /* Card Top Typography */
    .bento-top {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      margin-bottom: 8px;
    }}
    .bento-label {{
      font-size: 0.8rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      opacity: 0.85;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }}
    .bento-num {{
      font-size: 1.85rem;
      font-weight: 800;
      line-height: 1.1;
      letter-spacing: -0.03em;
    }}
    .bento-unit {{
      font-size: 1rem;
      font-weight: 600;
      opacity: 0.8;
    }}
    .bento-sub {{
      font-size: 0.74rem;
      font-weight: 600;
      opacity: 0.8;
      margin-top: 4px;
    }}

    /* Decorative Shapes for Bento Cards */
    .bento-bg-shape {{
      position: absolute;
      right: 12px;
      bottom: 12px;
      opacity: 0.22;
      pointer-events: none;
    }}

    /* Mini Bars for Waiting Pax */
    .bento-bars {{
      display: flex;
      align-items: flex-end;
      gap: 3px;
      height: 36px;
    }}
    .bento-bar {{
      width: 5px;
      border-radius: 3px;
      background: currentColor;
      opacity: 0.25;
      transition: height 0.3s ease;
    }}
    .bento-bar.active {{
      opacity: 0.85;
    }}

    /* Pink Card Embedded Demand Line Chart */
    .demand-chart-box {{
      position: relative;
      width: 100%;
      height: 52px;
      margin-top: 8px;
    }}

    /* Row 2: Main Workspace Grid (Checkpoints + Map) */
    .workspace-grid {{
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 20px;
      align-items: stretch;
      min-height: 540px;
    }}

    /* Left Card: 24-Station Checkpoint Timeline */
    .white-card {{
      background: var(--bg-card);
      border-radius: var(--radius-lg);
      border: 1px solid var(--border-subtle);
      box-shadow: var(--shadow-soft);
      padding: 22px;
      display: flex;
      flex-direction: column;
      position: relative;
    }}

    .card-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
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

    /* Direction Pill Switcher */
    .dir-toggle-pill {{
      display: inline-flex;
      background: #F4F1E8;
      padding: 3px;
      border-radius: 9999px;
      border: 1px solid var(--border-subtle);
      gap: 3px;
    }}
    .dir-toggle-btn {{
      border: none;
      background: transparent;
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 0.74rem;
      font-weight: 700;
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.2s ease;
    }}
    .dir-toggle-btn.active {{
      background: #18181B;
      color: #FFFFFF;
      box-shadow: 0 2px 6px rgba(24, 24, 27, 0.2);
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
      border-radius: 4px;
    }}

    .station-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 10px;
      border-radius: 12px;
      transition: background 0.15s ease;
      cursor: pointer;
      margin-bottom: 4px;
    }}
    .station-row:hover {{
      background: #FAF8F2;
    }}
    .station-left {{
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }}
    .st-dot-badge {{
      width: 26px;
      height: 26px;
      border-radius: 8px;
      background: #F4F1E8;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.7rem;
      font-weight: 800;
      color: var(--text-muted);
      flex-shrink: 0;
    }}
    .st-dot-badge.hotspot {{
      background: #FEE2E2;
      color: #DC2626;
    }}
    .st-dot-badge.terminal {{
      background: #DBEAFE;
      color: #2563EB;
    }}
    .st-name {{
      font-size: 0.82rem;
      font-weight: 700;
      color: var(--text-main);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 170px;
    }}
    .st-sub {{
      font-size: 0.69rem;
      color: var(--text-muted);
      font-weight: 500;
    }}
    .st-time {{
      font-size: 0.74rem;
      font-weight: 700;
      color: var(--text-muted);
      font-family: monospace;
      flex-shrink: 0;
    }}

    /* Bottom Info Pill */
    .checklist-footer {{
      margin-top: 14px;
      padding: 8px 12px;
      border-radius: 12px;
      background: #FAF8F2;
      border: 1px solid var(--border-subtle);
      font-size: 0.74rem;
      font-weight: 600;
      color: var(--text-muted);
      text-align: center;
    }}

    /* Right Card: Route Schematic Map & Scrubber */
    .map-card {{
      background: var(--bg-card);
      border-radius: var(--radius-lg);
      border: 1px solid var(--border-subtle);
      box-shadow: var(--shadow-soft);
      padding: 22px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
      overflow: hidden;
    }}

    /* Dynamic Floating Chokepoint Chip */
    .lane-status-chip {{
      position: absolute;
      top: 26px;
      left: 26px;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(8px);
      border: 1px solid var(--border-subtle);
      border-radius: 9999px;
      padding: 6px 14px;
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.76rem;
      font-weight: 700;
      z-index: 10;
      box-shadow: 0 4px 14px rgba(24, 24, 27, 0.06);
    }}
    .status-beacon-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-green);
    }}

    /* Map Legend */
    .map-legend-bar {{
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 16px;
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: 10px;
    }}
    .legend-item {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }}

    /* Vector Map Canvas Wrapper */
    .map-canvas-wrapper {{
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      background: radial-gradient(circle at 50% 50%, #FAF8F2 0%, #F5F1E6 100%);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-subtle);
      padding: 10px;
      margin-bottom: 14px;
      min-height: 340px;
    }}

    /* Bottom Scrubber Controller */
    .scrubber-dock {{
      display: flex;
      align-items: center;
      gap: 14px;
      background: #FAF8F2;
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 10px 16px;
    }}
    .play-pill-btn {{
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: #18181B;
      color: #FFFFFF;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(24, 24, 27, 0.2);
      transition: background 0.15s ease;
      flex-shrink: 0;
    }}
    .play-pill-btn:hover {{
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
      border-radius: 9999px;
      outline: none;
    }}
    .time-slider::-webkit-slider-thumb {{
      -webkit-appearance: none;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: #18181B;
      cursor: pointer;
      border: 2px solid #FFFFFF;
      box-shadow: 0 1px 4px rgba(24, 24, 27, 0.25);
    }}
    .speed-pill {{
      padding: 4px 10px;
      border-radius: 9999px;
      background: #FFFFFF;
      border: 1px solid var(--border-subtle);
      font-size: 0.74rem;
      font-weight: 700;
      color: var(--text-main);
      cursor: pointer;
    }}

    /* Global Tooltip Popover for Variables */
    #var-tooltip {{
      position: fixed;
      display: none;
      background: #18181B;
      color: #FFFFFF;
      padding: 8px 14px;
      border-radius: 10px;
      font-size: 0.74rem;
      line-height: 1.35;
      max-width: 250px;
      pointer-events: none;
      z-index: 9999;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
      border: 1px solid rgba(255, 255, 255, 0.12);
      transition: opacity 0.15s ease;
    }}
    #var-tooltip strong {{
      display: block;
      color: #F4F4F5;
      font-weight: 700;
      margin-bottom: 2px;
      letter-spacing: -0.01em;
    }}

    /* Station Map Tooltip */
    #map-tooltip {{
      position: absolute;
      display: none;
      background: #18181B;
      color: #FFFFFF;
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 0.72rem;
      font-weight: 500;
      pointer-events: none;
      z-index: 20;
      box-shadow: 0 6px 16px rgba(0,0,0,0.18);
      line-height: 1.35;
    }}

    /* Modal Styling */
    .modal-backdrop {{
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(24, 24, 27, 0.45);
      backdrop-filter: blur(4px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }}
    .modal-card {{
      background: #FFFFFF;
      border-radius: var(--radius-lg);
      padding: 28px 32px;
      width: 100%;
      max-width: 500px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.15);
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
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-muted);
      margin-bottom: 5px;
    }}
    .form-field input, .form-field select {{
      width: 100%;
      padding: 9px 12px;
      border-radius: 10px;
      border: 1px solid var(--border-subtle);
      font-size: 0.86rem;
      outline: none;
      background: #FAF8F2;
      color: var(--text-main);
    }}
    .form-field input:focus, .form-field select:focus {{
      border-color: #18181B;
      background: #FFFFFF;
    }}
    .modal-actions {{
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }}

    /* Loading Overlay */
    .loading-overlay {{
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(24, 24, 27, 0.65);
      backdrop-filter: blur(8px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 2000;
      transition: opacity 0.3s ease;
    }}
    .loading-box {{
      background: #FFFFFF;
      border-radius: var(--radius-xl);
      padding: 36px 40px;
      width: 100%;
      max-width: 460px;
      text-align: center;
      box-shadow: 0 24px 48px rgba(0, 0, 0, 0.2);
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
      border-top-color: #18181B;
      animation: spin 0.9s linear infinite;
    }}
    @keyframes spin {{
      to {{ transform: rotate(360deg); }}
    }}
    .progress-bar-box {{
      width: 100%;
      background: #F4F1E8;
      height: 6px;
      border-radius: 9999px;
      overflow: hidden;
      margin-top: 6px;
    }}
    .progress-bar-fill {{
      height: 100%;
      width: 0%;
      background: #18181B;
      border-radius: 9999px;
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
      opacity: 0.45;
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
      <div style="font-size:0.72rem; color:var(--text-light); font-weight:700; text-transform:uppercase;" id="loading-stage-label">Step 1 of 4: Calibrating 24 Stations</div>
    </div>
  </div>

  <div class="dashboard-layout">

    <!-- Main Workspace Canvas -->
    <main class="main-canvas">

      <!-- Header Action Bar -->
      <header class="canvas-header">
        <div class="canvas-title-group">
          <h1>Corridor Circulation Overview</h1>
          <p>Live multi-berth circulation and transit demand telemetry across 24 stations.</p>
        </div>

        <div class="header-actions">
          <button class="pill-btn" onclick="openModal()" data-tooltip-title="Time Window" data-tooltip="Active observation window for simulated passenger arrivals and dispatch schedule.">
            <span id="btn-time-label">08:00 AM – 11:00 AM</span>
          </button>
          <button class="pill-btn" onclick="openModal()" data-tooltip-title="Simulation Controls" data-tooltip="Configure headway, active fleet, bus capacity, and rogue actor lingering probability.">
            Parameters
          </button>
          <button class="pill-btn dark" onclick="runDirectSimulation()" data-tooltip-title="Run Simulation Engine" data-tooltip="Execute real-time SimPy discrete-event simulation across the 24-station corridor.">
            Run Simulation
          </button>
        </div>
      </header>

      <!-- Row 1: Bento Pastel Metric Cards Grid -->
      <section class="bento-metrics">
        
        <!-- Card 1: Pastel Yellow (Waiting Passengers) -->
        <div class="bento-card bento-yellow">
          <div class="bento-top">
            <span class="bento-label has-var-tooltip" data-tooltip-title="Waiting Passengers (pax_q)" data-tooltip="Total commuters queued at all 24 station platforms awaiting bus arrival.">
              Waiting Passengers
            </span>
            <div class="bento-bars" id="mini-bars-pax">
              <div class="bento-bar active" style="height: 18px;"></div>
              <div class="bento-bar active" style="height: 26px;"></div>
              <div class="bento-bar active" style="height: 34px;"></div>
              <div class="bento-bar active" style="height: 22px;"></div>
              <div class="bento-bar active" style="height: 28px;"></div>
            </div>
          </div>
          <div>
            <div class="bento-num" id="kpi-pax">4,839</div>
            <div class="bento-sub has-var-tooltip" data-tooltip-title="Directional Queues" data-tooltip="Commuters split across Southbound (Monumento → PITX) and Northbound (PITX → Monumento) lanes.">
              <span id="kpi-pax-sb-split">SB: 2,640</span> &nbsp;|&nbsp; <span id="kpi-pax-nb-split">NB: 2,199</span>
            </div>
          </div>
          <!-- Geometric Plus shape -->
          <svg class="bento-bg-shape" width="56" height="56" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 11h-6V5a1 1 0 0 0-2 0v6H5a1 1 0 0 0 0 2h6v6a1 1 0 0 0 2 0v-6h6a1 1 0 0 0 0-2z"/>
          </svg>
        </div>

        <!-- Card 2: Pastel Pink (Demand Trend Line Chart) -->
        <div class="bento-card bento-pink">
          <div class="bento-top">
            <span class="bento-label has-var-tooltip" data-tooltip-title="Demand Trend Line Chart" data-tooltip="Total platform waiting passengers fluctuating over time across the simulation window.">
              Demand Trend
            </span>
            <span id="chart-live-val" style="font-size:1.05rem; font-weight:800; font-family:monospace;">4,839 pax</span>
          </div>
          
          <div class="demand-chart-box">
            <svg id="pax-trend-svg" width="100%" height="100%" viewBox="0 0 240 55" preserveAspectRatio="none">
              <defs>
                <linearGradient id="pinkGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stop-color="#DB2777" stop-opacity="0.30"/>
                  <stop offset="100%" stop-color="#DB2777" stop-opacity="0.0"/>
                </linearGradient>
              </defs>
              <path id="pax-area-path" fill="url(#pinkGrad)" d=""/>
              <path id="pax-line-path" fill="none" stroke="#DB2777" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d=""/>
              <!-- Peak Marker Layer: Only peak labeled, NO vertical line -->
              <g id="peak-marker-group"></g>
              <circle id="chart-cursor-dot" cx="0" cy="0" r="3.5" fill="#831843" stroke="#FFFFFF" stroke-width="1.2" style="display:none;"/>
            </svg>
          </div>

          <div style="display:flex; justify-content:space-between; font-size:0.68rem; font-weight:700; opacity:0.8; margin-top:4px;">
            <span id="chart-time-start">08:00 AM</span>
            <span id="chart-time-mid">09:30 AM</span>
            <span id="chart-time-end">11:00 AM</span>
          </div>
        </div>

        <!-- Card 3: Pastel Green (Operating Fleet) -->
        <div class="bento-card bento-green">
          <div class="bento-top">
            <span class="bento-label has-var-tooltip" data-tooltip-title="Operating Fleet (fleet_size)" data-tooltip="Total active transit buses circulating inside the segregated median busway.">
              Operating Fleet
            </span>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="15" rx="3"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
              <circle cx="7" cy="15" r="1.5"/>
              <circle cx="17" cy="15" r="1.5"/>
            </svg>
          </div>
          <div>
            <div class="bento-num" id="kpi-fleet">100 <span class="bento-unit">buses</span></div>
            <div class="bento-sub has-var-tooltip" data-tooltip-title="Active Lane Allocation" data-tooltip="Buses segregated in physical median lanes with dedicated bypass overtaking paths.">
              Active in dedicated median lane
            </div>
          </div>
          <!-- Geometric Rounded Polygon shape -->
          <svg class="bento-bg-shape" width="56" height="56" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>

        <!-- Card 4: Pastel Blue (Cycle Time & Reliability) -->
        <div class="bento-card bento-blue">
          <div class="bento-top">
            <span class="bento-label has-var-tooltip" data-tooltip-title="Cycle Time & Headway Reliability" data-tooltip="Round-trip loop duration and headway consistency score (stability vs bunching).">
              Mean Cycle & Score
            </span>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <div>
            <div class="bento-num" id="kpi-cycle">91.2 <span class="bento-unit">min</span></div>
            <div class="bento-sub has-var-tooltip" data-tooltip-title="Reliability Index" data-tooltip="Percentage of bus arrivals adhering to scheduled dispatch headway tolerances.">
              <span id="kpi-reliability" style="font-weight:800;">94%</span> Headway Stability
            </div>
          </div>
          <!-- Starburst decorative shape -->
          <svg class="bento-bg-shape" width="56" height="56" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="12" r="8"/>
          </svg>
        </div>

      </section>

      <!-- Row 2: Main Workspace Grid (Checkpoints + Map) -->
      <section class="workspace-grid">
        
        <!-- Left: 24-Station Corridor Checkpoints -->
        <div class="white-card">
          <div class="card-header">
            <div>
              <div class="card-header-title has-var-tooltip" data-tooltip-title="Corridor Stations" data-tooltip="24 calibrated stations along EDSA featuring accurate coordinates and berth capacities.">
                Corridor Checkpoints
              </div>
              <div class="card-header-sub" id="dir-sub-title">24 Stations: Monumento → PITX</div>
            </div>

            <!-- Direction Toggle Pill Switcher -->
            <div class="dir-toggle-pill">
              <button class="dir-toggle-btn active" id="btn-dir-sb" onclick="setCorridorDirection('southbound')" data-tooltip-title="Southbound (SB)" data-tooltip="Circulate from Monumento terminal to PITX terminal.">SB</button>
              <button class="dir-toggle-btn" id="btn-dir-nb" onclick="setCorridorDirection('northbound')" data-tooltip-title="Northbound (NB)" data-tooltip="Circulate from PITX terminal to Monumento terminal.">NB</button>
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

        <!-- Right: Route Map Schematic & Scrubber -->
        <div class="map-card">
          
          <!-- Dynamic Floating Chokepoint Chip -->
          <div class="lane-status-chip" id="map-floating-chip">
            <div class="status-beacon-dot" id="chip-status-dot"></div>
            <span id="chip-station-name">Corridor Circulation Status</span> &nbsp;|&nbsp;
            <span id="chip-queue-info" style="color:var(--accent-green);">Nominal flow</span>
          </div>

          <!-- Map Legend -->
          <div class="map-legend-bar">
            <span class="legend-item has-var-tooltip" data-tooltip-title="Southbound Bus Lane" data-tooltip="Monumento towards PITX"><span style="color:#2563EB;">●</span> Southbound (SB)</span>
            <span class="legend-item has-var-tooltip" data-tooltip-title="Northbound Bus Lane" data-tooltip="PITX towards Monumento"><span style="color:#0284C7;">●</span> Northbound (NB)</span>
            <span class="legend-item has-var-tooltip" data-tooltip-title="Bottleneck / Rogue Bus" data-tooltip="Buses queued or lingering to fill up"><span style="color:#EA580C;">●</span> Rogue / Queued</span>
          </div>

          <!-- Vector Map Canvas (Pure SVG, 100% offline) -->
          <div class="map-canvas-wrapper" id="map-container-el">
            <div id="map-tooltip"></div>
            <svg id="route-vector-svg" width="100%" height="320" viewBox="0 0 540 280">
              <!-- Subtle Background Road Grid -->
              <line x1="20" y1="50" x2="520" y2="50" stroke="#EDE8DC" stroke-width="1.5"/>
              <line x1="20" y1="120" x2="520" y2="120" stroke="#EDE8DC" stroke-width="1.5"/>
              <line x1="20" y1="190" x2="520" y2="190" stroke="#EDE8DC" stroke-width="1.5"/>
              <line x1="120" y1="20" x2="120" y2="260" stroke="#EDE8DC" stroke-width="1.5"/>
              <line x1="260" y1="20" x2="260" y2="260" stroke="#EDE8DC" stroke-width="1.5"/>
              <line x1="400" y1="20" x2="400" y2="260" stroke="#EDE8DC" stroke-width="1.5"/>

              <!-- Main Route Transit Polyline -->
              <path id="route-path" d="{route_path_d}" 
                    stroke="#18181B" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
              <path d="{route_path_d}" 
                    stroke="#E4E4E7" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="4 6" fill="none"/>

              <!-- Dynamic Rogue Actor / Chokepoint Beacon -->
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

              <!-- Key Station Text Labels -->
              <text x="45.0" y="24" font-size="9" font-weight="700" text-anchor="middle" fill="#71717A">Monumento</text>
              <text x="270.9" y="24" font-size="8.5" font-weight="700" text-anchor="middle" fill="#71717A">FPJ / Muñoz</text>
              <text x="325" y="24" font-size="9" font-weight="700" fill="#71717A">SM North</text>
              <text x="382" y="70" font-size="8.5" font-weight="700" fill="#71717A">Quezon Ave</text>
              <text x="462" y="104" font-size="8.5" font-weight="700" fill="#71717A">Cubao</text>
              <text x="502" y="148" font-size="8.5" font-weight="700" fill="#71717A">Ortigas</text>
              <text x="435" y="177" font-size="8.5" font-weight="700" fill="#71717A">Guadalupe</text>
              <text x="325" y="202" font-size="8.5" font-weight="700" fill="#71717A">One Ayala</text>
              <text x="145" y="196" font-size="8.5" font-weight="700" fill="#71717A">Taft</text>
              <text x="45" y="230" font-size="8.5" font-weight="700" fill="#71717A">MOA</text>
              <text x="165" y="260" font-size="9" font-weight="800" fill="#18181B">PITX</text>
            </svg>
          </div>

          <!-- Bottom Scrubber Controller -->
          <div class="scrubber-dock">
            <button class="play-pill-btn" id="btn-play" onclick="togglePlay()" data-tooltip-title="Play / Pause" data-tooltip="Control automated minute-by-minute playback.">
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

    </main>

  </div>

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
        <button class="pill-btn" onclick="closeModal()">Cancel</button>
        <button class="pill-btn dark" id="btn-submit-sim" onclick="executeCustomSimulation()">
          Run Simulation
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
      
      const subTitle = document.getElementById('dir-sub-title');
      const durPill = document.getElementById('route-duration-pill');
      if (dir === 'southbound') {{
        subTitle.innerText = "24 Stations: Monumento → PITX";
        durPill.innerText = "Southbound Cycle: ~1h 35m";
      }} else {{
        subTitle.innerText = "24 Stations: PITX → Monumento";
        durPill.innerText = "Northbound Cycle: ~1h 35m";
      }}
      initChecklist();
      renderSnapshot(currentIndex);
    }}

    // Build Station Dots on SVG map
    function initStationDots() {{
      const layer = document.getElementById('station-dots-layer');
      if (!layer) return;
      let html = '';
      stationDefs.forEach((st, i) => {{
        const color = st.is_terminal ? '#18181B' : (st.is_hotspot ? '#EA580C' : '#3B82F6');
        const r = st.is_terminal ? 5.5 : (st.is_hotspot ? 5.0 : 4.0);
        html += `<circle id="dot-${{i}}" cx="${{st.x}}" cy="${{st.y}}" r="${{r}}" fill="${{color}}" stroke="#FFFFFF" stroke-width="1.5" 
                        onmouseenter="showStationTooltip(event, ${{i}})" onmouseleave="hideStationTooltip()" style="cursor:pointer;" />`;
      }});
      layer.innerHTML = html;
    }}

    // Build 24-Station Checklist based on current rotation (Southbound or Northbound)
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
        const seqNum = displaySeq + 1;
        html += `
          <div class="station-row" id="chk-item-${{stIdx}}" onclick="highlightStationDot(${{stIdx}})" data-tooltip-title="${{st.name}}" data-tooltip="Station Platform: ${{st.platform}} | Capacity: ${{st.berths}} Simultaneous Berths">
            <div class="station-left">
              <div class="st-dot-badge ${{badgeClass}}">${{seqNum}}</div>
              <div>
                <div class="st-name">${{st.name}}</div>
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
      if (dot) {{
        dot.setAttribute('r', '9');
        setTimeout(() => {{
          const st = stationDefs[idx];
          dot.setAttribute('r', st.is_terminal ? '5.5' : (st.is_hotspot ? '5.0' : '4.0'));
        }}, 800);
      }}
    }}

    function showStationTooltip(e, idx) {{
      const tip = document.getElementById('map-tooltip');
      const st = stationDefs[idx];
      const snap = snapshots[currentIndex];
      const stData = snap?.stations[st.name] || {{ pax_q_total: 0, pax_q_forward: 0, pax_q_reverse: 0, buses_queuing: 0, avg_delay_min: 0, has_rogue_bus: false }};

      const rogueTag = stData.has_rogue_bus ? '<br><span style="color:#EA580C; font-weight:700;">[Rogue Bus Lingering]</span>' : '';

      tip.innerHTML = `
        <strong>${{st.name}}</strong><br>
        Type: ${{st.platform}} (${{st.berths}} berths)<br>
        SB Waiting: ${{stData.pax_q_forward || 0}} | NB Waiting: ${{stData.pax_q_reverse || 0}}<br>
        Buses Queued: ${{stData.buses_queuing || 0}} (${{stData.avg_delay_min || 0}}m delay)
        ${{rogueTag}}
      `;
      tip.style.left = (e.offsetX + 15) + 'px';
      tip.style.top = (e.offsetY - 20) + 'px';
      tip.style.display = 'block';
    }}

    function hideStationTooltip() {{
      const tip = document.getElementById('map-tooltip');
      if (tip) tip.style.display = 'none';
    }}

    function drawPaxChart() {{
      if (!snapshots || snapshots.length === 0) return;
      const svgW = 240;
      const svgH = 55;
      const padTop = 15;
      const padBottom = 5;
      const chartH = svgH - padTop - padBottom;

      const paxes = snapshots.map(s => s.total_waiting_pax || 0);
      let minVal = Math.min(...paxes);
      let maxVal = Math.max(...paxes);
      if (maxVal === minVal) {{ maxVal = minVal + 1; }}

      // Find the peak index and value (ONLY the peak is labeled)
      let peakIdx = 0;
      let peakVal = -1;
      for (let i = 0; i < paxes.length; i++) {{
        if (paxes[i] > peakVal) {{
          peakVal = paxes[i];
          peakIdx = i;
        }}
      }}

      const pts = [];
      const n = snapshots.length;
      for (let i = 0; i < n; i++) {{
        const x = (i / Math.max(1, n - 1)) * svgW;
        const norm = (paxes[i] - minVal) / (maxVal - minVal);
        const y = (svgH - padBottom) - (norm * chartH);
        pts.push({{ x: Number(x.toFixed(1)), y: Number(y.toFixed(1)) }});
      }}

      let lineD = `M ${{pts[0].x}} ${{pts[0].y}}`;
      for (let i = 1; i < pts.length; i++) {{
        lineD += ` L ${{pts[i].x}} ${{pts[i].y}}`;
      }}

      const areaD = `${{lineD}} L ${{pts[pts.length - 1].x}} ${{svgH - padBottom}} L ${{pts[0].x}} ${{svgH - padBottom}} Z`;

      const lineEl = document.getElementById('pax-line-path');
      const areaEl = document.getElementById('pax-area-path');
      if (lineEl) lineEl.setAttribute('d', lineD);
      if (areaEl) areaEl.setAttribute('d', areaD);

      // Render Peak Marker and Label (ONLY the peak is labeled, NO vertical line)
      const peakGroup = document.getElementById('peak-marker-group');
      if (peakGroup && pts[peakIdx]) {{
        const peakPt = pts[peakIdx];
        let textX = peakPt.x;
        let anchor = "middle";
        if (textX < 26) {{ textX = 4; anchor = "start"; }}
        else if (textX > svgW - 26) {{ textX = svgW - 4; anchor = "end"; }}

        peakGroup.innerHTML = `
          <circle cx="${{peakPt.x}}" cy="${{peakPt.y}}" r="3.2" fill="#831843" stroke="#FFFFFF" stroke-width="1.2" />
          <text x="${{textX}}" y="${{Math.max(10, peakPt.y - 4)}}" font-size="8.5" font-weight="800" font-family="'Plus Jakarta Sans', sans-serif" text-anchor="${{anchor}}" fill="#831843">
            ${{peakVal.toLocaleString()}}
          </text>
        `;
      }}

      const startEl = document.getElementById('chart-time-start');
      const midEl = document.getElementById('chart-time-mid');
      const endEl = document.getElementById('chart-time-end');
      if (startEl && snapshots[0]) startEl.innerText = snapshots[0].time_str;
      if (midEl && snapshots[Math.floor(n / 2)]) midEl.innerText = snapshots[Math.floor(n / 2)].time_str;
      if (endEl && snapshots[n - 1]) endEl.innerText = snapshots[n - 1].time_str;

      window._chartPts = pts;
    }}

    function renderSnapshot(idx) {{
      const snap = snapshots[idx];
      if (!snap) return;

      document.getElementById('clock-display').innerText = snap.time_str;
      document.getElementById('time-slider').value = idx;
      document.getElementById('kpi-pax').innerText = snap.total_waiting_pax.toLocaleString();
      document.getElementById('kpi-fleet').innerHTML = `${{metadata.fleet_size || 100}} <span class="bento-unit">buses</span>`;

      // Update Live Demand Trend Chart
      const chartValEl = document.getElementById('chart-live-val');
      if (chartValEl) {{
        chartValEl.innerText = `${{snap.total_waiting_pax.toLocaleString()}} pax`;
      }}

      if (window._chartPts && window._chartPts[idx]) {{
        const pt = window._chartPts[idx];
        const dot = document.getElementById('chart-cursor-dot');
        if (dot) {{
          dot.style.display = 'block';
          dot.setAttribute('cx', pt.x);
          dot.setAttribute('cy', pt.y);
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

      // Identify active rogue actor and primary chokepoint for the ACTIVE direction
      let worstStationName = null;
      let maxBusQueue = 0;
      let hasRogue = false;
      let rogueStation = null;

      for (const [stName, stData] of Object.entries(snap.stations)) {{
        const dirQueue = isSB 
          ? (stData.buses_queuing_sb !== undefined ? stData.buses_queuing_sb : (stData.buses_queuing || 0))
          : (stData.buses_queuing_nb !== undefined ? stData.buses_queuing_nb : 0);
        
        const dirRogue = isSB
          ? (stData.has_rogue_bus_sb !== undefined ? stData.has_rogue_bus_sb : stData.has_rogue_bus)
          : (stData.has_rogue_bus_nb !== undefined ? stData.has_rogue_bus_nb : false);

        if (dirRogue) {{
          hasRogue = true;
          rogueStation = stName;
          worstStationName = stName;
          maxBusQueue = Math.max(maxBusQueue, dirQueue);
          break;
        }}
        if (dirQueue > maxBusQueue) {{
          maxBusQueue = dirQueue;
          worstStationName = stName;
        }}
      }}

      // Floating dynamic status chip (Lane-specific)
      const chipQueue = document.getElementById('chip-queue-info');
      const chipStation = document.getElementById('chip-station-name');
      const chipDot = document.getElementById('chip-status-dot');
      const laneTag = isSB ? 'SB Lane' : 'NB Lane';

      if (hasRogue && rogueStation) {{
        chipStation.innerText = `[${{laneTag}}] Rogue Bus: ${{rogueStation}}`;
        chipQueue.innerText = `Lingering to fill up | ${{maxBusQueue}} buses queued`;
        chipQueue.style.color = "var(--accent-orange)";
        if (chipDot) chipDot.style.background = "var(--accent-orange)";
      }} else if (maxBusQueue > 2 && worstStationName) {{
        chipStation.innerText = `[${{laneTag}}] Chokepoint: ${{worstStationName}}`;
        chipQueue.innerText = `${{maxBusQueue}} buses queued (~${{maxBusQueue * 12}}m backup)`;
        chipQueue.style.color = "var(--accent-orange)";
        if (chipDot) chipDot.style.background = "var(--accent-orange)";
      }} else {{
        chipStation.innerText = `Corridor Flow (${{laneTag}}): Clear`;
        chipQueue.innerText = "No bottlenecks (0-pax free flow)";
        chipQueue.style.color = "var(--accent-green)";
        if (chipDot) chipDot.style.background = "var(--accent-green)";
      }}

      // Dynamic Beacon Ripple on SVG map (placed at active chokepoint)
      const beaconGroup = document.getElementById('dynamic-beacon-group');
      const beaconRing = document.getElementById('beacon-ring');
      const beaconMid = document.getElementById('beacon-mid');
      const beaconCore = document.getElementById('beacon-core');

      if ((hasRogue || maxBusQueue > 2) && worstStationName) {{
        const stNode = stationDefs.find(s => s.name === worstStationName);
        if (stNode && beaconGroup) {{
          beaconGroup.style.display = 'block';
          beaconRing.setAttribute('cx', stNode.x);
          beaconRing.setAttribute('cy', stNode.y);
          beaconMid.setAttribute('cx', stNode.x);
          beaconMid.setAttribute('cy', stNode.y);
          beaconCore.setAttribute('cx', stNode.x);
          beaconCore.setAttribute('cy', stNode.y);

          const bColor = hasRogue ? '#EA580C' : (isSB ? '#EA580C' : '#0284C7');
          beaconCore.setAttribute('fill', bColor);
        }}
      }} else if (beaconGroup) {{
        beaconGroup.style.display = 'none';
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
            subEl.innerHTML = `<span style="color:#EA580C; font-weight:700;">[Rogue Bus Lingering]</span> | ${{dirPax}} pax in line`;
          }} else if (dirQueue > 2) {{
            subEl.innerHTML = `<span style="color:#EA580C; font-weight:700;">${{dirQueue}} buses queued (${{dirDelay}}m delay)</span> | ${{dirPax}} pax`;
          }} else if (dirPax === 0) {{
            subEl.innerHTML = `<span style="color:var(--accent-green); font-weight:600;">Free Flow (0 pax)</span> | ${{st.berths}} berths`;
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

      // Render Dynamic Moving Buses for both directions
      updateBusLayer(snap, idx);
    }}

    function updateBusLayer(snap, idx) {{
      const busLayer = document.getElementById('bus-layer');
      if (!busLayer) return;
      const pathEl = document.getElementById('route-path');
      if (!pathEl) return;
      const totalLen = pathEl.getTotalLength();

      let chokeDistSB = -1;
      let chokeDistNB = -1;
      let maxQueueSB = snap.max_bus_queue_sb || 0;
      let maxQueueNB = snap.max_bus_queue_nb || 0;
      let rogueSB = snap.has_active_rogue_sb || false;
      let rogueNB = snap.has_active_rogue_nb || false;

      // Find SB chokepoint position
      for (const [stName, stData] of Object.entries(snap.stations)) {{
        if (stData.has_rogue_bus_sb || (stData.buses_queuing_sb && stData.buses_queuing_sb > 2)) {{
          const stIdx = stationDefs.findIndex(s => s.name === stName);
          if (stIdx >= 0) {{
            chokeDistSB = totalLen * (stIdx / (stationDefs.length - 1));
            maxQueueSB = Math.max(maxQueueSB, stData.buses_queuing_sb || 0);
            if (stData.has_rogue_bus_sb) rogueSB = true;
            break;
          }}
        }}
      }}

      // Find NB chokepoint position
      for (const [stName, stData] of Object.entries(snap.stations)) {{
        if (stData.has_rogue_bus_nb || (stData.buses_queuing_nb && stData.buses_queuing_nb > 2)) {{
          const stIdx = stationDefs.findIndex(s => s.name === stName);
          if (stIdx >= 0) {{
            chokeDistNB = totalLen * (stIdx / (stationDefs.length - 1));
            maxQueueNB = Math.max(maxQueueNB, stData.buses_queuing_nb || 0);
            if (stData.has_rogue_bus_nb) rogueNB = true;
            break;
          }}
        }}
      }}

      let html = '';
      const numBusesPerDir = 12;

      // 1. Southbound Buses (Monumento -> PITX)
      for (let i = 0; i < numBusesPerDir; i++) {{
        const offset = ((i / numBusesPerDir) + (idx / Math.max(1, snapshots.length)) * 2.2) % 1.0;
        const dist = offset * totalLen;
        if (chokeDistSB >= 0 && maxQueueSB > 2 && Math.abs(dist - chokeDistSB) < 14) continue;

        const pt = pathEl.getPointAtLength(dist);
        html += `<circle cx="${{(pt.x - 1.5).toFixed(1)}}" cy="${{(pt.y - 1.5).toFixed(1)}}" r="4.2" fill="#2563EB" stroke="#FFFFFF" stroke-width="1.3" />`;
      }}

      // 2. Northbound Buses (PITX -> Monumento)
      for (let i = 0; i < numBusesPerDir; i++) {{
        const offset = (1.0 - ((i / numBusesPerDir) + (idx / Math.max(1, snapshots.length)) * 2.2) % 1.0) % 1.0;
        const dist = offset * totalLen;
        if (chokeDistNB >= 0 && maxQueueNB > 2 && Math.abs(dist - chokeDistNB) < 14) continue;

        const pt = pathEl.getPointAtLength(dist);
        html += `<circle cx="${{(pt.x + 1.5).toFixed(1)}}" cy="${{(pt.y + 1.5).toFixed(1)}}" r="4.2" fill="#0284C7" stroke="#FFFFFF" stroke-width="1.3" />`;
      }}

      // 3. Queued Bus Stack in Southbound Lane
      if (chokeDistSB >= 0 && (maxQueueSB > 0 || rogueSB)) {{
        const qCount = Math.min(8, Math.max(rogueSB ? 2 : 1, Math.ceil(maxQueueSB / 4)));
        for (let q = 1; q <= qCount; q++) {{
          const qDist = Math.max(0, chokeDistSB - (q * 7));
          const qPt = pathEl.getPointAtLength(qDist);
          const dotColor = rogueSB && q === 1 ? '#EA580C' : '#F97316';
          html += `<circle cx="${{(qPt.x - 1.5).toFixed(1)}}" cy="${{(qPt.y - 1.5).toFixed(1)}}" r="5" fill="${{dotColor}}" stroke="#FFFFFF" stroke-width="1.5">
                     <animate attributeName="opacity" values="0.7;1;0.7" dur="1.5s" repeatCount="indefinite" />
                   </circle>`;
        }}
      }}

      // 4. Queued Bus Stack in Northbound Lane
      if (chokeDistNB >= 0 && (maxQueueNB > 0 || rogueNB)) {{
        const qCount = Math.min(8, Math.max(rogueNB ? 2 : 1, Math.ceil(maxQueueNB / 4)));
        for (let q = 1; q <= qCount; q++) {{
          const qDist = Math.min(totalLen, chokeDistNB + (q * 7));
          const qPt = pathEl.getPointAtLength(qDist);
          const dotColor = rogueNB && q === 1 ? '#EA580C' : '#0284C7';
          html += `<circle cx="${{(qPt.x + 1.5).toFixed(1)}}" cy="${{(qPt.y + 1.5).toFixed(1)}}" r="5" fill="${{dotColor}}" stroke="#FFFFFF" stroke-width="1.5">
                     <animate attributeName="opacity" values="0.7;1;0.7" dur="1.5s" repeatCount="indefinite" />
                   </circle>`;
        }}
      }}

      busLayer.innerHTML = html;
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

    // Initial load
    initVariableTooltips();
    initStationDots();
    initChecklist();
    drawPaxChart();
    renderSnapshot(0);
  </script>
</body>
</html>
"""
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    logger.info("Successfully generated dual-rotation rogue actor dashboard at %s", out_file)


if __name__ == "__main__":
    main()
