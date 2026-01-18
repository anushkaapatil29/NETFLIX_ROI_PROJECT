"""
Simple analysis and plotting for the synthetic Content ROI project.
Reads: netflix_content.csv, user_attribution_enriched.csv (or user_base.csv if enrichment not run)
Outputs: textual summaries to stdout and two PNG charts:
 - avg_ltv_by_genre.png
 - ltv_cac_sci_fi_comedy.png

Usage: python analysis_and_plots.py
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

PLOTS_DIR = 'plots'

os.makedirs(PLOTS_DIR, exist_ok=True)

CONTENT_CSV = 'netflix_content.csv'
USER_ATTR_CSV = 'user_attribution_enriched.csv'
USER_CSV = 'user_base.csv'

sns.set(style='whitegrid')


def load_users():
    try:
        users = pd.read_csv(USER_ATTR_CSV, parse_dates=['sign_up_date', 'last_active_date'])
        print(f"Loaded enriched users from {USER_ATTR_CSV}")
    except Exception:
        users = pd.read_csv(USER_CSV, parse_dates=['sign_up_date', 'last_active_date'])
        print(f"Loaded base users from {USER_CSV} (no enrichment found)")
    return users


def compute_ltv(users):
    # lifetime months (floor to integer months) at least 1
    # compute month difference as year*12 + months
    diff = (users['last_active_date'].dt.year - users['sign_up_date'].dt.year) * 12 + (users['last_active_date'].dt.month - users['sign_up_date'].dt.month)
    diff = diff.fillna(0).astype(int)
    lifetime_months = np.maximum(1, diff)
    users = users.copy()
    users['lifetime_months'] = lifetime_months
    users['ltv'] = users['monthly_revenue'] * users['lifetime_months']
    return users


def main():
    content = pd.read_csv(CONTENT_CSV, parse_dates=['release_date'])
    users = load_users()

    print('\nSample content (first 5 rows):')
    print(content.head().to_string(index=False))

    print('\nSample users (first 5 rows):')
    print(users.head().to_string(index=False))

    users = compute_ltv(users)

    # Join to get genre for attributed users
    enriched = users.merge(content[['show_id', 'genre', 'production_cost']], left_on='attributed_show_id', right_on='show_id', how='left')

    # LTV by genre
    ltv_by_genre = enriched.groupby('genre').agg(
        attributed_users=('user_id', 'count'),
        avg_ltv=('ltv', 'mean'),
        total_ltv=('ltv', 'sum')
    ).reset_index().sort_values('avg_ltv', ascending=False)

    print('\nLTV by Genre (top rows):')
    print(ltv_by_genre.head(10).to_string(index=False, float_format='%.2f'))

    # Compute per-show revenue from attributed users
    show_rev = enriched.groupby('attributed_show_id').agg(
        attributed_users=('user_id', 'count'),
        total_revenue=('ltv', 'sum')
    ).reset_index()
    show_rev = show_rev.merge(content[['show_id', 'title', 'genre', 'production_cost']], left_on='attributed_show_id', right_on='show_id', how='left')
    show_rev['roi'] = (show_rev['total_revenue'] - show_rev['production_cost']) / show_rev['production_cost']

    print('\nTop 5 shows by ROI:')
    top_roi = show_rev.sort_values('roi', ascending=False).head(5)
    print(top_roi[['show_id', 'title', 'genre', 'production_cost', 'attributed_users', 'total_revenue', 'roi']].to_string(index=False, float_format='%.2f'))

    # Plot: avg LTV by genre (only genres with at least 5 attributed users for clarity)
    plot_data = ltv_by_genre[ltv_by_genre['attributed_users'] >= 5].copy()
    plt.figure(figsize=(12,8))
    # color-blind friendly palette
    sns.set_palette('colorblind')
    ax = sns.barplot(data=plot_data, x='avg_ltv', y='genre')
    plt.title('Average LTV by Genre (attributed users only)')
    plt.xlabel('Average LTV (USD)')
    plt.ylabel('Genre')
    # Annotate bars
    for p in ax.patches:
        width = p.get_width()
        ax.text(width + 1, p.get_y() + p.get_height() / 2, f"{width:.0f}", va='center')
    plt.tight_layout()
    outpath = os.path.join(PLOTS_DIR, 'avg_ltv_by_genre.png')
    plt.savefig(outpath, dpi=200)
    print(f"\nWrote chart: {outpath}")

    # Compute LTV:CAC for Sci-Fi vs Comedy
    # CAC approximated as production_cost / attributed users per show; aggregate to genre level
    genre_fin = show_rev.groupby('genre').agg(
        total_revenue=('total_revenue', 'sum'),
        total_prod_cost=('production_cost', 'sum'),
        total_attributed_users=('attributed_users', 'sum')
    ).reset_index()
    genre_fin['cac_per_user'] = genre_fin['total_prod_cost'] / genre_fin['total_attributed_users'].replace(0, np.nan)
    genre_fin['ltv_per_user'] = genre_fin['total_revenue'] / genre_fin['total_attributed_users'].replace(0, np.nan)
    genre_fin['ltv_to_cac'] = genre_fin['ltv_per_user'] / genre_fin['cac_per_user']

    print('\nGenre financials (Sci-Fi and Comedy):')
    print(genre_fin[genre_fin['genre'].isin(['Sci-Fi', 'Comedy'])].to_string(index=False, float_format='%.2f'))

    # Plot LTV:CAC for Sci-Fi and Comedy
    plot_gc = genre_fin[genre_fin['genre'].isin(['Sci-Fi', 'Comedy'])].copy()
    if not plot_gc.empty:
        plt.figure(figsize=(6,4))
        sns.set_palette('colorblind')
        ax2 = sns.barplot(data=plot_gc, x='genre', y='ltv_to_cac')
        plt.title('LTV to CAC Ratio: Sci-Fi vs Comedy')
        plt.ylabel('LTV / CAC')
        plt.xlabel('Genre')
        for p in ax2.patches:
            ax2.text(p.get_x() + p.get_width() / 2, p.get_height() + 0.01, f"{p.get_height():.2f}", ha='center')
        plt.tight_layout()
        out2 = os.path.join(PLOTS_DIR, 'ltv_cac_sci_fi_comedy.png')
        plt.savefig(out2, dpi=200)
        print(f'Wrote chart: {out2}')
    else:
        print('Not enough data for Sci-Fi vs Comedy LTV:CAC plot')

    print('\nAnalysis complete. Charts saved to project root.')

if __name__ == '__main__':
    main()
