"""
NETFLIX CONTENT ROI ANALYSIS - COMPLETE DATA PIPELINE
======================================================
This script generates all 3 CSV files needed for the project.

INSTRUCTIONS:
1. Copy this entire code into a file called: complete_pipeline.py
2. Run: python complete_pipeline.py
3. CSV files will be saved in the same folder

FILES CREATED:
- netflix_content.csv (500 shows)
- user_base.csv (10,000 users)
- user_attribution_enriched.csv (10,000 users with attribution)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

print("="*70)
print("NETFLIX CONTENT ROI ANALYSIS - DATA GENERATION PIPELINE")
print("="*70)

# Set seed for reproducibility
np.random.seed(42)

# ============================================
# STEP 1: Generate Netflix Content Dataset
# ============================================

def generate_netflix_content():
    """Generate 500 Netflix originals with realistic production costs"""
    
    genres = ['Sci-Fi', 'Comedy', 'Documentary', 'Drama', 'Thriller', 
              'Romance', 'Action', 'Horror', 'Animation', 'Reality TV']
    
    genre_weights = [0.15, 0.20, 0.10, 0.18, 0.12, 0.08, 0.10, 0.04, 0.02, 0.01]
    
    cost_ranges = {
        'Sci-Fi': (80, 200), 'Comedy': (20, 60), 'Documentary': (5, 25),
        'Drama': (40, 120), 'Thriller': (30, 90), 'Romance': (15, 50),
        'Action': (60, 150), 'Horror': (10, 40), 'Animation': (50, 100),
        'Reality TV': (3, 15)
    }
    
    show_titles = {
        'Sci-Fi': ['Quantum Paradox', 'Stellar Divide', 'Neural Gateway', 'Mars Colony', 'Synthetic Dreams'],
        'Comedy': ['Awkward Days', 'The Roommate Experiment', 'Office Politics', 'Late Night Chaos', 'Family Mishaps'],
        'Documentary': ['Ocean Secrets', 'Tech Revolution', 'Wild Earth', 'Music Legends', 'Crime Files'],
        'Drama': ['Broken Bonds', 'City Lights', 'The Last Stand', 'Family Ties', 'Power Play'],
        'Thriller': ['Dark Hours', 'Silent Witness', 'The Chase', 'Mind Games', 'Final Warning'],
        'Romance': ['Love in Paris', 'Second Chances', 'Heart Strings', 'Summer Nights', 'Perfect Match'],
        'Action': ['Strike Force', 'Urban Warriors', 'Rapid Fire', 'Code Red', 'Night Raid'],
        'Horror': ['The Haunting', 'Midnight Terror', 'Dark Shadows', 'Silent Screams', 'Evil Rising'],
        'Animation': ['Sky Adventures', 'Magic Kingdom', 'Robot Tales', 'Fantasy Quest', 'Dream World'],
        'Reality TV': ['Island Challenge', 'Love Quest', 'Talent Hunt', 'Survival Mode', 'Social Experiment']
    }
    
    data = []
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range = (end_date - start_date).days
    
    for show_id in range(1, 501):
        genre = np.random.choice(genres, p=genre_weights)
        base_titles = show_titles[genre]
        title = np.random.choice(base_titles) + f" S{np.random.randint(1, 4)}"
        
        random_days = np.random.randint(0, date_range)
        release_date = start_date + timedelta(days=random_days)
        
        cost_min, cost_max = cost_ranges[genre]
        production_cost = np.random.uniform(cost_min, cost_max) * 1_000_000
        
        data.append({
            'show_id': f'SH{show_id:04d}',
            'title': title,
            'genre': genre,
            'release_date': release_date.strftime('%Y-%m-%d'),
            'production_cost': round(production_cost, 2)
        })
    
    return pd.DataFrame(data)


# ============================================
# STEP 2: Generate User Base Dataset
# ============================================

def generate_user_base(content_df):
    """Generate 10,000 users with sign-up attribution"""
    
    data = []
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2025, 1, 15)
    date_range = (end_date - start_date).days
    
    revenue_tiers = [5.99, 9.99, 15.99, 19.99]
    tier_weights = [0.15, 0.40, 0.35, 0.10]
    
    content_df['release_datetime'] = pd.to_datetime(content_df['release_date'])
    
    for user_id in range(1, 10001):
        random_days = np.random.randint(0, date_range)
        sign_up_date = start_date + timedelta(days=random_days)
        
        # 70% attributed to shows, 30% organic
        if np.random.random() < 0.70:
            attribution_window_start = sign_up_date - timedelta(days=7)
            attribution_window_end = sign_up_date
            
            eligible_shows = content_df[
                (content_df['release_datetime'] >= attribution_window_start) &
                (content_df['release_datetime'] <= attribution_window_end)
            ]
            
            if len(eligible_shows) > 0:
                days_diff = (attribution_window_end - eligible_shows['release_datetime']).dt.days
                weights = np.exp(-days_diff / 3)
                weights = weights / weights.sum()
                attributed_show = np.random.choice(eligible_shows['show_id'].values, p=weights)
            else:
                attributed_show = None
        else:
            attributed_show = None
        
        monthly_revenue = np.random.choice(revenue_tiers, p=tier_weights)
        
        # 80% active, 20% churned
        if np.random.random() < 0.80:
            days_since_active = np.random.randint(0, 30)
            last_active_date = datetime(2025, 1, 15) - timedelta(days=days_since_active)
        else:
            # Calculate days between sign_up and current date
            max_churn_days = (datetime(2025, 1, 15) - sign_up_date).days
            # Ensure we have at least 30 days for churned users
            if max_churn_days > 30:
                churn_days = np.random.randint(30, max_churn_days)
            else:
                # If signed up recently, just set to midpoint
                churn_days = max(15, max_churn_days // 2)
            last_active_date = sign_up_date + timedelta(days=churn_days)
        
        data.append({
            'user_id': f'U{user_id:06d}',
            'sign_up_date': sign_up_date.strftime('%Y-%m-%d'),
            'last_active_date': last_active_date.strftime('%Y-%m-%d'),
            'monthly_revenue': monthly_revenue,
            'attributed_show_id': attributed_show
        })
    
    return pd.DataFrame(data)


# ============================================
# STEP 3: Apply Attribution & Calculate LTV
# ============================================

def create_attribution_enriched(user_df, content_df):
    """Create enriched dataset with attribution and LTV calculations"""
    
    user_df['sign_up_date'] = pd.to_datetime(user_df['sign_up_date'])
    user_df['last_active_date'] = pd.to_datetime(user_df['last_active_date'])
    content_df['release_date'] = pd.to_datetime(content_df['release_date'])
    
    # Merge user data with content data
    enriched = user_df.merge(
        content_df[['show_id', 'title', 'genre', 'production_cost', 'release_date']],
        left_on='attributed_show_id',
        right_on='show_id',
        how='left'
    )
    
    # Fill organic users
    enriched['genre'] = enriched['genre'].fillna('Organic')
    enriched['production_cost'] = enriched['production_cost'].fillna(0)
    
    # Calculate days since release
    enriched['days_since_release'] = (
        enriched['sign_up_date'] - enriched['release_date']
    ).dt.days
    
    # Calculate months active
    enriched['months_active'] = (
        (enriched['last_active_date'] - enriched['sign_up_date']).dt.days / 30.44
    ).round(1)
    
    # Calculate LTV
    enriched['ltv'] = (enriched['monthly_revenue'] * enriched['months_active']).round(2)
    
    # Identify churned users
    current_date = pd.Timestamp('2025-01-15')
    enriched['is_churned'] = (current_date - enriched['last_active_date']).dt.days > 30
    
    # Rename columns for clarity
    enriched = enriched.rename(columns={'title': 'show_title'})
    
    # Select final columns
    final_cols = [
        'user_id', 'sign_up_date', 'last_active_date', 'monthly_revenue',
        'attributed_show_id', 'show_title', 'genre', 'production_cost',
        'days_since_release', 'months_active', 'ltv', 'is_churned'
    ]
    
    return enriched[final_cols]


# ============================================
# EXECUTE PIPELINE
# ============================================

print("\n[1/3] Generating Netflix Content Dataset...")
netflix_content = generate_netflix_content()
print(f"      ✓ Created {len(netflix_content):,} shows")

print("\n[2/3] Generating User Base Dataset...")
user_base = generate_user_base(netflix_content)
attribution_rate = (user_base['attributed_show_id'].notna().sum() / len(user_base) * 100)
print(f"      ✓ Created {len(user_base):,} users")
print(f"      ✓ Attribution Rate: {attribution_rate:.1f}%")

print("\n[3/3] Creating Attribution Enriched Dataset...")
user_attribution_enriched = create_attribution_enriched(user_base, netflix_content)
print(f"      ✓ Enriched {len(user_attribution_enriched):,} user records")

# ============================================
# SAVE CSV FILES
# ============================================

print("\n" + "="*70)
print("SAVING CSV FILES...")
print("="*70)

netflix_content.to_csv('netflix_content.csv', index=False)
print("✓ Saved: netflix_content.csv")

user_base.to_csv('user_base.csv', index=False)
print("✓ Saved: user_base.csv")

user_attribution_enriched.to_csv('user_attribution_enriched.csv', index=False)
print("✓ Saved: user_attribution_enriched.csv")

# ============================================
# DISPLAY SUMMARY STATISTICS
# ============================================

print("\n" + "="*70)
print("DATA SUMMARY")
print("="*70)

print("\n📊 GENRE DISTRIBUTION:")
print(netflix_content['genre'].value_counts().to_string())

print("\n💰 AVERAGE LTV BY GENRE:")
ltv_summary = user_attribution_enriched[
    user_attribution_enriched['genre'] != 'Organic'
].groupby('genre')['ltv'].mean().sort_values(ascending=False)
print(ltv_summary.round(2).to_string())

print("\n🎯 TOP 5 SHOWS BY USER ACQUISITION:")
top_shows = user_attribution_enriched[
    user_attribution_enriched['attributed_show_id'].notna()
].groupby(['show_title', 'genre']).size().sort_values(ascending=False).head(5)
print(top_shows.to_string())

print("\n" + "="*70)
print("✅ PIPELINE COMPLETE - All CSV files ready for analysis!")
print("="*70)
print("\nNext Steps:")
print("1. Load 'user_attribution_enriched.csv' into your SQL database")
print("2. Run the SQL queries from Artifact 3")
print("3. Build your executive presentation")
print("\nGood luck with your Netflix application! 🚀")
print("="*70)
