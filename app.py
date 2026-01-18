"""
Streamlit demo app for Content ROI exploration.

Run with:
    pip install streamlit
    streamlit run app.py

Features:
- select attribution window (3/7/14 days)
- choose genre to filter
- view static charts and numeric summary
"""
import streamlit as st
import pandas as pd
import numpy as np
from attribution import assign_last_touch

st.set_page_config(layout='wide', page_title='Content ROI Explorer')

CONTENT_CSV = 'netflix_content.csv'
USER_CSV = 'user_base.csv'

@st.cache_data
def load_data():
    content = pd.read_csv(CONTENT_CSV, parse_dates=['release_date'])
    users = pd.read_csv(USER_CSV, parse_dates=['sign_up_date','last_active_date'])
    return content, users

content, users = load_data()

st.title('Content ROI — Interactive Explorer')

col1, col2 = st.columns([1,3])
with col1:
    window = st.selectbox('Attribution window (days)', options=[3,7,14], index=1)
    genre = st.selectbox('Genre (All)', options=['All'] + sorted(content['genre'].unique().tolist()))

with col2:
    st.markdown('''
    Use the controls to recompute attribution and view LTV / ROI for selected genres.
    ''')

attributed = assign_last_touch(content, users.copy(), window_days=window)

# compute ltv
diff = (attributed['last_active_date'].dt.year - attributed['sign_up_date'].dt.year) * 12 + (attributed['last_active_date'].dt.month - attributed['sign_up_date'].dt.month)
diff = diff.fillna(0).astype(int)
attributed['lifetime_months'] = np.maximum(1, diff)
attributed['ltv'] = attributed['monthly_revenue'] * attributed['lifetime_months']

enriched = attributed.merge(content[['show_id','genre','production_cost']], left_on='attributed_show_id', right_on='show_id', how='left')

if genre != 'All':
    enriched = enriched[enriched['genre'] == genre]

st.subheader('Summary metrics')
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric('Attributed Users', int(enriched['user_id'].nunique()))
with col_b:
    st.metric('Avg LTV', f"${enriched['ltv'].mean():.2f}")
with col_c:
    st.metric('Total Revenue', f"${enriched['ltv'].sum():.0f}")

st.subheader('Top shows by attributed revenue')
show_rev = enriched.groupby('attributed_show_id').agg(attributed_users=('user_id','count'), total_revenue=('ltv','sum')).reset_index()
show_rev = show_rev.merge(content[['show_id','title','genre','production_cost']], left_on='attributed_show_id', right_on='show_id', how='left')
st.dataframe(show_rev.sort_values('total_revenue', ascending=False).head(10))

st.info('This is a lightweight demo: for production use, add auth, better caching, and pagination.')
