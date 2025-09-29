import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from mplsoccer import Pitch
import os

from metrics import (
    prepare_enhanced_passes, get_pass_combinations, get_enhanced_positions, 
    calculate_team_metrics, filter_defensive_actions, calculate_player_defensive_positions, 
    calculate_match_stats, 
    get_enhanced_positions_all, calculate_team_metrics_all,
    get_half_pass_map,
    get_ball_recovery_turnover
)
from viz import (
    plot_enhanced_network, defensive_block, draw_progressive_pass_map, 
    plot_xt_momentum_subplot, plot_match_stats_subplot,
    plot_half_pass_density,
    plot_recovery_turnover_map
)

try:
    with open("config.json", "r") as f:
        config = json.load(f)
    
    DATA_DIR = config["MATCH_SETTINGS"]["DATA_DIR"]
    OUTPUT_FILE_DASHBOARD = config["MATCH_SETTINGS"]["OUTPUT_FILE_DASHBOARD"]
    
    df_events = pd.read_csv(os.path.join(DATA_DIR, "df_events.csv"))
    xT_grid = pd.read_csv(os.path.join(DATA_DIR, "xT_grid.csv"), header=None).values 
    with open(os.path.join(DATA_DIR, "matchdict.json"), "r") as f:
        matchdict_data = json.load(f)

    home_team = matchdict_data['home']
    away_team = matchdict_data['away']
    home_team_id = home_team['teamId']
    away_team_id = away_team['teamId']
    home_team_name = config["TEAM_COLORS"]["HOME_NAME"]
    away_team_name = config["TEAM_COLORS"]["AWAY_NAME"]
    team_id_to_name = {home_team_id: home_team_name, away_team_id: away_team_name}
    
    OUTPUT_DASHBOARD_PATH = os.path.join(DATA_DIR, OUTPUT_FILE_DASHBOARD)

except Exception as e:
    print(f"FATAL ERROR: Configuration or Data loading failed. Check config.json and data files. Error: {e}")
    exit()

df_events['prog_pass'] = np.where(
    (df_events['type_display_name'] == 'Pass'),
    np.sqrt((105 - df_events['x'])**2 + (34 - df_events['y'])**2) - np.sqrt((105 - df_events['end_x'])**2 + (34 - df_events['end_y'])**2),
    0
)

passes_df = prepare_enhanced_passes(df_events) 
home_avg_locs = get_enhanced_positions(passes_df, home_team_id, home_team['players'], matchdict_data['playerIdNameDictionary'])
home_combinations = get_pass_combinations(passes_df, home_team_id)
home_metrics = calculate_team_metrics(passes_df, home_avg_locs, home_team_id)
away_avg_locs = get_enhanced_positions(passes_df, away_team_id, away_team['players'], matchdict_data['playerIdNameDictionary'])
away_combinations = get_pass_combinations(passes_df, away_team_id)
away_metrics = calculate_team_metrics(passes_df, away_avg_locs, away_team_id)
home_avg_locs_all = get_enhanced_positions_all(passes_df, home_team_id, home_team['players'], matchdict_data['playerIdNameDictionary'])
home_metrics_all = calculate_team_metrics_all(passes_df, home_avg_locs_all, home_team_id)
away_avg_locs_all = get_enhanced_positions_all(passes_df, away_team_id, away_team['players'], matchdict_data['playerIdNameDictionary'])
away_metrics_all = calculate_team_metrics_all(passes_df, away_avg_locs_all, away_team_id)
defensive_actions = filter_defensive_actions(df_events)
home_positions = calculate_player_defensive_positions(defensive_actions, home_team_id, home_team['players'])
away_positions = calculate_player_defensive_positions(defensive_actions, away_team_id, away_team['players'])
home_actions = defensive_actions[defensive_actions['team_id'] == home_team_id]
away_actions = defensive_actions[df_events['team_id'] == away_team_id]
stats = calculate_match_stats(df_events, home_team_id, away_team_id)
home_half_pass_df, _ = get_half_pass_map(df_events, home_team_id)
away_half_pass_df, _ = get_half_pass_map(df_events, away_team_id)
home_recovery_df = get_ball_recovery_turnover(df_events, home_team_id)
away_recovery_df = get_ball_recovery_turnover(df_events, away_team_id)

def generate_dashboard():

    BG_COLOR = config["AESTHETICS"]["BG_COLOR"]
    LINE_COLOR = config["AESTHETICS"]["LINE_COLOR"]
    HOME_COLOR = config["TEAM_COLORS"]["HOME_COLOR"]
    AWAY_COLOR = config["TEAM_COLORS"]["AWAY_COLOR"]

    fig, axs = plt.subplots(4, 3, figsize=(24, 20), facecolor=BG_COLOR)
    fig.suptitle(f'{home_team_name} vs {away_team_name} - Full Tactical Report', fontsize=32, color=LINE_COLOR, weight='bold', y=0.98)
    
    plot_enhanced_network(axs[0,0], passes_df, home_avg_locs, home_combinations, home_metrics, 
                          f'{home_team_name} (Starters)', HOME_COLOR, True, BG_COLOR)
    plot_enhanced_network(axs[0,1], passes_df, away_avg_locs, away_combinations, away_metrics, 
                          f'{away_team_name} (Starters)', AWAY_COLOR, False, BG_COLOR)
    plot_match_stats_subplot(axs[0,2], stats, home_team_name, away_team_name) 

    plot_enhanced_network(axs[1,0], passes_df, home_avg_locs_all, home_combinations, home_metrics_all, 
                          f'{home_team_name} (All Players)', HOME_COLOR, True, BG_COLOR)
    plot_enhanced_network(axs[1,1], passes_df, away_avg_locs_all, away_combinations, away_metrics_all, 
                          f'{away_team_name} (All Players)', AWAY_COLOR, False, BG_COLOR)
    plot_xt_momentum_subplot(axs[1,2], df_events, xT_grid, team_id_to_name, home_team_id, away_team_id)

    defensive_block(axs[2,0], home_positions, home_actions, home_team_name, HOME_COLOR, is_away_team=False)
    defensive_block(axs[2,1], away_positions, away_actions, away_team_name, AWAY_COLOR, is_away_team=True)
    plot_half_pass_density(axs[2,2], home_half_pass_df, home_team_name, HOME_COLOR, is_away_team=False) 

    draw_progressive_pass_map(axs[3,0], df_events, home_team_id, home_team_name, HOME_COLOR, is_away_team=False) 
    draw_progressive_pass_map(axs[3,1], df_events, away_team_id, away_team_name, AWAY_COLOR, is_away_team=True) 
    plot_recovery_turnover_map(axs[3,2], away_recovery_df, away_team_name, is_away_team=True) 

    plt.tight_layout()
    plt.subplots_adjust(top=0.94, hspace=0.3, wspace=0.15) 
    
    print(f"Saving dashboard image to {OUTPUT_DASHBOARD_PATH}...")
    plt.savefig(OUTPUT_DASHBOARD_PATH, dpi=300, bbox_inches='tight')
    print("Dashboard image saved successfully!")

if __name__ == "__main__":
    generate_dashboard()