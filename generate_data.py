"""
Dataset Generator for Public Transport Analytics Project
Creates realistic, multi-modal public transport operational data:
- Buses, Metro, Suburban Rail, BRTS
- Peak-hour demand spikes, weekend variations
- Delays, Fares, Capacities, Distances, Routes
"""

import csv
import random
from datetime import datetime, timedelta

# Set seed for reproducible realistic data
random.seed(42)

# Transport modes, routes, and operational profiles
ROUTES = [
    {
        "route_id": "BUS-101",
        "route_name": "Central Station ⇄ IT Tech Park",
        "transport_type": "Bus",
        "source_stop": "Central Railway Station",
        "destination_stop": "Cyber City Tech Park",
        "distance_km": 16.5,
        "base_travel_time": 45,
        "capacity": 60,
        "ticket_price": 30.0,
        "peak_multiplier": 1.4,
        "vehicles": [f"BUS-KA01-E{i:03d}" for i in range(101, 112)]
    },
    {
        "route_id": "BUS-102",
        "route_name": "Airport Express ⇄ Downtown Terminal",
        "transport_type": "Bus",
        "source_stop": "International Airport Terminal 2",
        "destination_stop": "Downtown Central Terminal",
        "distance_km": 28.0,
        "base_travel_time": 60,
        "capacity": 50,
        "ticket_price": 90.0,
        "peak_multiplier": 1.25,
        "vehicles": [f"BUS-KA01-A{i:03d}" for i in range(201, 210)]
    },
    {
        "route_id": "BUS-105",
        "route_name": "Westside Mall ⇄ Harbor Port",
        "transport_type": "Bus",
        "source_stop": "Westside Mall Circle",
        "destination_stop": "South Harbor Port Gate",
        "distance_km": 14.2,
        "base_travel_time": 38,
        "capacity": 60,
        "ticket_price": 25.0,
        "peak_multiplier": 1.2,
        "vehicles": [f"BUS-KA02-W{i:03d}" for i in range(301, 310)]
    },
    {
        "route_id": "BUS-110",
        "route_name": "University Campus ⇄ City Center",
        "transport_type": "Bus",
        "source_stop": "State University North Gate",
        "destination_stop": "City Commercial Center",
        "distance_km": 11.0,
        "base_travel_time": 32,
        "capacity": 60,
        "ticket_price": 20.0,
        "peak_multiplier": 1.35,
        "vehicles": [f"BUS-KA02-U{i:03d}" for i in range(401, 410)]
    },
    {
        "route_id": "METRO-BLU",
        "route_name": "Metro Blue Line: North Ridge ⇄ Tech Valley",
        "transport_type": "Metro",
        "source_stop": "North Ridge Terminal",
        "destination_stop": "Tech Valley Central",
        "distance_km": 24.5,
        "base_travel_time": 35,
        "capacity": 320,
        "ticket_price": 45.0,
        "peak_multiplier": 1.6,
        "vehicles": [f"METRO-B-{i:02d}" for i in range(1, 11)]
    },
    {
        "route_id": "METRO-RED",
        "route_name": "Metro Red Line: East Suburb ⇄ Financial District",
        "transport_type": "Metro",
        "source_stop": "East Suburb Terminal",
        "destination_stop": "Financial District Hub",
        "distance_km": 21.0,
        "base_travel_time": 30,
        "capacity": 320,
        "ticket_price": 40.0,
        "peak_multiplier": 1.55,
        "vehicles": [f"METRO-R-{i:02d}" for i in range(1, 11)]
    },
    {
        "route_id": "RAIL-CST",
        "route_name": "Suburban Rail: Coast Line ⇄ Old City Junction",
        "transport_type": "Suburban Rail",
        "source_stop": "Coastal Harbor Junction",
        "destination_stop": "Old City Main Junction",
        "distance_km": 38.0,
        "base_travel_time": 55,
        "capacity": 750,
        "ticket_price": 25.0,
        "peak_multiplier": 1.5,
        "vehicles": [f"RAIL-EMU-{i:03d}" for i in range(501, 508)]
    },
    {
        "route_id": "RAIL-EXT",
        "route_name": "Suburban Rail: Industrial Corridor ⇄ South Terminal",
        "transport_type": "Suburban Rail",
        "source_stop": "Northern Industrial Zone",
        "destination_stop": "South Terminal Intermodal",
        "distance_km": 42.5,
        "base_travel_time": 65,
        "capacity": 750,
        "ticket_price": 30.0,
        "peak_multiplier": 1.45,
        "vehicles": [f"RAIL-EMU-{i:03d}" for i in range(601, 608)]
    },
    {
        "route_id": "BRTS-01",
        "route_name": "BRTS Ring Corridor: Outer Express",
        "transport_type": "BRTS",
        "source_stop": "East Ring Hub",
        "destination_stop": "West Ring Hub",
        "distance_km": 18.0,
        "base_travel_time": 32,
        "capacity": 85,
        "ticket_price": 35.0,
        "peak_multiplier": 1.3,
        "vehicles": [f"BRTS-OR-{i:02d}" for i in range(1, 9)]
    }
]

# Generate data for 90 days: 2024-01-01 to 2024-03-30
start_date = datetime(2024, 1, 1)
total_days = 90

records = []

# Operational hours: 06:00 to 22:30
# Define hourly schedule probabilities and peak weights
hourly_weights = {
    6: 0.35, 7: 0.70, 8: 1.45, 9: 1.60, 10: 1.25,
    11: 0.85, 12: 0.80, 13: 0.75, 14: 0.80, 15: 0.90,
    16: 1.10, 17: 1.50, 18: 1.65, 19: 1.40, 20: 1.05,
    21: 0.65, 22: 0.40
}

trip_id_counter = 10001

for day_offset in range(total_days):
    current_date = start_date + timedelta(days=day_offset)
    is_weekend = current_date.weekday() >= 5
    date_str = current_date.strftime("%Y-%m-%d")
    
    # On weekends, demand is ~75% of weekdays
    weekend_factor = 0.75 if is_weekend else 1.0

    for route in ROUTES:
        # Number of scheduled trips per day for this route
        if route["transport_type"] == "Suburban Rail":
            trips_count = random.randint(2, 4)
        elif route["transport_type"] == "Metro":
            trips_count = random.randint(4, 6)
        else: # Bus and BRTS
            trips_count = random.randint(3, 5)
            
        # Distribute trips across day
        selected_hours = random.sample(list(hourly_weights.keys()), k=trips_count)
        selected_hours.sort()
        
        for hour in selected_hours:
            minute = random.choice([0, 10, 15, 20, 30, 40, 45, 50])
            second = random.choice([0, 15, 30, 45])
            time_str = f"{hour:02d}:{minute:02d}:{second:02d}"
            
            # Base capacity and load factor
            hw = hourly_weights[hour]
            base_load_factor = (hw * weekend_factor) * random.uniform(0.60, 0.90)
            # Cap load factor at 1.08 (occasional over-crowding)
            load_factor = min(1.08, max(0.20, base_load_factor))
            
            passengers = int(route["capacity"] * load_factor)
            passengers = max(8, min(int(route["capacity"] * 1.08), passengers))
            
            # Delay modeling
            is_peak = (8 <= hour <= 10) or (17 <= hour <= 19)
            if is_peak:
                # 50% chance of delay
                if random.random() < 0.52:
                    if route["transport_type"] == "Metro":
                        delay = random.randint(1, 8)
                    elif route["transport_type"] == "Suburban Rail":
                        delay = random.randint(3, 24)
                    else: # Bus & BRTS
                        delay = random.randint(4, 35)
                else:
                    delay = 0
            else:
                # Off-peak: 25% chance of slight delay
                if random.random() < 0.25:
                    delay = random.randint(1, 10)
                else:
                    delay = 0
            
            # Travel time with delay impact
            travel_time = route["base_travel_time"] + int(delay * random.uniform(0.5, 0.9))
            
            # Revenue calculation
            revenue = round(passengers * route["ticket_price"], 2)
            
            # Pick a vehicle
            vehicle = random.choice(route["vehicles"])
            
            # Status classification
            if delay <= 3:
                status = "On-Time"
            elif delay <= 15:
                status = "Moderate Delay"
            else:
                status = "Major Delay"

            records.append({
                "trip_id": f"TRIP-{trip_id_counter}",
                "date": date_str,
                "time": time_str,
                "route_id": route["route_id"],
                "route_name": route["route_name"],
                "transport_type": route["transport_type"],
                "vehicle_id": vehicle,
                "source_stop": route["source_stop"],
                "destination_stop": route["destination_stop"],
                "distance_km": route["distance_km"],
                "vehicle_capacity": route["capacity"],
                "passenger_count": passengers,
                "ticket_price": route["ticket_price"],
                "revenue": revenue,
                "delay_minutes": delay,
                "travel_time_mins": travel_time,
                "status": status
            })
            
            trip_id_counter += 1

output_file = "C:/Users/Kunal Pol/.gemini/antigravity/scratch/Public-Transport-Analytics/data/public_transport_data.csv"
fieldnames = [
    "trip_id", "date", "time", "route_id", "route_name", "transport_type",
    "vehicle_id", "source_stop", "destination_stop", "distance_km",
    "vehicle_capacity", "passenger_count", "ticket_price", "revenue",
    "delay_minutes", "travel_time_mins", "status"
]

with open(output_file, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)

print(f"Successfully generated {len(records)} realistic transport operational records at {output_file}")
