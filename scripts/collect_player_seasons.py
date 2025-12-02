"""
NBA Player Season Data Collection Script

Collects player season statistics from 1996-97 to present for breakout prediction.
Primary metric: E_NET_RATING (Estimated Net Rating)

Output: data/raw/player_seasons_with_breakouts.csv
"""

import pandas as pd
import numpy as np
import time
import sys
from datetime import datetime
from pathlib import Path

try:
    from nba_api.stats.endpoints import (
        leaguedashplayerstats,
        playerestimatedmetrics
    )
except ImportError:
    print("ERROR: nba_api not installed. Install with: pip install nba_api")
    sys.exit(1)


def generate_season_list(start_year=1996, end_year=None):
    """Generate list of season strings (e.g., '1996-97', '1997-98', ...)."""
    if end_year is None:
        end_year = datetime.now().year

    seasons = []
    for year in range(start_year, end_year):
        season_str = f"{year}-{str(year+1)[2:]}"
        seasons.append(season_str)

    return seasons


def collect_league_stats(season, retry_count=3):
    """
    Collect league-wide player statistics for a given season.

    Returns:
        DataFrame with player stats including PTS, AST, REB, etc.
    """
    for attempt in range(retry_count):
        try:
            print(f"  Fetching league stats... (attempt {attempt + 1}/{retry_count})")

            stats = leaguedashplayerstats.LeagueDashPlayerStats(
                season=season,
                per_mode_detailed='PerGame',
                season_type_all_star='Regular Season'
            )

            df = stats.get_data_frames()[0]

            # Filter players with minimum playing time (500 minutes)
            df = df[df['MIN'] * df['GP'] >= 500].copy()

            print(f"  ✓ Got {len(df)} players with 500+ minutes")
            return df

        except Exception as e:
            print(f"  ✗ Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retry_count - 1:
                time.sleep(5 * (attempt + 1))  # Exponential backoff
            else:
                print(f"  ✗ Failed to fetch league stats for {season}")
                return None

    return None


def collect_estimated_metrics(season, retry_count=3):
    """
    Collect estimated metrics (E_NET_RATING, E_OFF_RATING, E_DEF_RATING).

    Returns:
        DataFrame with estimated metrics
    """
    for attempt in range(retry_count):
        try:
            print(f"  Fetching estimated metrics... (attempt {attempt + 1}/{retry_count})")

            metrics = playerestimatedmetrics.PlayerEstimatedMetrics(
                season=season,
                season_type='Regular Season'
            )

            df = metrics.get_data_frames()[0]

            print(f"  ✓ Got estimated metrics for {len(df)} players")
            return df

        except Exception as e:
            print(f"  ✗ Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retry_count - 1:
                time.sleep(5 * (attempt + 1))
            else:
                print(f"  ✗ Failed to fetch estimated metrics for {season}")
                return None

    return None


def merge_season_data(league_stats, estimated_metrics, season):
    """
    Merge league stats and estimated metrics into a single DataFrame.

    Returns:
        Combined DataFrame with all metrics
    """
    if league_stats is None or estimated_metrics is None:
        return None

    # Select relevant columns from league stats
    league_cols = [
        'PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'AGE', 'GP', 'W', 'L',
        'MIN', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT',
        'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'TOV', 'STL', 'BLK',
        'BLKA', 'PF', 'PFD', 'PTS', 'PLUS_MINUS'
    ]

    # Filter to columns that exist
    league_cols = [col for col in league_cols if col in league_stats.columns]
    league_subset = league_stats[league_cols].copy()

    # Select relevant columns from estimated metrics
    metrics_cols = [
        'PLAYER_ID', 'E_OFF_RATING', 'E_DEF_RATING', 'E_NET_RATING',
        'E_AST_RATIO', 'E_OREB_PCT', 'E_DREB_PCT', 'E_REB_PCT',
        'E_TOV_PCT', 'E_USG_PCT', 'E_PACE'
    ]

    # Filter to columns that exist
    metrics_cols = [col for col in metrics_cols if col in estimated_metrics.columns]
    metrics_subset = estimated_metrics[metrics_cols].copy()

    # Merge on PLAYER_ID
    merged = pd.merge(
        league_subset,
        metrics_subset,
        on='PLAYER_ID',
        how='inner'
    )

    # Add season column
    merged['SEASON'] = season

    # Calculate additional metrics
    if 'FGA' in merged.columns and 'FTA' in merged.columns and 'PTS' in merged.columns:
        # True Shooting Percentage: PTS / (2 * (FGA + 0.44 * FTA))
        merged['TS_PCT'] = merged['PTS'] / (2 * (merged['FGA'] + 0.44 * merged['FTA']))
        merged['TS_PCT'] = merged['TS_PCT'].replace([np.inf, -np.inf], np.nan)

    # Calculate experience (rough estimate based on age - 19)
    merged['EXPERIENCE'] = (merged['AGE'] - 19).clip(lower=0)

    print(f"  ✓ Merged data: {len(merged)} players")

    return merged


def collect_all_seasons(start_year=1996, end_year=None, save_progress=True):
    """
    Collect data for all seasons.

    Args:
        start_year: Starting year (default 1996)
        end_year: Ending year (default current year)
        save_progress: Save progress after each season

    Returns:
        DataFrame with all player-season data
    """
    seasons = generate_season_list(start_year, end_year)
    all_data = []

    print("="*70)
    print(f"Collecting NBA Player Season Data: {seasons[0]} to {seasons[-1]}")
    print(f"Total seasons: {len(seasons)}")
    print("="*70)

    for i, season in enumerate(seasons, 1):
        print(f"\n[{i}/{len(seasons)}] Processing season: {season}")
        print("-" * 50)

        # Collect data for this season
        league_stats = collect_league_stats(season)
        time.sleep(0.6)  # Rate limiting

        estimated_metrics = collect_estimated_metrics(season)
        time.sleep(0.6)  # Rate limiting

        # Merge data
        season_data = merge_season_data(league_stats, estimated_metrics, season)

        if season_data is not None:
            all_data.append(season_data)
            print(f"  ✓ Season {season} complete: {len(season_data)} players")

            # Save progress
            if save_progress and len(all_data) > 0:
                progress_df = pd.concat(all_data, ignore_index=True)
                progress_file = Path('data/raw/player_seasons_progress.csv')
                progress_file.parent.mkdir(parents=True, exist_ok=True)
                progress_df.to_csv(progress_file, index=False)
                print(f"  ✓ Progress saved: {len(progress_df)} total player-seasons")
        else:
            print(f"  ✗ Season {season} failed - skipping")

        # Brief pause between seasons
        time.sleep(1)

    if len(all_data) == 0:
        print("\n✗ ERROR: No data collected")
        return None

    # Combine all seasons
    combined_df = pd.concat(all_data, ignore_index=True)

    print("\n" + "="*70)
    print(f"✓ Data collection complete!")
    print(f"  Total player-seasons: {len(combined_df)}")
    print(f"  Seasons covered: {combined_df['SEASON'].nunique()}")
    print(f"  Unique players: {combined_df['PLAYER_ID'].nunique()}")
    print("="*70)

    return combined_df


def calculate_lag_features(df):
    """
    Calculate previous season statistics for each player.
    Creates lag features for trend analysis.

    Returns:
        DataFrame with lag features added
    """
    print("\nCalculating lag features (previous season stats)...")

    # Sort by player and season
    df = df.sort_values(['PLAYER_ID', 'SEASON']).copy()

    # Metrics to lag
    lag_metrics = [
        'E_NET_RATING', 'E_OFF_RATING', 'E_DEF_RATING',
        'PTS', 'AST', 'REB', 'MIN', 'GP',
        'TS_PCT', 'E_USG_PCT', 'FG_PCT', 'FG3_PCT'
    ]

    # Filter to metrics that exist
    lag_metrics = [col for col in lag_metrics if col in df.columns]

    # Create lag features
    for metric in lag_metrics:
        df[f'{metric}_PREV'] = df.groupby('PLAYER_ID')[metric].shift(1)
        df[f'{metric}_2YRS_AGO'] = df.groupby('PLAYER_ID')[metric].shift(2)

    # Calculate changes
    for metric in lag_metrics:
        if f'{metric}_PREV' in df.columns:
            df[f'{metric}_CHANGE_1YR'] = df[metric] - df[f'{metric}_PREV']

            # Growth rate (percentage change)
            with np.errstate(divide='ignore', invalid='ignore'):
                df[f'{metric}_GROWTH_RATE'] = df[f'{metric}_CHANGE_1YR'] / df[f'{metric}_PREV'].abs()
                df[f'{metric}_GROWTH_RATE'] = df[f'{metric}_GROWTH_RATE'].replace([np.inf, -np.inf], np.nan)

    print(f"✓ Lag features calculated")

    return df


def label_breakouts(df, threshold=5.0):
    """
    Label breakout seasons based on E_NET_RATING improvement.

    Args:
        df: DataFrame with lag features
        threshold: Minimum E_NET_RATING improvement to be considered breakout (default 5.0)

    Returns:
        DataFrame with breakout labels
    """
    print(f"\nLabeling breakout seasons (threshold: +{threshold} E_NET_RATING)...")

    # Define breakout based on E_NET_RATING improvement
    df['BREAKOUT'] = 0
    df['BREAKOUT_MAGNITUDE'] = 0.0

    # Only consider players with previous season data
    has_prev_data = df['E_NET_RATING_PREV'].notna()

    # Calculate breakout magnitude
    df.loc[has_prev_data, 'BREAKOUT_MAGNITUDE'] = df.loc[has_prev_data, 'E_NET_RATING_CHANGE_1YR']

    # Label breakouts
    breakout_mask = has_prev_data & (df['E_NET_RATING_CHANGE_1YR'] >= threshold)
    df.loc[breakout_mask, 'BREAKOUT'] = 1

    # Statistics
    num_breakouts = df['BREAKOUT'].sum()
    num_eligible = has_prev_data.sum()
    breakout_pct = (num_breakouts / num_eligible * 100) if num_eligible > 0 else 0

    print(f"✓ Breakouts labeled:")
    print(f"  - Total player-seasons: {len(df)}")
    print(f"  - Eligible (have previous season): {num_eligible}")
    print(f"  - Breakouts identified: {num_breakouts}")
    print(f"  - Breakout rate: {breakout_pct:.2f}%")

    if num_breakouts > 0:
        print(f"\nBreakout E_NET_RATING improvements:")
        breakout_improvements = df[df['BREAKOUT'] == 1]['E_NET_RATING_CHANGE_1YR']
        print(f"  - Min: +{breakout_improvements.min():.2f}")
        print(f"  - Max: +{breakout_improvements.max():.2f}")
        print(f"  - Mean: +{breakout_improvements.mean():.2f}")
        print(f"  - Median: +{breakout_improvements.median():.2f}")

    return df


def save_dataset(df, output_path='data/raw/player_seasons_with_breakouts.csv'):
    """Save the final dataset."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_file, index=False)

    print(f"\n✓ Dataset saved to: {output_file}")
    print(f"  - Shape: {df.shape}")
    print(f"  - Columns: {len(df.columns)}")

    return output_file


def main():
    """Main execution function."""

    print("\n" + "="*70)
    print("NBA Player Breakout Season Dataset Generator")
    print("="*70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Collect all season data
    df = collect_all_seasons(start_year=1996, end_year=None, save_progress=True)

    if df is None:
        print("\n✗ ERROR: Data collection failed")
        sys.exit(1)

    # Step 2: Calculate lag features
    df = calculate_lag_features(df)

    # Step 3: Label breakouts
    df = label_breakouts(df, threshold=5.0)

    # Step 4: Save dataset
    output_file = save_dataset(df)

    # Step 5: Summary statistics
    print("\n" + "="*70)
    print("DATASET SUMMARY")
    print("="*70)
    print(f"Total player-seasons: {len(df)}")
    print(f"Seasons covered: {df['SEASON'].min()} to {df['SEASON'].max()}")
    print(f"Unique players: {df['PLAYER_ID'].nunique()}")
    print(f"Breakouts: {df['BREAKOUT'].sum()} ({df['BREAKOUT'].sum()/len(df)*100:.2f}%)")
    print(f"\nE_NET_RATING statistics:")
    print(f"  Min: {df['E_NET_RATING'].min():.2f}")
    print(f"  Max: {df['E_NET_RATING'].max():.2f}")
    print(f"  Mean: {df['E_NET_RATING'].mean():.2f}")
    print(f"  Median: {df['E_NET_RATING'].median():.2f}")

    print(f"\nMissing data:")
    missing_pct = (df.isnull().sum() / len(df) * 100)
    print(missing_pct[missing_pct > 0].sort_values(ascending=False).head(10))

    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print("✓ Complete! Dataset ready for analysis.")
    print("="*70)


if __name__ == "__main__":
    main()
