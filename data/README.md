# NBA Player Breakout Season Dataset

## Overview

This dataset contains **9,752 player-seasons** from **1996-97 to 2024-25** for predicting NBA player breakout seasons using machine learning.

**Generated:** December 1, 2025
**Source:** NBA.com via `nba_api` package
**Primary Metric:** E_NET_RATING (Estimated Net Rating)

## Files

### Raw Data
- **`player_seasons_with_breakouts.csv`** (9,752 rows × 92 columns)
  - Complete dataset with all features, lag variables, and breakout labels
  - Ready for modeling and analysis

- **`player_seasons_progress.csv`**
  - Intermediate file saved during collection
  - Can be used for debugging or resuming interrupted collections

### Logs
- **`collection_log.txt`**
  - Full log of data collection process
  - Useful for troubleshooting and validation

## Dataset Statistics

| Metric | Value |
|--------|-------|
| Total Player-Seasons | 9,752 |
| Seasons Covered | 29 (1996-97 to 2024-25) |
| Unique Players | 1,738 |
| Breakout Seasons | 1,551 (15.90%) |
| Features | 92 |
| Minimum Playing Time | 500+ minutes per season |

## Breakout Definition

A **breakout season** is defined as:
- E_NET_RATING improvement of **+5.0 or more** from previous season
- Only players with previous season data are eligible

**Breakout Statistics:**
- Eligible player-seasons: 8,014 (82.2%)
- Breakouts identified: 1,551
- Breakout rate among eligible: **19.35%**
- Mean improvement: +8.59 E_NET_RATING
- Median improvement: +7.80 E_NET_RATING
- Range: +5.00 to +26.00

## Feature Categories

### 1. Basic Information (6 features)
- `PLAYER_ID`: Unique NBA player identifier
- `PLAYER_NAME`: Player full name
- `SEASON`: Season string (e.g., "2023-24")
- `TEAM_ABBREVIATION`: Team 3-letter code
- `AGE`: Player age during season
- `EXPERIENCE`: Estimated years in NBA (age - 19)

### 2. Playing Time & Games (6 features)
- `GP`: Games played
- `W`: Wins
- `L`: Losses
- `MIN`: Minutes per game
- Previous season values: `GP_PREV`, `MIN_PREV`

### 3. Shooting Statistics (12 features)
- `FGM`, `FGA`, `FG_PCT`: Field goals made/attempted/percentage
- `FG3M`, `FG3A`, `FG3_PCT`: Three-pointers made/attempted/percentage
- `FTM`, `FTA`, `FT_PCT`: Free throws made/attempted/percentage
- `TS_PCT`: True Shooting Percentage (calculated)

### 4. Traditional Stats (9 features)
- `OREB`, `DREB`, `REB`: Offensive/defensive/total rebounds
- `AST`: Assists
- `TOV`: Turnovers
- `STL`: Steals
- `BLK`: Blocks
- `PF`: Personal fouls
- `PTS`: Points per game

### 5. Advanced Stats (11 features)
- `E_NET_RATING`: **Estimated Net Rating (primary metric)**
- `E_OFF_RATING`: Estimated Offensive Rating
- `E_DEF_RATING`: Estimated Defensive Rating
- `E_AST_RATIO`: Estimated Assist Ratio
- `E_OREB_PCT`, `E_DREB_PCT`, `E_REB_PCT`: Rebound percentages
- `E_TOV_PCT`: Turnover percentage
- `E_USG_PCT`: Usage percentage
- `E_PACE`: Estimated Pace
- `PLUS_MINUS`: Plus/Minus

### 6. Lag Features - Previous Season (40+ features)
All major metrics have previous season values with `_PREV` suffix:
- `E_NET_RATING_PREV`, `PTS_PREV`, `AST_PREV`, etc.
- Enables trend analysis and year-over-year comparisons

### 7. Lag Features - 2 Years Ago (10 features)
Key metrics from 2 seasons ago with `_2YRS_AGO` suffix:
- `E_NET_RATING_2YRS_AGO`, `PTS_2YRS_AGO`, etc.
- ~32% missing (expected for players with <3 seasons)

### 8. Change Features (24 features)
Year-over-year changes with `_CHANGE_1YR` suffix:
- Example: `E_NET_RATING_CHANGE_1YR` = Current - Previous
- Critical for identifying improvement trends

### 9. Growth Rate Features (12 features)
Percentage changes with `_GROWTH_RATE` suffix:
- Example: `E_NET_RATING_GROWTH_RATE` = Change / Previous
- Normalized changes for fair comparison

### 10. Target Variables (2 features)
- **`BREAKOUT`**: Binary label (0 = no breakout, 1 = breakout)
- **`BREAKOUT_MAGNITUDE`**: Continuous E_NET_RATING change

## E_NET_RATING Explanation

**E_NET_RATING** (Estimated Net Rating) measures a player's point differential impact per 100 possessions.

**Interpretation:**
- **+10 to +20**: Elite/MVP level
- **+5 to +10**: All-Star level
- **-2 to +5**: Average starter
- **< -2**: Below average

**Dataset Range:**
- Minimum: -22.10
- Maximum: +18.90
- Mean: -0.39
- Median: -0.30

## Missing Data

Missing data is minimal and expected:

| Feature Type | Missing % | Reason |
|-------------|-----------|---------|
| 2-year lag features | ~32% | Players with <3 seasons |
| Growth rates | Variable | Division by zero cases |
| All other features | <1% | Complete data |

## Data Quality

### Filters Applied
1. **Minimum playing time**: 500+ minutes per season
   - Excludes rarely-used bench players
   - Ensures statistical reliability

2. **Complete season data**: Both league stats and estimated metrics required
   - All seasons successfully collected

### Data Validation
- All 29 seasons collected without failures
- No duplicate player-seasons
- E_NET_RATING values within expected range
- Breakout labels validated against threshold

## Usage Examples

### Load Dataset
```python
import pandas as pd

df = pd.read_csv('data/raw/player_seasons_with_breakouts.csv')
print(f"Loaded {len(df)} player-seasons")
```

### Filter for Modeling
```python
# Get players with previous season data (eligible for breakout)
modeling_df = df[df['E_NET_RATING_PREV'].notna()].copy()
print(f"Eligible for modeling: {len(modeling_df)} player-seasons")
print(f"Breakouts: {modeling_df['BREAKOUT'].sum()} ({modeling_df['BREAKOUT'].mean()*100:.1f}%)")
```

### Explore Breakouts
```python
# View players with biggest breakouts
breakouts = df[df['BREAKOUT'] == 1].copy()
breakouts = breakouts.sort_values('BREAKOUT_MAGNITUDE', ascending=False)

print("Top 10 Breakout Seasons:")
print(breakouts[['PLAYER_NAME', 'SEASON', 'E_NET_RATING',
                  'E_NET_RATING_PREV', 'BREAKOUT_MAGNITUDE']].head(10))
```

### Calculate Additional Features
```python
# Age-based features
df['is_breakout_age'] = ((df['AGE'] >= 21) & (df['AGE'] <= 26)).astype(int)
df['is_breakout_year'] = ((df['EXPERIENCE'] >= 2) & (df['EXPERIENCE'] <= 5)).astype(int)

# Efficiency trends
df['efficiency_improving'] = (df['TS_PCT'] > df['TS_PCT_PREV']).astype(int)
df['usage_increasing'] = (df['E_USG_PCT'] > df['E_USG_PCT_PREV']).astype(int)
```

## Modeling Considerations

### Train/Test Split
- **Use time-based splits**: Train on earlier seasons, test on later
- **Don't shuffle randomly**: Would leak future information
- **Suggested split**: Train on 1996-2020, validate on 2021-2023, test on 2024-25

### Class Imbalance
- Breakouts: ~19% of eligible players
- **Recommended approaches:**
  - Use class weights in model
  - SMOTE oversampling
  - Stratified sampling
  - Evaluate with ROC-AUC, PR-AUC (not accuracy)

### Feature Selection
**Most Important Features (Expected):**
1. Year-over-year change features (`*_CHANGE_1YR`)
2. Growth rate features (`*_GROWTH_RATE`)
3. Age and experience
4. Minutes per game trends
5. Efficiency metrics (TS_PCT, E_USG_PCT)

### Missing Data Handling
- 2-year lag features: Impute with 0 or use indicator variable
- Growth rates: Replace inf/-inf with large values or cap
- Most models (XGBoost, Random Forest) handle missing data well

---

**Dataset Version:** 1.0
**Last Updated:** December 1, 2025
**Status:** Ready for modeling
