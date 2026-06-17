# ============================================================
# VECTORISED PAIRED OD TRAVEL TIME & DISTANCE (CAR / WALK / TRANSIT)
# ============================================================

import os
import pandas as pd
import numpy as np
import pandana as pdna
import time

t0 = time.time()

# ---------------------------- CONFIG ----------------------------
root_dir = r"C:/Users/username"

drive_file   = os.path.join(root_dir, "assets/data/networks/gipuzkoa_drive_net.h5")
walk_file    = os.path.join(root_dir, "assets/data/networks/gipuzkoa_walk_net.h5")
transit_file = os.path.join(root_dir, "assets/data/networks/gipuzkoa_integrated_net_all_hours.h5")t_all_hours_drive_fallback.h5")

HOUR = "07"

# 5 paired OD points (lat, lon)
origins = [
    (43.31291613, -2.004880785),
    (43.31920156, -1.929862138),
    (43.32600000, -1.96000000),
    (43.30750000, -2.02000000),
    (43.31244921, -1.898043517),
    (43.135195,-2.071947),
    (43.107811,-2.133762),
    (43.252617997745624, -2.0203129784790548),
    (43.135644047837445, -2.076339576768636)
]

destinations = [
    (43.32000000, -1.93000000),
    (43.31500000, -1.95000000),
    (43.33000000, -1.97000000),
    (43.31000000, -2.01000000),
    (43.256347, -2.033693),
    (43.212268, -2.022877),
    (43.213847,-2.022759),
    (43.13524706756529, -2.0753605115958895),
    (43.19290622597661, -2.096324953020156)
]

# Speeds for fallback distance calculation (if network distance is missing)
walk_speed_m_s = 1.4  # 5 km/h
ride_speed_m_s = 5.0  # 18 km/h

# ---------------------------- HELPERS ----------------------------

def load_pandana_network(h5_file, time_col="travel_time_s", dist_col="distance_m"):
    """Load a Pandana network from HDF5."""
    if h5_file.endswith(".h5") and "integrated" in h5_file:  # transit
        nodes = pd.read_hdf(h5_file, key=f"nodes_{HOUR}")
        edges = pd.read_hdf(h5_file, key=f"edges_{HOUR}")
        return pdna.Network(
            nodes["x"].values,
            nodes["y"].values,
            edges["from_pid"].values,
            edges["to_pid"].values,
            edges[[time_col, dist_col]].copy()
        )
    else:  # drive / walk networks
        return pdna.Network.from_hdf5(h5_file)

def get_node_ids(net, latlon_list):
    """Vectorized: convert list of (lat, lon) to Pandana node IDs."""
    lats, lons = zip(*latlon_list)
    return net.get_node_ids(list(lons), list(lats))

def paired_od_travel(net, origins, destinations, time_imp="travel_time_s", dist_imp=None, fallback_speed=None):
    """Compute paired OD travel times and distances (vectorized)."""
    origin_nodes = get_node_ids(net, origins)
    dest_nodes = get_node_ids(net, destinations)

    # Travel time
    T = net.shortest_path_lengths(origin_nodes, dest_nodes, imp_name=time_imp)

    # Distance
    if dist_imp and dist_imp in net.impedance_names:
        D = net.shortest_path_lengths(origin_nodes, dest_nodes, imp_name=dist_imp)
    elif fallback_speed is not None:
        D = np.array(T) * fallback_speed
    else:
        D = np.zeros_like(T)

    # Return dataframe
    return pd.DataFrame({
        "O_lat": [lat for lat, lon in origins],
        "O_lon": [lon for lat, lon in origins],
        "D_lat": [lat for lat, lon in destinations],
        "D_lon": [lon for lat, lon in destinations],
        "Travel_time_s": T,
        "Distance_m": D
    })


from shapely.geometry import LineString

def get_route_linestring(net, origin, destination, imp_name):
    """
    Returns a LineString of the shortest path between origin and destination.
    origin, destination: (lat, lon)
    imp_name: impedance to minimize (e.g. 'drive_time_s', 'travel_time_s')
    """
    o_lat, o_lon = origin
    d_lat, d_lon = destination

    # get node IDs
    o_node = net.get_node_ids([o_lon], [o_lat])[0]
    d_node = net.get_node_ids([d_lon], [d_lat])[0]

    # shortest path in terms of impedance
    path_nodes = net.shortest_path(o_node, d_node, imp_name=imp_name)

    # extract coordinates from nodes_df
    xs = net.nodes_df.loc[path_nodes, 'x'].values
    ys = net.nodes_df.loc[path_nodes, 'y'].values

    return LineString(zip(xs, ys))




# ---------------------------- LOAD NETWORKS ----------------------------
print("Loading Pandana networks...")
drive_net   = load_pandana_network(drive_file, time_col="drive_time_s", dist_col="distance_m")
walk_net    = load_pandana_network(walk_file, time_col="travel_time_s", dist_col="distance_m")
transit_net = load_pandana_network(transit_file, time_col="travel_time_s", dist_col="distance_m")
print("✔ All networks loaded\n")

# ---------------------------- COMPUTE PAIRED OD ----------------------------
drive_df = paired_od_travel(drive_net, origins, destinations, time_imp="drive_time_s", dist_imp="distance_m")
walk_df = paired_od_travel(walk_net, origins, destinations, time_imp="travel_time_s", dist_imp="distance_m", fallback_speed=walk_speed_m_s)
transit_df = paired_od_travel(transit_net, origins, destinations, time_imp="travel_time_s", dist_imp="distance_m", fallback_speed=ride_speed_m_s)

# ---------------------------- COMBINE ALL MODES ----------------------------
final_df = pd.DataFrame({
    "O_lat": [lat for lat, lon in origins],
    "O_lon": [lon for lat, lon in origins],
    "D_lat": [lat for lat, lon in destinations],
    "D_lon": [lon for lat, lon in destinations],
    "d_car_km": (drive_df.Distance_m / 1000).round(2),
    "d_PT_km": (transit_df.Distance_m / 1000).round(2),
    "d_walk_km": (walk_df.Distance_m / 1000).round(2),
    "tt_car_min": (drive_df.Travel_time_s / 60).round(1),
    "tt_PT_min": (transit_df.Travel_time_s / 60).round(1),
    "tt_walk_min": (walk_df.Travel_time_s / 60).round(1)
})

# ---------------------------- PRINT FINAL TABLE ----------------------------
print("\n--- Paired OD Travel Times & Distances ---")
print(final_df)

t1 = time.time()
print(f"\n✅ Total elapsed time: {round((t1-t0)/60, 3)} min")

# ============================================================


# ---------------------------- ROUTES FOR FIRST OD PAIR ----------------------------
import plotly.graph_objects as go

# Example OD pair
origin_0 = origins[0]
dest_0   = destinations[0]

# Get LineStrings (using fixed get_route_linestring from Pandana)
drive_route   = get_route_linestring(drive_net, origin_0, dest_0, imp_name="drive_time_s")
walk_route    = get_route_linestring(walk_net,  origin_0, dest_0, imp_name="travel_time_s")
transit_route = get_route_linestring(transit_net, origin_0, dest_0, imp_name="travel_time_s")

fig = go.Figure()

# Add routes
for route, color, name in zip([walk_route, transit_route, drive_route],
                              ["green", "blue", "red"],
                              ["Walk", "PT", "Car"]):
    lons, lats = zip(*route.coords)
    fig.add_trace(go.Scattermapbox(
        lon=lons, lat=lats,
        mode="lines",
        line=dict(color=color, width=4),
        name=name
    ))

# Add origin/destination points
fig.add_trace(go.Scattermapbox(
    lon=[origin_0[1]], lat=[origin_0[0]],
    mode="markers",
    marker=dict(color="black", size=8),
    name="Origin"
))
fig.add_trace(go.Scattermapbox(
    lon=[dest_0[1]], lat=[dest_0[0]],
    mode="markers",
    marker=dict(color="orange", size=8),
    name="Destination"
))

# Layout
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=12,
    mapbox_center={"lat":42.91,"lon":-2.0},
    margin=dict(l=0,r=0,t=0,b=0),
    legend=dict(font=dict(size=14))  # slightly bigger legend font
)

fig.show()