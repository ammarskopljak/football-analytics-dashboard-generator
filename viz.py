import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as patheffects
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from scipy.ndimage import gaussian_filter1d
from mplsoccer import Pitch

BG_COLOR = '#0C0D0E'
LINE_COLOR = 'white'
HOME_COLOR = '#43A1D5'
AWAY_COLOR = '#FF4C4C'

def plot_enhanced_network(ax, passes_df, avg_locs, pass_combinations, team_metrics, team_name, color, is_home, bg_color=BG_COLOR):
    pitch = Pitch(pitch_type='statsbomb', line_color=LINE_COLOR, pitch_color=bg_color, linewidth=1)
    pitch.draw(ax=ax)
    ax.set_xlim(0, 120); ax.set_ylim(0, 80); ax.set_facecolor(bg_color)

    if not is_home:
        avg_locs = avg_locs.copy(); avg_locs['x_avg'] = 120 - avg_locs['x_avg']; avg_locs['y_avg'] = 80 - avg_locs['y_avg']

    combinations = pass_combinations.merge(
        avg_locs[['x_avg', 'y_avg']], left_on='pos_min', right_index=True
    ).merge(
        avg_locs[['x_avg', 'y_avg']], left_on='pos_max', right_index=True, suffixes=['', '_end']
    )
    
    if len(combinations) > 0:
        max_passes = combinations['pass_count'].max()
        combinations['line_width'] = (combinations['pass_count'] / max_passes) * 10 
        combinations['alpha'] = 0.3 + (combinations['pass_count'] / max_passes) * 0.6
        
        for _, row in combinations.iterrows():
            pitch.lines(row['x_avg'], row['y_avg'], row['x_avg_end'], row['y_avg_end'],
                        lw=row['line_width'], color=color, alpha=row['alpha'], ax=ax, zorder=1)

    for player_id, row in avg_locs.iterrows():
        marker = 'o' if row['isFirstEleven'] else 's'
        pitch.scatter(row['x_avg'], row['y_avg'], s=1000, marker=marker, 
                      color=LINE_COLOR, edgecolors=color, linewidth=2.5, ax=ax, zorder=3)
        ax.text(row['x_avg'], row['y_avg'], str(row['shirtNo']),
                ha='center', va='center', fontsize=12, color=color, weight='bold', 
                path_effects=[patheffects.withStroke(linewidth=2, foreground=LINE_COLOR)], zorder=4)

    team_median_disp = team_metrics['team_median']
    if not is_home:
        team_median_disp = 120 - team_metrics['team_median']
    
    ax.axvline(x=team_median_disp, color='lightgray', linestyle='--', alpha=0.8, linewidth=1.5, zorder=2)
    ax.text(10 if is_home else 110, 75, f"Median X: {team_metrics['team_median']:.1f}m", 
            fontsize=9, ha='left' if is_home else 'right', color=LINE_COLOR)

    ax.set_title(f"{team_name} - Passing Network", fontsize=13, color=LINE_COLOR, pad=10)

def defensive_block(ax, team_positions: dict, team_actions: pd.DataFrame, team_name: str, team_color: str, is_away_team: bool = False):
    pitch = Pitch(pitch_type='statsbomb', pitch_color=BG_COLOR, line_color=LINE_COLOR, linewidth=1.5, line_zorder=2, corner_arcs=True) 
    pitch.draw(ax=ax); ax.set_facecolor(BG_COLOR); ax.set_xlim(-0.5, 120.5); ax.set_ylim(-0.5, 80.5)
    
    if len(team_positions) == 0 or len(team_actions) == 0:
        ax.set_title(f"{team_name}\nDefensive Action Heatmap (No Data)", color=LINE_COLOR, fontsize=12); return {} 

    positions_df = pd.DataFrame.from_dict(team_positions, orient='index')
    
    if is_away_team: 
        ax.invert_xaxis(); ax.invert_yaxis()

    flamingo_cmap = LinearSegmentedColormap.from_list("Team colors", [BG_COLOR, team_color], N=500)
    pitch.kdeplot(team_actions['x_sb'], team_actions['y_sb'], ax=ax, fill=True, levels=5000, thresh=0.02, cut=4, cmap=flamingo_cmap)
    
    dah = round(positions_df['x'].median(), 2)
    center_backs = positions_df[positions_df['position'] == 'DC']
    def_line_h = round(center_backs['x'].median(), 2) if len(center_backs) > 0 else dah
    starters = positions_df[positions_df['is_starter'] == True]
    fwd_line_h = round(starters.nlargest(2, 'x')['x'].mean(), 2) if len(starters) >= 2 else dah
    compactness = round((1 - ((fwd_line_h - def_line_h) / 120)) * 100, 2)

    dah_plot = dah
    if is_away_team:
        dah_plot = 120 - dah
        
    ax.axvline(x=dah_plot, color='gray', linestyle='--', alpha=0.75, linewidth=1.5, zorder=2) 
    
    MAX_MARKER_SIZE = 3500
    positions_df['marker_size'] = (positions_df['action_count'] / positions_df['action_count'].max()) * 2500 
    
    for idx, row in positions_df.iterrows():
        x_plot = row['x']; y_plot = row['y']
        
        if is_away_team: 
            x_plot = 120 - x_plot; y_plot = 80 - y_plot

        marker = 'o' if row['is_starter'] else 's'
        pitch.scatter(x_plot, y_plot, s=row['marker_size'] + 50, marker=marker, color=BG_COLOR, edgecolor=LINE_COLOR, linewidth=1.5, alpha=1, zorder=3) 
        pitch.annotate(str(row['shirtNo']), xy=(x_plot, y_plot), c=LINE_COLOR, ha='center', va='center', size=10, ax=ax) 
        
    ax.text(dah_plot - 1 if not is_away_team else dah_plot + 1, -3 if not is_away_team else 78, f"DAH: {round(dah * 1.2, 2)}m", fontsize=8, color=LINE_COLOR, ha='right' if not is_away_team else 'left', va='center') 
    ax.text(120 if not is_away_team else 0, -3 if not is_away_team else 78, f'Compact:{compactness}%', fontsize=8, color=LINE_COLOR, ha='right' if not is_away_team else 'left', va='center') 

    ax.set_title(f"{team_name}\nDefensive Action Heatmap", color=LINE_COLOR, fontsize=12, fontweight='bold')

    return {'Average_Defensive_Action_Height': dah, 'Compactness': compactness}

def draw_progressive_pass_map(ax, df_events, team_id, team_name, team_color, is_away_team=False):
    
    dfpro = df_events[
        (df_events['team_id'] == team_id) &
        (df_events['type_display_name'] == 'Pass') &
        (df_events['outcome_type_display_name'] == 'Successful') &
        (~df_events['qualifiers'].astype(str).str.contains('CornerTaken|Freekick', na=False)) &
        (df_events['x'] >= 35) &
        (df_events['prog_pass'] >= 9.11)
    ].copy()
    
    dfpro['x_sb'] = dfpro['x'] * 1.2
    dfpro['y_sb'] = dfpro['y'] * 0.8
    dfpro['end_x_sb'] = dfpro['end_x'] * 1.2
    dfpro['end_y_sb'] = dfpro['end_y'] * 0.8

    pitch = Pitch(pitch_type='statsbomb', pitch_color=BG_COLOR, line_color=LINE_COLOR, linewidth=1.5, line_zorder=2, corner_arcs=True) 
    pitch.draw(ax=ax); ax.set_facecolor(BG_COLOR); ax.set_xlim(-0.5, 120.5); ax.set_ylim(-0.5, 80.5)
    
    if is_away_team:
        ax.invert_xaxis(); ax.invert_yaxis()
        dfpro['x_sb'], dfpro['end_x_sb'] = 120 - dfpro['x_sb'], 120 - dfpro['end_x_sb']
        dfpro['y_sb'], dfpro['end_y_sb'] = 80 - dfpro['y_sb'], 80 - dfpro['end_y_sb']

    pro_count = len(dfpro)
    
    if pro_count > 0:
        ax.hlines(26.67, xmin=0, xmax=120, colors=LINE_COLOR, linestyle='dashed', alpha=0.35)
        ax.hlines(53.33, xmin=0, xmax=120, colors=LINE_COLOR, linestyle='dashed', alpha=0.35)
        
        label_x = 8 if not is_away_team else 120 - 8
        bbox_props = dict(boxstyle="round,pad=0.3", edgecolor="None", facecolor=BG_COLOR, alpha=0.75)
        ax.text(label_x, 40, f'{pro_count}', color=team_color, fontsize=12, va='center', ha='center', bbox=bbox_props, weight='bold') 

        pitch.lines(dfpro['x_sb'], dfpro['y_sb'], dfpro['end_x_sb'], dfpro['end_y_sb'],
                    lw=2.5, comet=True, color=team_color, ax=ax, alpha=0.5) 
        pitch.scatter(dfpro['end_x_sb'], dfpro['end_y_sb'], s=25, edgecolor=team_color, linewidth=1, facecolor=BG_COLOR, zorder=2, ax=ax) 
    
    ax.set_title(f"{team_name}\n{pro_count} Progressive Passes", color=LINE_COLOR, fontsize=12, fontweight='bold')
    
    return {'Total_Progressive_Passes': pro_count}

def plot_xt_momentum_subplot(ax, df_events, xT_grid, team_id_to_name, home_team_id, away_team_id):
    ax.set_facecolor(BG_COLOR)
    
    df = df_events.copy()
    df['x'] *= 1.2; df['y'] *= 0.8; df['end_x'] *= 1.2; df['end_y'] *= 0.8
    df_xT = df[(df['type_display_name'].isin(['Pass', 'Carry'])) & (df['outcome_type_display_name'] == 'Successful')].copy()

    if len(df_xT) == 0:
        ax.text(0.5, 0.5, 'No xT data available', transform=ax.transAxes, ha='center', va='center', color=LINE_COLOR, fontsize=10); return 

    n_rows, n_cols = xT_grid.shape
    def get_bin(val, max_val, n_bins):
        val = max(0, min(val, max_val)); return min(int(val / max_val * n_bins), n_bins - 1)
    df_xT['xT'] = df_xT.apply(lambda row: xT_grid[get_bin(row['end_y'], 80, n_rows), get_bin(row['end_x'], 120, n_cols)] - xT_grid[get_bin(row['y'], 80, n_rows), get_bin(row['x'], 120, n_cols)], axis=1)
    df_xT['xT_clipped'] = np.clip(df_xT['xT'], 0, 0.1)
    df_xT['team'] = df_xT['team_id'].map(team_id_to_name)
    max_xT_per_minute = df_xT.groupby(['team', 'minute'])['xT_clipped'].max().reset_index()
    minutes = sorted(max_xT_per_minute['minute'].unique())
    teams = [team_id_to_name[home_team_id], team_id_to_name[away_team_id]]
    
    window_size, decay_rate = 4, 0.25
    weighted_xT_sum = {team: [] for team in teams}; momentum = []
    for current_minute in minutes:
        for team in teams:
            recent_xT = max_xT_per_minute[(max_xT_per_minute['team'] == team) & (max_xT_per_minute['minute'] <= current_minute) & (max_xT_per_minute['minute'] > current_minute - window_size)]
            weights = np.exp(-decay_rate * (current_minute - recent_xT['minute'].values))
            weighted_sum = np.sum(weights * recent_xT['xT_clipped'].values)
            weighted_xT_sum[team].append(weighted_sum)
        momentum.append(weighted_xT_sum[teams[0]][-1] - weighted_xT_sum[teams[1]][-1])

    momentum_smoothed = gaussian_filter1d(momentum, sigma=1.0)
    ax.plot(minutes, momentum_smoothed, color=LINE_COLOR, linewidth=1.5) 
    ax.axhline(0, color=LINE_COLOR, linestyle='--', linewidth=1, alpha=0.7)
    ax.fill_between(minutes, momentum_smoothed, where=(np.array(momentum_smoothed) > 0), color=HOME_COLOR, alpha=0.5, interpolate=True)
    ax.fill_between(minutes, momentum_smoothed, where=(np.array(momentum_smoothed) < 0), color=AWAY_COLOR, alpha=0.5, interpolate=True)

    ax.text(2, 0.06, team_id_to_name[home_team_id], fontsize=10, ha='left', va='center', color=HOME_COLOR, fontweight='bold') 
    ax.text(2, -0.06, team_id_to_name[away_team_id], fontsize=10, ha='left', va='center', color=AWAY_COLOR, fontweight='bold') 
    ax.set_xlabel('Minute', color=LINE_COLOR, fontsize=9, fontweight='bold') 
    ax.set_title('xT Momentum', color=LINE_COLOR, fontsize=12, fontweight='bold') 
    ax.tick_params(colors=LINE_COLOR, axis='y', left=False, right=False, labelleft=False)
    ax.set_xticks([0, 45, 90]) 
    for spine in ax.spines.values(): spine.set_color(LINE_COLOR)
    ax.margins(x=0); ax.set_ylim(min(-0.08, np.min(momentum_smoothed) * 1.2), max(0.08, np.max(momentum_smoothed) * 1.2))

def plot_match_stats_subplot(ax, stats, home_team_name, away_team_name):
    """Plots match statistics comparison using horizontal bars."""
    ax.set_facecolor(BG_COLOR); ax.axis('off')
    
    stat_keys = list(stats.keys())
    categories = stat_keys
    y_positions = np.linspace(0.85, 0.15, len(categories))
    
    for i, category in enumerate(categories):
        stat_data = stats[category]
        home_val = stat_data.get('home', 0)
        away_val = stat_data.get('away', 0)
        
        total = home_val + away_val
        home_width = (home_val / total) * 0.35 if total > 0 else 0.1
        away_width = (away_val / total) * 0.35 if total > 0 else 0.1

        ax.barh(y_positions[i], home_width, left=0.5-home_width, height=0.04, color=HOME_COLOR, alpha=0.8) 
        ax.barh(y_positions[i], away_width, left=0.5, height=0.04, color=AWAY_COLOR, alpha=0.8) 

        ax.text(0.2, y_positions[i], f'{home_val}', ha='center', va='center', color=LINE_COLOR, fontsize=9, weight='bold') 
        ax.text(0.8, y_positions[i], f'{away_val}', ha='center', va='center', color=LINE_COLOR, fontsize=9, weight='bold') 
        ax.text(0.5, y_positions[i], category, ha='center', va='center', color=LINE_COLOR, fontsize=8, weight='bold') 
        
    ax.text(0.2, 0.95, home_team_name, ha='center', va='center', color=HOME_COLOR, fontsize=12, weight='bold') 
    ax.text(0.8, 0.95, away_team_name, ha='center', va='center', color=AWAY_COLOR, fontsize=12, weight='bold') 
    ax.set_title('Key Match Stats', fontsize=12, color=LINE_COLOR, weight='bold') 
    
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)


def plot_half_pass_density(ax, df_passes, team_name, team_color, is_away_team=False):
    pitch = Pitch(pitch_type='statsbomb', pitch_color=BG_COLOR, line_color=LINE_COLOR, linewidth=1.5)
    pitch.draw(ax=ax)
    ax.set_facecolor(BG_COLOR)
    
    if not is_away_team:
        ax.set_xlim(60, 120)
        ax.set_ylim(0, 80)
    else:
        ax.set_xlim(0, 60)
        ax.set_ylim(0, 80)
        ax.invert_xaxis()
        ax.invert_yaxis()
        
    ax.set_title(f"{team_name} - Opponent Half Passing Flow", fontsize=12, color=LINE_COLOR, fontweight='bold')
    
    plot_df = df_passes.copy()
    
    if len(plot_df) == 0:
        ax.text(90, 40, "No passes in opponent's half.", ha='center', va='center', color='gray', fontsize=10)
        return

    pitch.lines(plot_df['x'], plot_df['y'], plot_df['end_x'], plot_df['end_y'],
                ax=ax, 
                lw=1.0, 
                color=team_color, 
                alpha=0.6,
                zorder=1)
                
    pitch.scatter(plot_df['end_x'], plot_df['end_y'],
                  ax=ax, 
                  s=30, 
                  marker='o', 
                  color='white', 
                  edgecolors=team_color, 
                  linewidth=1, 
                  zorder=2)
    
    ax.text(115 if not is_away_team else 5, 75, f"Pass Count: {len(plot_df)}", 
            color=LINE_COLOR, fontsize=10, ha='right' if not is_away_team else 'left')

def plot_recovery_turnover_map(ax, df_actions, team_name, is_away_team=False):
    pitch = Pitch(pitch_type='statsbomb', pitch_color=BG_COLOR, line_color=LINE_COLOR, linewidth=1.5)
    pitch.draw(ax=ax)
    ax.set_facecolor(BG_COLOR)
    ax.set_title(f"{team_name} - Ball Recovery vs Turnover Zones", fontsize=12, color=LINE_COLOR, fontweight='bold')
    
    if is_away_team:
        ax.invert_xaxis()
        ax.invert_yaxis()

    df_rec = df_actions[df_actions['action_type'] == 'Recovery']
    df_turn = df_actions[df_actions['action_type'] == 'Turnover']
    
    if len(df_actions) > 10:
         pitch.kdeplot(df_actions['x_sb'], df_actions['y_sb'], ax=ax, fill=True, levels=10, 
                       cmap=LinearSegmentedColormap.from_list("ActionDensity", [BG_COLOR, 'gray'], N=100),
                       zorder=0, alpha=0.3)
    
    pitch.scatter(df_rec['x_sb'], df_rec['y_sb'], ax=ax,
                  marker='D', 
                  s=50, 
                  color='lightgreen', 
                  edgecolor='none', 
                  alpha=0.6, 
                  zorder=1)

    pitch.scatter(df_turn['x_sb'], df_turn['y_sb'], ax=ax,
                  marker='x', 
                  s=70, 
                  linewidth=1.5,
                  color='red', 
                  alpha=0.7, 
                  zorder=1)
    
    ax.text(10 if not is_away_team else 110, 75, 
            f"Recoveries (Win): {len(df_rec)}\nTurnovers (Loss): {len(df_turn)}", 
            fontsize=9, color=LINE_COLOR, ha='left' if not is_away_team else 'right')