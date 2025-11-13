import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from nba_api.stats.endpoints import playergamelog, leaguedashplayerstats
from nba_api.stats.static import players, teams
import os
import warnings
warnings.filterwarnings('ignore')

sns.set_style("whitegrid")

os.makedirs('visualizations', exist_ok=True)

player_stats = leaguedashplayerstats.LeagueDashPlayerStats(
    season='2023-24',
    per_mode_detailed='PerGame',
    season_type_all_star='Regular Season'
)
df_season = player_stats.get_data_frames()[0]

# Get top 30 scorers
top_scorers = df_season.nlargest(30, 'PTS')[['PLAYER_ID', 'PLAYER_NAME', 'PTS']].copy()

all_games = []

for idx, player in top_scorers.iterrows():
    try:
        player_id = player['PLAYER_ID']
        player_name = player['PLAYER_NAME']

        gamelog = playergamelog.PlayerGameLog(
            player_id=player_id,
            season='2023-24',
            season_type_all_star='Regular Season'
        )

        df_games = gamelog.get_data_frames()[0]
        df_games['PLAYER_NAME'] = player_name
        all_games.append(df_games)

    except Exception as e:
        continue

df_all_games = pd.concat(all_games, ignore_index=True)

# Add home/away indicator
df_all_games['IS_HOME'] = df_all_games['MATCHUP'].str.contains('vs.').astype(int)
df_all_games['LOCATION'] = df_all_games['IS_HOME'].map({1: 'Home', 0: 'Away'})

# Add win indicator
df_all_games['WIN'] = (df_all_games['WL'] == 'W').astype(int)

# Visualization 1: Home vs Away Points
fig, ax = plt.subplots(figsize=(10, 6))

home_away_pts = df_all_games.groupby('LOCATION')['PTS'].agg(['mean', 'std', 'count']).reset_index()

colors = ['#2196F3', '#FF9800']
bars = ax.bar(home_away_pts['LOCATION'], home_away_pts['mean'],
              color=colors, alpha=0.7, edgecolor='black', linewidth=2)

ax.set_ylabel('Average Points Per Game', fontsize=13, fontweight='bold')
ax.set_xlabel('Location', fontsize=13, fontweight='bold')
ax.set_title('Home vs Away: Player Scoring Performance', fontsize=15, fontweight='bold')

# Add value labels
for i, row in home_away_pts.iterrows():
    ax.text(i, row['mean'] + 0.5, f"{row['mean']:.2f} PPG",
            ha='center', va='bottom', fontweight='bold', fontsize=12)
    ax.text(i, row['mean']/2, f"n={int(row['count'])}\ngames",
            ha='center', va='center', fontsize=10, style='italic')

ax.set_ylim([0, max(home_away_pts['mean']) * 1.15])

plt.tight_layout()
plt.savefig('visualizations/home_away_points.png', dpi=300, bbox_inches='tight')
plt.close()

# Visualization 2: Home vs Away Win Rate
win_stats = df_all_games.groupby('LOCATION').agg({
    'WIN': ['sum', 'count', 'mean']
}).round(3)

win_stats.columns = ['Wins', 'Games', 'Win_Rate']

fig, ax = plt.subplots(figsize=(10, 6))

locations = win_stats.index
win_rates = win_stats['Win_Rate'] * 100

bars = ax.bar(locations, win_rates, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
ax.set_ylabel('Win Rate (%)', fontsize=13, fontweight='bold')
ax.set_xlabel('Location', fontsize=13, fontweight='bold')
ax.set_title('Win Rate: Home vs Away', fontsize=15, fontweight='bold')
ax.set_ylim([0, 100])

for i, (loc, rate) in enumerate(zip(locations, win_rates)):
    wins = int(win_stats.loc[loc, 'Wins'])
    losses = int(win_stats.loc[loc, 'Games'] - win_stats.loc[loc, 'Wins'])
    ax.text(i, rate + 3, f'{rate:.1f}%\n({wins}W-{losses}L)',
            ha='center', fontweight='bold', fontsize=12)

plt.tight_layout()

plt.savefig('visualizations/home_away_wins.png', dpi=300, bbox_inches='tight')
plt.close()
