#!/usr/bin/env python3
"""Main execution script for the EDSA Carousel Busway Simulation.

Runs a full 24-hour simulation cycle and produces:
- Executive summary metrics report (console)
- Interactive edsa_simulation_map.html map
- Visualization charts (PNG)
"""

import sys
import os

# Add parent directory to sys.path so edsa_carousel_sim can be imported directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import logging
import argparse
from pathlib import Path

from edsa_carousel_sim.config import get_default_config, SimulationConfig
from edsa_carousel_sim.osm_network import build_network
from edsa_carousel_sim.engine import run_simulation
from edsa_carousel_sim.metrics import compute_metrics, print_executive_summary
from edsa_carousel_sim.visualize import generate_all_visualizations, plot_route_schematic

def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the simulation."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def main() -> None:
    """Main execution function."""
    parser = argparse.ArgumentParser(description="EDSA Carousel Busway Simulation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--duration", type=float, default=24.0, help="Simulation duration in hours (default: 24.0)")
    parser.add_argument("--fleet-size", type=int, default=100, help="Fleet size (default: 100)")
    parser.add_argument("--dispatch-interval", type=float, default=120, help="Dispatch interval in seconds (default: 120)")
    parser.add_argument("--output-dir", type=str, default=".", help="Output directory for results (default: current directory)")
    parser.add_argument("--osm-xml", type=str, default=None, help="Path to local OSM XML file (.osm/.xml) for 100% offline network graph")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--no-viz", action="store_true", help="Skip visualization generation")
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    start_time_total = time.time()
    
    try:
        # Load default config and override with CLI args
        config = get_default_config()
        config.random_seed = args.seed
        config.simulation_duration_hours = args.duration
        config.fleet.fleet_size = args.fleet_size
        config.fleet.dispatch_interval_seconds = args.dispatch_interval
        if args.osm_xml:
            config.network.osm_xml_path = args.osm_xml
        
        # Ensure output directory exists
        out_dir = Path(args.output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        
        print("==================================================")
        print("       EDSA Carousel Busway Simulation            ")
        print("==================================================")
        print(f"Simulation Duration : {config.simulation_duration_hours} hours")
        print(f"Random Seed         : {config.random_seed}")
        print(f"Fleet Size          : {config.fleet.fleet_size} buses")
        print(f"Dispatch Interval   : {config.fleet.dispatch_interval_seconds} seconds")
        print(f"Output Directory    : {out_dir.absolute()}")
        print("==================================================\n")
        
        # Build OSM network
        logger.info("Building OSM network...")
        t0 = time.time()
        network = build_network(config)
        t1 = time.time()
        logger.info(f"Network built in {t1 - t0:.2f} seconds.")
        
        # Run simulation
        logger.info("Running simulation...")
        t0 = time.time()
        sim_state = run_simulation(config, network)
        t1 = time.time()
        logger.info(f"Simulation completed in {t1 - t0:.2f} seconds.")
        
        # Compute metrics
        logger.info("Computing metrics...")
        metrics = compute_metrics(sim_state)
        
        # Print executive summary
        print("\n--- Executive Summary ---")
        print_executive_summary(metrics)
        
        # Generate visualizations
        if not args.no_viz:
            logger.info("Generating visualizations...")
            t0 = time.time()
            generate_all_visualizations(sim_state, network, metrics, output_dir=str(out_dir))
            t1 = time.time()
            logger.info(f"Visualizations generated in {t1 - t0:.2f} seconds.")
        else:
            logger.info("Skipping visualizations generation (--no-viz passed).")
            
        end_time_total = time.time()
        total_time = end_time_total - start_time_total
        logger.info(f"All tasks completed successfully in {total_time:.2f} seconds.")
        
    except Exception as e:
        logger.error(f"Simulation failed with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
