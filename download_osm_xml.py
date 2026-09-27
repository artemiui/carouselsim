"""
Utility to download OpenStreetMap XML (.osm) for the EDSA corridor.
Downloads the real EDSA road geometry from Overpass API and saves it locally
as 'edsa_corridor.osm'. This allows 100% offline simulation runs with exact road distances.
"""

import urllib.request
import urllib.parse
import os
import sys

OUTPUT_FILE = "edsa_corridor.osm"

# Overpass API query for EDSA highway ways and their coordinate nodes
QUERY = """[out:xml][timeout:60];
(
  way["highway"~"trunk|primary|secondary"]["name"~"Epifanio|EDSA"](14.50,120.97,14.67,121.07);
  node(w);
);
out body;
>;
out skel qt;
"""

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
]

def download_edsa_osm_xml(output_path: str = OUTPUT_FILE) -> bool:
    print("=" * 60)
    print(" Downloading EDSA Corridor OpenStreetMap XML")
    print("=" * 60)
    
    encoded_data = urllib.parse.urlencode({"data": QUERY}).encode("utf-8")
    headers = {
        "User-Agent": "EDSA-Carousel-Sim/1.0 (Transportation Engineering Research; Metro Manila)",
        "Accept": "application/xml, text/xml, */*"
    }
    
    for server_url in OVERPASS_SERVERS:
        print(f"Querying Overpass server: {server_url} ...")
        try:
            req = urllib.request.Request(server_url, data=encoded_data, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    content = resp.read()
                    if b"<osm" in content:
                        with open(output_path, "wb") as f:
                            f.write(content)
                        size_kb = len(content) / 1024.0
                        print(f"SUCCESS: Downloaded {size_kb:.1f} KB of OSM XML to '{output_path}'.")
                        print("The simulation can now run 100% offline with zero API calls!")
                        return True
                    else:
                        print(f"Warning: Response was not valid OSM XML from {server_url}.")
        except Exception as e:
            print(f"Server {server_url} failed: {e}")
            
    print("\nCould not download automatically. You can also export manually:")
    print("1. Go to https://www.openstreetmap.org/export")
    print("2. Enter Bounding Box: North 14.67, South 14.50, East 121.07, West 120.97")
    print(f"3. Click 'Export' and save the file as '{OUTPUT_FILE}' in this folder.")
    return False

if __name__ == "__main__":
    download_edsa_osm_xml()
