import numpy as np
import pandas as pd

def prepare_enhanced_passes(df_events):
    passes = df_events[
        (df_events['type_display_name'] == 'Pass') &
        (df_events['outcome_type_display_name'] == 'Successful')
    ].copy()

    passes['x'] = passes['x'] * 1.2
    passes['y'] = passes['y'] * 0.8
    passes['end_x'] = passes['end_x'] * 1.2
    passes['end_y'] = passes['end_y'] * 0.8

    passes['pass_angle'] = np.degrees(np.arctan2(passes['end_y'] - passes['y'], passes['end_x'] - passes['x']))
    passes['pass_angle_abs'] = np.abs(passes['pass_angle'])
    
    passes['receiver'] = passes['player_id'].shift(-1).astype('Int64')
    
    return passes

def get_pass_combinations(passes_df, team_id):
    team_passes = passes_df[passes_df['team_id'] == team_id].copy()
    
    team_passes = team_passes[team_passes['receiver'].notna() & team_passes['player_id'].notna()]

    team_passes['pos_min'] = team_passes[['player_id', 'receiver']].min(axis=1)
    team_passes['pos_max'] = team_passes[['player_id', 'receiver']].max(axis=1)
    
    pass_combinations = team_passes.groupby(['pos_min', 'pos_max']).size().reset_index(name='pass_count')
    
    return pass_combinations

def get_enhanced_positions(passes_df, team_id, team_players, player_names_dict):
    team_passes = passes_df[passes_df['team_id'] == team_id]
    
    avg_locs = team_passes.groupby('player_id').agg({
        'x': 'median',  
        'y': 'median',  
        'player_id': 'count'
    }).rename(columns={'x': 'x_avg', 'y': 'y_avg', 'player_id': 'pass_count'})
    
    player_info = {}
    for player in team_players:
        player_id = player['playerId']
        player_info[player_id] = {
            'name': player_names_dict.get(str(player_id), player['name']),
            'shirtNo': player['shirtNo'],
            'position': player['position'],
            'isFirstEleven': player.get('isFirstEleven', False)
        }
        
    player_df = pd.DataFrame.from_dict(player_info, orient='index')
    avg_locs = avg_locs.join(player_df)
    
    return avg_locs[avg_locs['isFirstEleven'] == True] 

def calculate_team_metrics(passes_df, avg_locs, team_id):
    team_passes = passes_df[passes_df['team_id'] == team_id]
    
    valid_passes = team_passes[(team_passes['pass_angle_abs'] >= 0) & (team_passes['pass_angle_abs'] <= 90)]
    median_angle = valid_passes['pass_angle_abs'].median()
    verticality = round((1 - median_angle/90) * 100, 2)
    
    team_median = avg_locs['x_avg'].median()
    
    center_backs = avg_locs[avg_locs['position'] == 'DC']
    defense_line = center_backs['x_avg'].median() if len(center_backs) > 0 else avg_locs['x_avg'].min()

    attackers = avg_locs[avg_locs['position'].isin(['FW', 'AMC', 'AML', 'AMR'])]
    forward_line = attackers['x_avg'].mean() if len(attackers) > 0 else avg_locs['x_avg'].max()
    
    return {
        'verticality': verticality,
        'defense_line': defense_line,
        'forward_line': forward_line,
        'team_median': team_median
    }

def get_enhanced_positions_all(passes_df, team_id, team_players, player_names_dict):
    team_passes = passes_df[passes_df['team_id'] == team_id]
    
    avg_locs = team_passes.groupby('player_id').agg({
        'x': 'median',  
        'y': 'median',  
        'player_id': 'count'
    }).rename(columns={'x': 'x_avg', 'y': 'y_avg', 'player_id': 'pass_count'})
    
    player_info = {}
    for player in team_players:
        player_id = player['playerId']
        player_info[player_id] = {
            'name': player_names_dict.get(str(player_id), player['name']),
            'shirtNo': player['shirtNo'],
            'position': player['position'],
            'isFirstEleven': player.get('isFirstEleven', False)
        }
        
    player_df = pd.DataFrame.from_dict(player_info, orient='index')
    avg_locs = avg_locs.join(player_df)
    
    return avg_locs[avg_locs['pass_count'] > 0]


def calculate_team_metrics_all(passes_df, avg_locs_all, team_id):
    team_passes = passes_df[passes_df['team_id'] == team_id]
    
    valid_passes = team_passes[(team_passes['pass_angle_abs'] >= 0) & (team_passes['pass_angle_abs'] <= 90)]
    median_angle = valid_passes['pass_angle_abs'].median()
    verticality = round((1 - median_angle/90) * 100, 2)
    
    team_median = avg_locs_all['x_avg'].median()
    
    defense_line = avg_locs_all['x_avg'].min() 
    forward_line = avg_locs_all['x_avg'].max()
    
    return {
        'verticality': verticality,
        'defense_line': defense_line,
        'forward_line': forward_line,
        'team_median': team_median
    }

def filter_defensive_actions(df_events: pd.DataFrame) -> pd.DataFrame:
    defensive_types = ['Tackle', 'Interception', 'BallRecovery', 'BlockedPass', 'Challenge', 'Clearance', 'Foul', 'Aerial']
    
    defensive_actions = df_events[df_events['type_display_name'].isin(defensive_types)].copy()
    
    defensive_actions['x_sb'] = defensive_actions['x'] * 1.2
    defensive_actions['y_sb'] = defensive_actions['y'] * 0.8
    
    return defensive_actions

def calculate_player_defensive_positions(defensive_actions: pd.DataFrame, team_id: int, team_players: list) -> dict:
    team_actions = defensive_actions[defensive_actions['team_id'] == team_id]
    if len(team_actions) == 0: return {}
    
    player_info = {p['playerId']: {'name': p['name'], 'position': p['position'], 
                                   'shirtNo': p['shirtNo'], 
                                   'is_starter': p.get('isFirstEleven', False)} for p in team_players}
    
    player_stats = (
        team_actions.groupby('player_id')
        .agg({'x_sb': 'median', 'y_sb': 'median', 'id': 'count'})
        .rename(columns={'id': 'action_count'})
    )
    
    positions = {}
    for player_id, stats in player_stats.iterrows():
        if player_id in player_info and player_info[player_id]['is_starter']:
            positions[player_id] = {
                'x': stats['x_sb'],
                'y': stats['y_sb'],
                'action_count': stats['action_count'],
                **player_info[player_id]
            }
    return positions

def calculate_match_stats(df, hteam_id, ateam_id):
    stats = {}
    
    home_passes = df[(df['team_id'] == hteam_id) & (df['type_display_name'] == 'Pass')]
    away_passes = df[(df['team_id'] == ateam_id) & (df['type_display_name'] == 'Pass')] 
    total_passes = len(home_passes) + len(away_passes)
    stats['Possession'] = {'home': round((len(home_passes) / total_passes) * 100, 2) if total_passes else 0,
                           'away': round((len(away_passes) / total_passes) * 100, 2) if total_passes else 0}
    
    home_touches = df[(df['team_id'] == hteam_id) & (df['is_touch'] == True) & (df['x'] >= 70)]
    away_touches = df[(df['team_id'] == ateam_id) & (df['is_touch'] == True) & (df['x'] >= 70)] 
    total_touches = len(home_touches) + len(away_touches)
    stats['Field Tilt'] = {'home': round((len(home_touches) / total_touches) * 100, 2) if total_touches else 0,
                           'away': round((len(away_touches) / total_touches) * 100, 2) if total_touches else 0}
    
    home_def_actions = df[(df['team_id'] == hteam_id) & (df['type_display_name'].isin(['Interception', 'Tackle', 'Foul', 'Challenge'])) & (df['x'] > 35)]
    away_def_actions = df[(df['team_id'] == ateam_id) & (df['type_display_name'].isin(['Interception', 'Tackle', 'Foul', 'Challenge'])) & (df['x'] > 35)]
    home_passes_ppda = df[(df['team_id'] == hteam_id) & (df['type_display_name'] == 'Pass') & (df['outcome_type_display_name'] == 'Successful') & (df['x'] < 70)]
    away_passes_ppda = df[(df['team_id'] == ateam_id) & (df['type_display_name'] == 'Pass') & (df['outcome_type_display_name'] == 'Successful') & (df['x'] < 70)]
    
    stats['PPDA'] = {'home': round(len(away_passes_ppda) / len(home_def_actions), 2) if len(home_def_actions) > 0 else 0,
                     'away': round(len(home_passes_ppda) / len(away_def_actions), 2) if len(away_def_actions) > 0 else 0}

    stats['Tackles (Wins)'] = {'home': len(df[(df['team_id'] == hteam_id) & (df['type_display_name'] == 'Tackle') & (df['outcome_type_display_name'] == 'Successful')]),
                               'away': len(df[(df['team_id'] == ateam_id) & (df['type_display_name'] == 'Tackle') & (df['outcome_type_display_name'] == 'Successful')])}
    stats['Interceptions'] = {'home': len(df[(df['team_id'] == hteam_id) & (df['type_display_name'] == 'Interception')]),
                              'away': len(df[(df['team_id'] == ateam_id) & (df['type_display_name'] == 'Interception')])}
    stats['Clearance'] = {'home': len(df[(df['team_id'] == hteam_id) & (df['type_display_name'] == 'Clearance')]),
                          'away': len(df[(df['team_id'] == ateam_id) & (df['type_display_name'] == 'Clearance')])}
    stats['Aerials (Wins)'] = {'home': len(df[(df['team_id'] == hteam_id) & (df['type_display_name'] == 'Aerial') & (df['outcome_type_display_name'] == 'Successful')]),
                               'away': len(df[(df['team_id'] == ateam_id) & (df['type_display_name'] == 'Aerial') & (df['outcome_type_display_name'] == 'Successful')])}
    return stats

def get_half_pass_map(df_events: pd.DataFrame, team_id: int):
    passes_df = prepare_enhanced_passes(df_events)
    team_passes = passes_df[passes_df['team_id'] == team_id].copy()
    attacking_half_passes = team_passes[(team_passes['x'] >= 60) & (team_passes['end_x'] >= 60)].copy()
    total_passes = len(attacking_half_passes)
    if total_passes > 0:
        plot_df = attacking_half_passes[['x', 'y', 'end_x', 'end_y', 'minute']].copy()
    else:
        plot_df = pd.DataFrame(columns=['x', 'y', 'end_x', 'end_y', 'minute'])
    return plot_df, {}

def get_ball_recovery_turnover(df_events: pd.DataFrame, team_id: int):
    recoveries = df_events[
        (df_events['team_id'] == team_id) & 
        (df_events['type_display_name'].isin(['BallRecovery', 'Interception', 'Tackle'])) &
        (df_events['outcome_type_display_name'] == 'Successful')
    ].copy()
    turnovers = df_events[
        (df_events['team_id'] == team_id) & 
        (
            (df_events['type_display_name'].isin(['Pass', 'Dribble', 'Challenge']) & (df_events['outcome_type_display_name'] == 'Unsuccessful')) |
            (df_events['type_display_name'] == 'Foul') 
        )
    ].copy()
    recoveries['x_sb'] = recoveries['x'] * 1.2; recoveries['y_sb'] = recoveries['y'] * 0.8; recoveries['action_type'] = 'Recovery'
    turnovers['x_sb'] = turnovers['x'] * 1.2; turnovers['y_sb'] = turnovers['y'] * 0.8; turnovers['action_type'] = 'Turnover'
    plot_df = pd.concat([recoveries[['x_sb', 'y_sb', 'action_type', 'minute']], turnovers[['x_sb', 'y_sb', 'action_type', 'minute']]])
    return plot_df