# -*- coding: utf-8 -*-
"""
Created on Thu Mar 20 19:12:53 2025

@author: Knatt
"""

import requests
import json
import csv
import os
import datetime
import time
import pandas as pd

# API Key made as a Github Secret
API_KEY = os.getenv("HYPIXEL_API_KEY")

# uuid used to fetch the guild (hardcoded)
uuid_knattekalle = "29135e50c229404ba0b2a147abc374fc"

SLEEP_DELAY_SHORT = 3
SLEEP_DELAY_LONG = 8

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


def fetch_username(uuid):
    """Fetch the username from Mojang API using the player's UUID"""
    
    # Mojang API URL
    MOJANG_API = f"https://api.minecraftservices.com/minecraft/profile/lookup/{uuid}"
    
    data = getInfo(MOJANG_API)                             
    return data.get("name") if data else None  # Return the username if available

#
def fetch_guild_info():
    # Hypixel Guild API
    PLAYER_GUILD_API = f"https://api.hypixel.net/v2/guild?player={uuid_knattekalle}&key={API_KEY}"
    
    # Fetching the information from the url and makes it to json
    guild_info = getInfo(PLAYER_GUILD_API)

    joined_date_list = [] # Empty List
    uuid_list = [] # Empty List

    # Append "joined" and "uuid" into their respective list
    for member in guild_info["guild"]["members"]:
        joined_date_list.append(member["joined"])
        uuid_list.append(member["uuid"])

    return joined_date_list, uuid_list

#
def fetch_skyblock_data(uuid_list):
    """Fetch Skyblock data for all UUIDs and return as a dictionary"""

    guild_data = {}

    for uuid in uuid_list:
        SKYBLOCK_PROFILE_API = f"https://api.hypixel.net/v2/skyblock/profiles?uuid={uuid}&key={API_KEY}"
        data = getInfo(SKYBLOCK_PROFILE_API)

        for profile in data["profiles"]:
            if profile.get("selected", False):  # Check if this is the active profile
                # Stores all profile members uuid from the selected profile. We will assume you are on the correct profile when running this script
                profile_members = profile["members"]
                
                # Store data in dictionary, using .get() to avoid KeyError when data is missing (like for our Bridge bot)
                guild_data[uuid] = {
                    "Skyblock XP": profile_members[uuid].get("leveling", {}).get("experience", 0),  # Default to 0 if not available
                    "Zombie Slayer XP": profile_members[uuid].get("slayer", {}).get("slayer_bosses", {}).get("zombie", {}).get("xp", 0),  # Default to 0 if not available
                    "Catacombs XP": profile_members[uuid].get("dungeons", {}).get("dungeon_types", {}).get("catacombs", {}).get("experience", 0)  # Default to 0 if not available
                }
        time.sleep(SLEEP_DELAY_SHORT) # 3s sleep, Prevent Hypixel API spam as this is fetching all 125 guild members at once, max is 120/5min

    return guild_data


#
def write_skyblock_data_to_csv(date_list, username_list, guild_data, filename="Guild_Event"): 
    """Write Skyblock stats data to a new CSV file"""

    current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    
    # Create a unique filename with the current date (e.g., guild_data_2025-03-23_14-30.csv)
    unique_filename = f"csv_files/{filename}_{current_date}.csv"
    
    # Convert dictionary to DataFrame    
    df = pd.DataFrame.from_dict(guild_data, orient="index")
    
    # Move UUID from index to column
    df.reset_index(inplace=True)
    df.rename(columns={"index": "UUID"}, inplace=True)
    
    # Add Joined Guild data as the first column
    df['Joined Guild'] = date_list
    
    # Add Joined Guild data as the first column
    df['Username'] = username_list
    
    # Specify the column order manually
    column_order = ['Joined Guild', 'UUID', 'Username','Skyblock XP', 'Zombie Slayer XP', 'Catacombs XP']
    
    # Reorder the DataFrame based on the specified column order
    df = df[column_order]
    
    # Save DataFrame to CSV (overwrite any existing file)
    df.to_csv(unique_filename, index=False)
    
    print(f"Data successfully written to {unique_filename}")


#
def main():
    # Record the start time
    start_time = time.time()
    print("Script started...")
    
    # Gather guild information
    date_list, uuid_list = fetch_guild_info()
    
    print("Successfully gathered Guild Data")
    
    # Convert UNIX time to human-readable time
    new_date_list = []
    for i in range(len(date_list)):  # Loop through the list by index
        new_time = convert_unix_timestamp(date_list[i])  # Convert the timestamp at index i
        new_date_list.append(new_time)
    
    print("Converted Unix time to readable time")
    
    # Convert UUID to Username
    a = 0
    username_list = []
    for uuid in uuid_list:
        a+=1
        username = fetch_username(uuid)
        username_list.append(username)
        print(a, "Added: ", username, " to the CSV file.")
        time.sleep(SLEEP_DELAY_LONG)  # 8s sleep, Prevent API spam
    
    print("Converted uuids to usernames")
    
    # Gather player stats from Skyblock
    skyblock_data = fetch_skyblock_data(uuid_list)
    
    print("Gathered player stats")
    
    # Call the write to csv function and add the following lists
    write_skyblock_data_to_csv(new_date_list, username_list, skyblock_data)
    
    print("Updated CSV")
    
    print("... Script is complete!")
    end_time = time.time()

    # Calculate the total time taken
    execution_time = end_time - start_time
    print(f"Script executed in {execution_time:.2f} seconds")


#    
if __name__ == "__main__":
    main()

