import json
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.safari.webdriver import WebDriver as SafariDriver
from selenium.common.exceptions import WebDriverException
import os

try:
    with open("config.json", "r") as f:
        config = json.load(f)
    WHOSCORED_URL = config["MATCH_SETTINGS"]["WHOSCORED_URL"]
    OUTPUT_DIR = config["MATCH_SETTINGS"]["DATA_DIR"]
except FileNotFoundError:
    print("FATAL ERROR: config.json not found. Please create it.")
    exit()
except KeyError as e:
    print(f"FATAL ERROR: Key {e} missing from config.json under MATCH_SETTINGS.")
    exit()

def scrape_whoscored_events():
    print("Starting WhoScored scraping using Safari...")
    
    try:
        driver = webdriver.Safari() 
        driver.set_page_load_timeout(45)
    except WebDriverException as e:
        print(f"CRITICAL SAFARI DRIVER ERROR: {e}")
        print("Ensure Safari's 'Develop > Allow Remote Automation' is enabled.")
        return None, None
    except Exception as e:
        print(f"General driver error: {e}")
        return None, None

    try:
        driver.get(WHOSCORED_URL)
        time.sleep(5)  
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        element = soup.select_one('script:-soup-contains("matchCentreData")')
        driver.quit()

        if element:
            match_data_raw = element.text.split("matchCentreData: ")[1].split(',\n')[0]
            matchdict = json.loads(match_data_raw)
            
            df_events = pd.DataFrame(matchdict['events'])
            
            df_events = df_events.rename(columns={
                'eventId': 'id', 
                'outcomeType': 'outcome_type', 
                'playerId': 'player_id', 
                'teamId': 'team_id',
                'endX': 'end_x', 
                'endY': 'end_y',
                'isTouch': 'is_touch',
                'isShot': 'is_shot',
                'isGoal': 'is_goal'
            })
            
            get_display_name = lambda x: x['displayName'] if isinstance(x, dict) and 'displayName' in x else None
            df_events['type_display_name'] = df_events['type'].apply(get_display_name)
            df_events['outcome_type_display_name'] = df_events['outcome_type'].apply(get_display_name)
            
            print("WhoScored Data extracted successfully.")
            return matchdict, df_events
        else:
            print("ERROR: matchCentreData not found!")
            return None, None

    except Exception as e:
        print(f"An error occurred during page interaction: {e}")
        if 'driver' in locals():
            driver.quit()
        return None, None

def main_scrape():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    matchdict, df_events = scrape_whoscored_events()
    
    if matchdict and df_events is not None and not df_events.empty:
        df_events.to_csv(os.path.join(OUTPUT_DIR, "df_events.csv"), index=False)
        with open(os.path.join(OUTPUT_DIR, "matchdict.json"), "w") as f:
            json.dump(matchdict, f, indent=4)
        print(f"Saved df_events.csv and matchdict.json to {OUTPUT_DIR}")
    else:
        print("CRITICAL: Failed to save any core WhoScored match data.")
        
if __name__ == "__main__":
    main_scrape()