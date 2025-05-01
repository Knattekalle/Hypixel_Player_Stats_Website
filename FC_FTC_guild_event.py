# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 13:09:00 2025

@author: Knatt
"""

import requests
import json
import csv
import os
import datetime
import time
import pandas as pd


API_KEY = os.getenv("HYPIXEL_API_KEY")

SLEEP_DELAY = 10
SLEEP_DELAY_SHORT = 1

# Global list of skill keys used in multiple places
COLLECTION_KEYS = [
    'ROTTEN_FLESH', 'COBBLESTONE', 'MITHRIL_ORE', 'PUMPKIN', 'GOLD_INGOT', 'SPIDER_EYE', 'STRING', 'BONE', 'SLIME_BALL', 
    'LOG:2', 'LOG', 'LOG:1', 'LOG:3', 'LOG_2', 'LOG_2:1', 'ENDER_PEARL', 'ENDER_STONE', 'OBSIDIAN', 
    'BLAZE_ROD', 'COAL', 'GEMSTONE_COLLECTION', 'HARD_STONE', 'IRON_INGOT', 'EMERALD', 'INK_SACK:4', 'ICE', 
    'SULPHUR', 'MAGMA_CREAM', 'REDSTONE', 'SULPHUR_ORE', 'DIAMOND', 'GLOWSTONE_DUST', 'SAND:1', 'QUARTZ', 'MAGMA_FISH',
    'CADUCOUS_STEM', 'WILTED_BERBERIS', 'AGARICUS_CAP', 'HALF_EATEN_CARROT', 'METAL_HEART', 'HEMOVIBE', 
    'INK_SACK:3', 'GRAVEL', 'NETHERRACK', 'FEATHER', 'LEATHER', 'PORK', 'RAW_CHICKEN', 
    'CARROT_ITEM', 'MUSHROOM_COLLECTION', 'WHEAT', 'POTATO_ITEM', 'NETHER_STALK', 'SUGAR_CANE', 'MUTTON', 'RABBIT', 'MELON', 'CACTUS', 'GHAST_TEAR', 'SEEDS', 'GLACITE',
    'SAND', 'PRISMARINE_CRYSTALS', 'PRISMARINE_SHARD', 'RAW_FISH', 'RAW_FISH:1', 'RAW_FISH:2', 'RAW_FISH:3', 
    'SPONGE', 'WATER_LILY', 'CLAY_BALL', 'INK_SACK', 'UMBER', 'TUNGSTEN', 'MYCEL', 'TIMITE', 'CHILI_PEPPER'
]

SKILL_KEYS = [
    "SKILL_FARMING", "SKILL_MINING", "SKILL_COMBAT", "SKILL_FORAGING",
    "SKILL_FISHING", "SKILL_ENCHANTING", "SKILL_ALCHEMY", "SKILL_TAMING",
    "SKILL_CARPENTRY", "SKILL_SOCIAL"
]

CLASS_KEYS = [
    "healer", "mage", "berserk", "archer", "tank"
]

NORMAL_FLOORS_KEYS = [
    "total", "0", "1", "2", "3", "4", "5", "6", "7"
]

MASTER_MODE_FLOORS_KEYS = [
    "total", "1", "2", "3", "4", "5", "6", "7"
]

KUUDRA_TIER_KEYS = [
    "none", "hot", "burning", "fiery", "infernal"
]

#
def getInfo(call):
    r = requests.get(call)
    return r.json()


#
def convert_unix_timestamp(timestamp):
    # If timestamp is in milliseconds, divide by 1000
    if timestamp > 10000000000:  # Assume it's in milliseconds
        timestamp = timestamp / 1000
        
    # Convert the Unix timestamp to a datetime object
    readable_time = datetime.datetime.fromtimestamp(timestamp)
    
    # Format it to a string in YYYY-MM-DD HH:MM:SS
    formatted_time = readable_time.strftime("%Y-%m-%d %H:%M:%S")
    
    return formatted_time

# Not used for github-workflows, using def load_usernames_from_cache(uuid_list) instead
def fetch_username(uuid):
    """Fetch the username from Mojang API using the player's UUID"""
    
    # Mojang API URL
    MOJANG_API = f"https://api.minecraftservices.com/minecraft/profile/lookup/{uuid}"
    
    data = getInfo(MOJANG_API)                             
    return data.get("name") if data else None  # Return the username if available
# Not used for github-workflows, using def load_usernames_from_cache(uuid_list) instead
def load_or_fetch_usernames(uuid_list):
    """Load usernames from today's cache or fetch from API and cache them."""
    
    #today = datetime.datetime.now().strftime("%Y_%m_%d")
    today = "2025_04_30"
    filename = f"FC_and_FTC_usernames_{today}.csv"

    username_dict = {}

    if os.path.exists(filename):
        print(f"Loading usernames from cache: {filename}")
        df = pd.read_csv(filename)
        for _, row in df.iterrows():
            username_dict[row['UUID']] = row['Username']
    else:
        print("No cache found. Fetching usernames from Mojang API...")
        rows = []
        for idx, uuid in enumerate(uuid_list, start=1):
            username = fetch_username(uuid)
            username_dict[uuid] = username
            print(f"{idx}/{len(uuid_list)} Fetched: {username}")
            rows.append({"UUID": uuid, "Username": username})
            time.sleep(SLEEP_DELAY)  # Be nice to Mojang’s API

        # Save to CSV
        df = pd.DataFrame(rows)
        df.to_csv(filename, index=False)
        print(f"Saved username cache to: {filename}")

    return [username_dict[uuid] for uuid in uuid_list]  # Ordered username list  


def load_usernames_from_cache(uuid_list):
    """
    Load usernames from a pre-uploaded CSV file containing UUID-to-Username mapping.
    No API calls — assumes file is present in repo.
    """

    # Update this if you change the filename
    today = "2025_04_30"
    filename = f"FC_and_FTC_usernames_{today}.csv"
    username_dict = {}

    if not os.path.exists(filename):
        raise FileNotFoundError(f"Username cache file '{filename}' not found in repository. Please upload it before running.")

    print(f"Loading usernames from cache: {filename}")
    df = pd.read_csv(filename)

    for _, row in df.iterrows():
        username_dict[row['UUID']] = row['Username']

    # Return the usernames in the same order as the input UUIDs
    return [username_dict.get(uuid, "Unknown") for uuid in uuid_list]



#
def fetch_guild_info(guild_id):
    PLAYER_GUILD_API = f"https://api.hypixel.net/v2/guild?player={guild_id}&key={API_KEY}"
    guild_info = getInfo(PLAYER_GUILD_API)

    guild_name = guild_info["guild"]["name"]
    members = guild_info["guild"]["members"]

    # Return a list of tuples: (uuid, joined, guild_name)
    return [(member["uuid"], member["joined"], guild_name) for member in members]


#
def fetch_skyblock_data(uuid_list):
    """Fetch Skyblock data for all UUIDs and return as a dictionary"""
    
    # Uses global SKILL_KEYS
    a = 0
    guild_data = {}

    for uuid in uuid_list:
        a += 1
        SKYBLOCK_PROFILE_API = f"https://api.hypixel.net/v2/skyblock/profiles?uuid={uuid}&key={API_KEY}"
        data = getInfo(SKYBLOCK_PROFILE_API)

        profiles = data.get("profiles", None)
        if not profiles:
            print(f"Error: No Skyblock data found for UUID {uuid}. Full API response: {data}")
            guild_data[uuid] = {
                "Skyblock XP": 0,
                "Zombie Slayer XP": 0,
                "Catacombs XP": 0
            }
            continue

        best_profile = None
        highest_xp = 0
        
        for profile in profiles:
            skyblock_xp = profile.get("members", {}).get(uuid, {}).get("leveling", {}).get("experience", 0)
        
            if skyblock_xp > highest_xp:
                highest_xp = skyblock_xp
                best_profile = profile
                
        if best_profile:
            profile_members = best_profile["members"]
            print(f"{a}/{len(uuid_list)} Getting skyblock information for uuid: {uuid}")

            # Base stats
            guild_data[uuid] = {
                "Skyblock XP": profile_members[uuid].get("leveling", {}).get("experience", 0),
                "Zombie Slayer XP": profile_members[uuid].get("slayer", {}).get("slayer_bosses", {}).get("zombie", {}).get("xp", 0),
                "Spider Slayer XP": profile_members[uuid].get("slayer", {}).get("slayer_bosses", {}).get("spider", {}).get("xp", 0),
                "Wolf Slayer XP": profile_members[uuid].get("slayer", {}).get("slayer_bosses", {}).get("wolf", {}).get("xp", 0),
                "Enderman Slayer XP": profile_members[uuid].get("slayer", {}).get("slayer_bosses", {}).get("enderman", {}).get("xp", 0),
                "Blaze Slayer XP": profile_members[uuid].get("slayer", {}).get("slayer_bosses", {}).get("blaze", {}).get("xp", 0),
                "Vampire Slayer XP": profile_members[uuid].get("slayer", {}).get("slayer_bosses", {}).get("vampire", {}).get("xp", 0),
                "Catacombs XP": profile_members[uuid].get("dungeons", {}).get("dungeon_types", {}).get("catacombs", {}).get("experience", 0),
                "Amount of Secrets": profile_members[uuid].get("dungeons", {}).get("secrets", 0),
                "Mythological Kills": profile_members[uuid].get("player_stats", {}).get("mythos", {}).get("kills", 0),
                "Burrows Chains Complete": profile_members[uuid].get("player_stats", {}).get("mythos", {}).get("burrows_dug_next", {}).get("total", 0),
                "Burrows Dug": profile_members[uuid].get("player_stats", {}).get("mythos", {}).get("burrows_chains_complete", {}).get("total", 0),
                "Sea Creatures Caught": profile_members[uuid].get("player_stats", {}).get("pets", {}).get("milestone", {}).get("sea_creatures_killed", 0),
                "Trophy Fish Caught": profile_members[uuid].get("trophy_fish", {}).get("total_caught", 0)
            }
                                
            # Dictionaries
            collection_data = {}
            skill_xp_data = {}
            class_xp_data = {}
            normal_floors_data = {}
            master_mode_floors_data = {}
            kuudra_runs = {}
            
            # Collections loop (this only includes personal collections, so if your coop members grinds a collection this wont change your own data)
            for collection_id in COLLECTION_KEYS:
                collection_item = profile_members[uuid].get("collection", {}).get(collection_id, 0)
                collection_data[collection_id] = collection_item
                
            # Merge collection into main data
            guild_data[uuid].update(collection_data)
            
            # Skills loop
            for skill_id in SKILL_KEYS:
                skill_xp = profile_members[uuid].get("player_data", {}).get("experience", {}).get(skill_id, 0)
                skill_xp_data[skill_id] = skill_xp  # e.g., "SKILL_FARMING": 12345 lA                
                
            # Merge skill XP into main data
            guild_data[uuid].update(skill_xp_data)
            
            # CLass XP loop
            for class_id in CLASS_KEYS:
                class_xp = profile_members[uuid].get("dungeons", {}).get("player_classes", {}).get(class_id, {}).get("experience", 0)
                class_xp_data[class_id] = class_xp
            
            # Merge class XP into main data
            guild_data[uuid].update(class_xp_data)
            
            
            # Dungeon Floor loop
            #Normal Floors
            for floor_id in NORMAL_FLOORS_KEYS:
                floor = profile_members[uuid].get("dungeons", {}).get("dungeon_types", {}).get("catacombs", {}).get("tier_completions", {}).get(floor_id, 0)
                normal_floors_data[floor_id] = floor
            
            guild_data[uuid].update(normal_floors_data)
            
            #Master_Mode
            for master_floor_id in MASTER_MODE_FLOORS_KEYS:    
                master_floor = profile_members[uuid].get("dungeons", {}).get("dungeon_types", {}).get("master_catacombs", {}).get("tier_completions", {}).get(master_floor_id, 0)
                master_mode_floors_data[f"M_{master_floor_id}"] = master_floor
            
            # Merge amount of runs per floor into main data
            guild_data[uuid].update(master_mode_floors_data)
            
            # Kuudra runs loop
            for kuudra_id in KUUDRA_TIER_KEYS:
                kuudra_completions = profile_members[uuid].get("nether_island_player_data", {}).get("kuudra_completed_tiers", {}).get(kuudra_id, 0)
                kuudra_runs[kuudra_id] = kuudra_completions 
                
            guild_data[uuid].update(kuudra_runs)
            
        else:
            print(f"{a}/{len(uuid_list)} Skipping UUID {uuid} — no valid profile found.")
            guild_data[uuid] = {"Skyblock XP": 0}
                
        time.sleep(SLEEP_DELAY_SHORT)  # Hypixel API rate limits

    return guild_data



#
def write_skyblock_data_to_csv(date_list, username_list, guild_list, guild_data): 
    """Write Skyblock stats data to a new CSV file"""
    filename="Guild_FC_and_FTC"


    # Convert dictionary to DataFrame    
    df = pd.DataFrame.from_dict(guild_data, orient="index")
    df.reset_index(inplace=True)
    df.rename(columns={"index": "UUID"}, inplace=True)
    
    # Added Joined Guild data
    df['Snapshot Time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df['Guild'] = guild_list
    df['Joined Guild'] = date_list
    df['Username'] = username_list
    
    
    # Basic static columns
    base_columns = [
        'Snapshot Time', 'Guild', 'Joined Guild', 'UUID', 'Username',
        'Skyblock XP', 'Zombie Slayer XP', 'Spider Slayer XP',
        'Wolf Slayer XP', 'Enderman Slayer XP', 'Blaze Slayer XP', 'Vampire Slayer XP',
        'Catacombs XP', 'Amount of Secrets', 'Mythological Kills', 'Burrows Chains Complete', 'Burrows Dug',
        'Sea Creatures Caught', 'Trophy Fish Caught'
    ]
   
    # Skill XP columns (from global SKILL_KEYS list)
    collection_columns = COLLECTION_KEYS
    skill_columns = SKILL_KEYS  # These are used as-is for now, e.g., "SKILL_FARMING"
    class_columns = CLASS_KEYS
    floor_columns = NORMAL_FLOORS_KEYS
    master_floor_columns = [f"M_{floor}" for floor in MASTER_MODE_FLOORS_KEYS]  # <-- update here
    kuudra_runs_columns = KUUDRA_TIER_KEYS
    
    # Final column order
    column_order = base_columns + collection_columns + skill_columns + class_columns + floor_columns + master_floor_columns + kuudra_runs_columns

    # Reorder columns (only include ones that actually exist in DataFrame)
    existing_columns = [col for col in column_order if col in df.columns]
    df = df[existing_columns]
    
    # Save DataFrame to CSV 
    full_filename = f"data/{filename}.csv"
    df.to_csv(full_filename, mode='a', header=not os.path.exists(full_filename), index=False)
    print(f"Data successfully written to {full_filename }")


#
def main():
    # Record the start time
    start_time = time.time()
    print("Script started...")
    
    # My uuid and API Key
    fc_guild_id = "29135e50c229404ba0b2a147abc374fc" # My (Knattekalle's) uuid 
    ftc_guild_id = "88ef0bfe7d66478d8f94bf7334d35066" # SpeedBoostDog's uuid
    
    # Gather guild information
    fc_members = fetch_guild_info(fc_guild_id)
    ftc_members = fetch_guild_info(ftc_guild_id)
    combined_members = fc_members + ftc_members
    
    uuid_list = [x[0] for x in combined_members]
    date_list = [convert_unix_timestamp(x[1]) for x in combined_members]
    guild_list = [x[2] for x in combined_members]    
   
    print("Successfully gathered Guild Data")
    print("Converted Unix time to readable time")
    
    
    # Convert UUID to Username
    # username_list = load_or_fetch_usernames(uuid_list)
    username_list = load_usernames_from_cache(uuid_list)
    
    print("Converted uuids to usernames")
    
    # Gather player stats from Skyblock
    skyblock_data = fetch_skyblock_data(uuid_list)
    
    print("Gathered player stats")
    
    # Call the write to csv function and add the following lists
    write_skyblock_data_to_csv(date_list, username_list, guild_list, skyblock_data)
    
    print("Updated CSV")
    
    print("... Script is complete!")
    end_time = time.time()

    # Calculate the total time taken
    execution_time = end_time - start_time
    print(f"Script executed in {execution_time:.2f} seconds")


#    
if __name__ == "__main__":
    main()
