import os
import json
import csv
import pandas as pd

base_folder = "data/crawled"


# extract amenities
def extract_amenity_name(item):
    # amenities is a list of dict
    if isinstance(item, dict):
        return item.get("amenity")
    # amenities is a list of string
    if isinstance(item, str):
        return item
    return None


# scan JSON files to collect all amenities
def collect_amenities_columns(region_path):
    amenities = set()

    for file in os.listdir(region_path):
        if not file.endswith(".json"):
            continue

        with open(os.path.join(region_path, file), "r", encoding="utf-8-sig") as f:
            hotels = json.load(f)

        for hotel in hotels:
            for room_type in hotel.get("room_types", []):
                for amenity in room_type.get("amenities", []):
                    amenity = extract_amenity_name(amenity)
                    if amenity is not None:
                        amenities.add(amenity)

    return sorted(list(amenities))


# scan JSON files to collect room details
def collect_room_details(hotels, amenity_columns):
    rooms = []
    for hotel in hotels:
        for room_type in hotel.get("room_types", []):
            for option in room_type.get("price_options", []):
                row = {
                    "hotel_id": hotel.get("hotel_id"),
                    "hotel_name": hotel.get("hotel_name"),
                    "hotel_address": hotel.get("hotel_address"),
                    "room_type_name": room_type.get("room_type_name"),
                    "option_name": option.get("option_name"),
                    "option_price": option.get("option_price"),
                }

                # initialize amenity columns with 0
                for amenity in amenity_columns:
                    row[amenity] = 0

                # mark amenities = 1
                for amenity in room_type.get("amenities", []):
                    amenity = extract_amenity_name(amenity)
                    row[amenity] = 1

                rooms.append(row)
    return rooms


# write CSV
def write_csv(region_path, region, rows, amenity_columns):
    csv_path = os.path.join(region_path, f"{region}.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "hotel_id",
                "hotel_name",
                "hotel_address",
                "room_type_name",
                "option_name",
                "option_price",
            ]
            + amenity_columns,
            delimiter=";",
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        writer.writerows(rows)

    print("Created:", csv_path)


def delete_all_region_csv():
    for region in os.listdir(base_folder):
        region_path = os.path.join(base_folder, region)
        if not os.path.isdir(region_path):
            continue

        for f in os.listdir(region_path):
            if f.endswith(".csv"):
                csv_path = os.path.join(region_path, f)
                try:
                    os.remove(csv_path)
                    print("Deleted:", csv_path)
                except Exception as e:
                    print("Error deleting:", csv_path, e)


# create csv for each region
def create_csv_each_region():
    # loop through regions in crawled folder
    for region in os.listdir(base_folder):
        region_path = os.path.join(base_folder, region)
        if not os.path.isdir(region_path):
            continue

        # collect amenities
        amenity_columns = collect_amenities_columns(region_path)

        rows = []

        for file in os.listdir(region_path):
            if not file.endswith(".json"):
                continue

            json_path = os.path.join(region_path, file)
            with open(json_path, "r", encoding="utf-8-sig") as f:
                hotels = json.load(f)

            rooms_details = collect_room_details(hotels, amenity_columns)
            rows.extend(rooms_details)

        write_csv(region_path, region, rows, amenity_columns)


# create a united csv file
def merge_csv():
    dfs = []

    for region in os.listdir(base_folder):
        region_path = os.path.join(base_folder, region)
        if not os.path.isdir(region_path):
            continue

        # find csv file inside region folder
        csv_file = [f for f in os.listdir(region_path) if f.endswith(".csv")]
        if not csv_file:
            continue

        # each region folder has only 1 csv file
        csv_path = os.path.join(region_path, csv_file[0])

        df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
        df["region"] = region
        dfs.append(df)

    # merged all csv files with missing columns filled with 0
    merged_csv = pd.concat(dfs, axis=0, ignore_index=True).fillna(0)
    try:
        merged_csv.to_csv(
            "data/merged/merged.csv",
            encoding="utf-8-sig",
            sep=";",
            quoting=1,
        )
    except Exception as e:
        print(f"Exception raised: {e}")


delete_all_region_csv()
create_csv_each_region()
merge_csv()
