import os
import math
import xml.etree.ElementTree as ET

def haversine(lat1, lon1, lat2, lon2):
    # Radius of the earth in km
    R = 6371.0
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def get_gpx_distance(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    # Namespaces
    namespaces = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    
    total_dist = 0.0
    points = []
    
    # Try with namespace
    trkpts = root.findall('.//gpx:trkpt', namespaces)
    if not trkpts:
        # Try without namespace
        trkpts = root.findall('.//trkpt')
        
    for trkpt in trkpts:
        lat = float(trkpt.attrib['lat'])
        lon = float(trkpt.attrib['lon'])
        points.append((lat, lon))
        
    for i in range(1, len(points)):
        p1 = points[i-1]
        p2 = points[i]
        total_dist += haversine(p1[0], p1[1], p2[0], p2[1])
        
    return total_dist

tracks_dir = r"E:\Data\other_projects\VitaSteps\landing_predikalo1\assets\nagykevely\tracks"
for filename in sorted(os.listdir(tracks_dir)):
    if filename.endswith(".gpx"):
        path = os.path.join(tracks_dir, filename)
        dist = get_gpx_distance(path)
        print(f"{filename}: {dist:.2f} km")
