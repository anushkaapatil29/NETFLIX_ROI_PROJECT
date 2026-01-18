"""
Sensitivity analysis for attribution window sizes.
Runs attribution with windows [3,7,14] days and computes LTV:CAC for Sci-Fi and Comedy.
Writes `sensitivity_attribution_window.png` to project root.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from attribution import assign_last_touch

CONTENT_CSV = 'netflix_content.csv'
USER_CSV = 'user_base.csv'

sns.set(style='whitegrid')


def compute_genre_metrics(users, content):
    # compute ltv
    diff = (users['last_active_date'].dt.year - users['sign_up_date'].dt.year) * 12 + (users['last_active_date'].dt.month - users['sign_up_date'].dt.month)
    diff = diff.fillna(0).astype(int)
    users = users.copy()
    users['lifetime_months'] = np.maximum(1, diff)
    users['ltv'] = users['monthly_revenue'] * users['lifetime_months']

    enriched = users.merge(content[['show_id', 'genre', 'production_cost']], left_on='attributed_show_id', right_on='show_id', how='left')
    show_rev = enriched.groupby('attributed_show_id').agg(attributed_users=('user_id','count'), total_revenue=('ltv','sum')).reset_index()
    show_rev = show_rev.merge(content[['show_id','genre','production_cost']], left_on='attributed_show_id', right_on='show_id', how='left')
    genre_fin = show_rev.groupby('genre').agg(total_revenue=('total_revenue','sum'), total_prod_cost=('production_cost','sum'), total_attributed_users=('attributed_users','sum')).reset_index()
    genre_fin['cac_per_user'] = genre_fin['total_prod_cost'] / genre_fin['total_attributed_users'].replace(0, np.nan)
    genre_fin['ltv_per_user'] = genre_fin['total_revenue'] / genre_fin['total_attributed_users'].replace(0, np.nan)
    genre_fin['ltv_to_cac'] = genre_fin['ltv_per_user'] / genre_fin['cac_per_user']
    return genre_fin


def main():
    content = pd.read_csv(CONTENT_CSV, parse_dates=['release_date'])
    users = pd.read_csv(USER_CSV, parse_dates=['sign_up_date','last_active_date'])

    windows = [3,7,14]
    rows = []
    for w in windows:
        attributed = assign_last_touch(content, users.copy(), window_days=w)
        genre_fin = compute_genre_metrics(attributed, content)
        for g in ['Sci-Fi','Comedy']:
            val = genre_fin[genre_fin['genre']==g]
            if val.empty:
                rows.append({'window':w, 'genre':g, 'ltv_to_cac':np.nan})
            else:
                rows.append({'window':w, 'genre':g, 'ltv_to_cac':float(val['ltv_to_cac'].iloc[0])})

    df_plot = pd.DataFrame(rows)
    plt.figure(figsize=(8,5))
    sns.lineplot(data=df_plot, x='window', y='ltv_to_cac', hue='genre', marker='o')
    plt.title('Sensitivity: LTV:CAC vs Attribution Window (Sci-Fi vs Comedy)')
    plt.xlabel('Attribution Window (days)')
    plt.ylabel('LTV / CAC')
    plt.xticks(windows)
    plt.tight_layout()
    plt.savefig('sensitivity_attribution_window.png', dpi=150)
    print('Wrote sensitivity_attribution_window.png')


if __name__ == '__main__':
    main()
