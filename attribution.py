"""
Last-Touch Attribution script.
Reads `netflix_content.csv` and `user_base.csv`, assigns attributed_show_id to users whose sign_up_date
is within 7 days after a show's release_date (last-touch: the latest such release wins).
Writes `user_attribution_enriched.csv` with the attributed_show_id populated.

Usage: python attribution.py
"""
import pandas as pd
import numpy as np
from datetime import timedelta

CONTENT_CSV = 'netflix_content.csv'
USER_CSV = 'user_base.csv'
OUTPUT_CSV = 'user_attribution_enriched.csv'

WINDOW_DAYS = 7  # attribution window after release_date


def load_data():
    content = pd.read_csv(CONTENT_CSV, parse_dates=['release_date'])
    users = pd.read_csv(USER_CSV, parse_dates=['sign_up_date', 'last_active_date'])
    return content, users


def assign_last_touch(content: pd.DataFrame, users: pd.DataFrame, window_days: int = WINDOW_DAYS) -> pd.DataFrame:
    # Prepare content: keep only show_id and release_date for speed; sort by release_date
    content_small = content[['show_id', 'release_date']].sort_values('release_date')

    # For each user, find shows whose release_date is within WINDOW_DAYS before or equal to sign_up_date
    # We'll perform a join-like approach by expanding content window for vectorized operations

    # Create windows for content
    content_small['window_start'] = content_small['release_date']
    content_small['window_end'] = content_small['release_date'] + pd.Timedelta(days=int(window_days))

    # To avoid an explicit O(N*M) loop, we'll perform a merge where sign_up_date between release and window_end
    # Merge: cross-join by date ranges via an interval join approach. For modest data sizes this is fine.
    users_exp = users[['user_id', 'sign_up_date']].copy()
    users_exp['key'] = 1
    content_small['key'] = 1

    merged = users_exp.merge(content_small, on='key').drop(columns=['key'])

    # Filter rows where sign_up_date is within [release_date, release_date + WINDOW]
    cond = (merged['sign_up_date'] >= merged['release_date']) & (merged['sign_up_date'] <= merged['window_end'])
    merged = merged[cond].copy()

    if merged.empty:
        # No matches
        users['attributed_show_id'] = None
        return users

    # For last-touch, pick the show with the latest release_date for each user
    merged.sort_values(['user_id', 'release_date'], inplace=True)
    last_touch = merged.groupby('user_id', as_index=False).last()[['user_id', 'show_id']]
    last_touch.rename(columns={'show_id': 'attributed_show_id'}, inplace=True)

    # Ensure users has an attributed_show_id column (may be missing)
    if 'attributed_show_id' not in users.columns:
        users['attributed_show_id'] = None

    # Merge back into users, keep existing column and new attribution with suffix
    users = users.merge(last_touch, on='user_id', how='left', suffixes=('', '_new'))

    # Coalesce: prefer the new attribution if present, otherwise keep existing
    if 'attributed_show_id_new' in users.columns:
        users['attributed_show_id'] = users['attributed_show_id_new'].where(pd.notnull(users['attributed_show_id_new']), users['attributed_show_id'])
        users.drop(columns=['attributed_show_id_new'], inplace=True)

    # Normalize missing values to None
    users['attributed_show_id'] = users['attributed_show_id'].where(pd.notnull(users['attributed_show_id']), None)

    return users


if __name__ == '__main__':
    content_df, users_df = load_data()
    enriched = assign_last_touch(content_df, users_df)
    enriched.to_csv(OUTPUT_CSV, index=False)
    print(f"Wrote enriched user data with attribution to {OUTPUT_CSV}")
