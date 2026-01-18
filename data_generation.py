"""
Generate synthetic datasets for the 'Content ROI' portfolio project.
Creates:
 - netflix_content.csv (500 rows): show_id, title, genre, release_date, production_cost
 - user_base.csv (10_000 rows): user_id, sign_up_date, last_active_date, monthly_revenue, attributed_show_id (empty)

Usage: run this file with Python 3.8+ installed. It uses pandas and numpy.
"""
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

NUM_SHOWS = 500
NUM_USERS = 10_000

GENRES = [
    'Sci-Fi', 'Comedy', 'Documentary', 'Drama', 'Thriller', 'Romance', 'Animation', 'Horror'
]

# Helper to random date between two dates
def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

def generate_netflix_content(path='netflix_content.csv'):
    shows = []
    start_release = datetime(2017, 1, 1)
    end_release = datetime(2025, 12, 31)

    for i in range(1, NUM_SHOWS + 1):
        show_id = f"show_{i:04d}"
        genre = np.random.choice(GENRES, p=[0.15, 0.18, 0.10, 0.20, 0.12, 0.12, 0.08, 0.05])
        # Titles: synthetic but human-readable
        title = f"{genre[:3].upper()} Series {i}"
        release_date = random_date(start_release, end_release).date()
        # Production cost by genre and randomness (in USD)
        base_cost = {
            'Sci-Fi': 30_000_000,
            'Comedy': 5_000_000,
            'Documentary': 1_000_000,
            'Drama': 10_000_000,
            'Thriller': 12_000_000,
            'Romance': 4_000_000,
            'Animation': 18_000_000,
            'Horror': 3_000_000,
        }[genre]
        production_cost = int(np.round(np.random.normal(base_cost, base_cost * 0.25)))
        production_cost = max(100_000, production_cost)

        shows.append({
            'show_id': show_id,
            'title': title,
            'genre': genre,
            'release_date': release_date,
            'production_cost': production_cost,
        })

    df = pd.DataFrame(shows)
    df = df.sort_values('release_date').reset_index(drop=True)
    df.to_csv(path, index=False)
    print(f"Wrote {len(df)} shows to {path}")
    return df


def generate_user_base(content_df, path='user_base.csv'):
    users = []
    first_signup = datetime(2017, 1, 1)
    last_signup = datetime(2025, 12, 31)

    # To allow realistic attribution, bias some signups near releases
    release_dates = pd.to_datetime(content_df['release_date']).dt.date.tolist()

    for i in range(1, NUM_USERS + 1):
        user_id = f"user_{i:05d}"
        # Mix: 70% organic uniform signups, 30% signups near a random release (to create attribution signal)
        if random.random() < 0.30:
            show_release = random.choice(release_dates)
            # sign up within +/- 3 days of release to simulate campaign effect
            delta_days = np.random.randint(-3, 4)
            sign_up_date = show_release + timedelta(days=int(delta_days))
        else:
            sign_up_date = random_date(first_signup, last_signup).date()

        # last_active_date at or after sign_up_date (users may churn quickly or stay long)
        # active period: 0 to 48 months roughly
        months_active = np.random.poisson(6)  # mean ~6 months
        last_active = (pd.to_datetime(sign_up_date) + pd.DateOffset(months=int(months_active))).date()
        # monthly revenue: many users on low plans, a few high spenders
        monthly_revenue = float(round(np.random.exponential(8.0) + 6.0, 2))  # average around $14

        users.append({
            'user_id': user_id,
            'sign_up_date': sign_up_date,
            'last_active_date': last_active,
            'monthly_revenue': monthly_revenue,
            'attributed_show_id': None,
        })

    df = pd.DataFrame(users)
    df.to_csv(path, index=False)
    print(f"Wrote {len(df)} users to {path}")
    return df


if __name__ == '__main__':
    content_df = generate_netflix_content()
    user_df = generate_user_base(content_df)
    print('Data generation complete. Files: netflix_content.csv, user_base.csv')
