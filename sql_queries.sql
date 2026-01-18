-- SQL queries for Content ROI project (PostgreSQL-compatible)
-- Assumptions:
--  - Table `netflix_content` has columns (show_id, title, genre, release_date, production_cost)
--  - Table `user_base` has columns (user_id, sign_up_date, last_active_date, monthly_revenue, attributed_show_id)
--  - Dates are stored as DATE or TIMESTAMP (queries use DATE_TRUNC/::date accordingly)

-- 1) Monthly Churn Rate
-- Definition: For each month (calendar month), churn_rate = users_lost / users_at_start
-- users_at_start: users who were active on the first day of the month
-- users_lost: users who were active on the first day but whose last_active_date < first_day_of_next_month

WITH months AS (
  SELECT generate_series(
    (SELECT date_trunc('month', min(sign_up_date)) FROM user_base),
    (SELECT date_trunc('month', max(last_active_date)) FROM user_base),
    interval '1 month'
  )::date as month_start
),
user_status AS (
  SELECT
    u.user_id,
    u.sign_up_date::date AS sign_up_date,
    u.last_active_date::date AS last_active_date
  FROM user_base u
)
SELECT
  m.month_start,
  m.month_start + interval '1 month' - interval '1 day' AS month_end,
  -- users active at start: sign_up_date <= month_start AND last_active_date >= month_start
  (SELECT count(*) FROM user_status us WHERE us.sign_up_date <= m.month_start AND us.last_active_date >= m.month_start) AS users_at_start,
  -- users lost during month: active at start but last_active_date < first_day_of_next_month
  (SELECT count(*) FROM user_status us WHERE us.sign_up_date <= m.month_start AND us.last_active_date >= m.month_start AND us.last_active_date < (m.month_start + interval '1 month')) AS users_lost,
  CASE WHEN (SELECT count(*) FROM user_status us WHERE us.sign_up_date <= m.month_start AND us.last_active_date >= m.month_start) = 0
       THEN NULL
       ELSE ROUND( ( (SELECT count(*) FROM user_status us WHERE us.sign_up_date <= m.month_start AND us.last_active_date >= m.month_start AND us.last_active_date < (m.month_start + interval '1 month'))::numeric
                    / (SELECT count(*) FROM user_status us WHERE us.sign_up_date <= m.month_start AND us.last_active_date >= m.month_start)::numeric )::numeric, 4)
  END AS churn_rate
FROM months m
ORDER BY m.month_start;


-- 2) LTV by Genre
-- Define lifetime months ~= number of full months between sign_up_date and last_active_date, minimum 1
-- Lifetime value per user = monthly_revenue * lifetime_months

WITH user_ltv AS (
  SELECT
    user_id,
    monthly_revenue,
    sign_up_date::date AS sign_up_date,
    last_active_date::date AS last_active_date,
    GREATEST(1, DATE_PART('year', age(last_active_date::date, sign_up_date::date)) * 12 + DATE_PART('month', age(last_active_date::date, sign_up_date::date)))::int AS lifetime_months,
    (monthly_revenue * GREATEST(1, DATE_PART('year', age(last_active_date::date, sign_up_date::date)) * 12 + DATE_PART('month', age(last_active_date::date, sign_up_date::date))))::numeric AS lifetime_value,
    attributed_show_id
  FROM user_base
)
SELECT
  c.genre,
  COUNT(u.user_id) AS attributed_users,
  ROUND(AVG(u.lifetime_value)::numeric, 2) AS avg_ltv,
  ROUND(SUM(u.lifetime_value)::numeric, 2) AS total_revenue_from_attributed_users
FROM user_ltv u
LEFT JOIN netflix_content c ON u.attributed_show_id = c.show_id
GROUP BY c.genre
ORDER BY avg_ltv DESC NULLS LAST;


-- 3) Content ROI (per show and aggregated by genre)
-- ROI = (Total Revenue from Attributed Users - Production Cost) / Production Cost

WITH user_ltv AS (
  SELECT
    user_id,
    attributed_show_id,
    (monthly_revenue * GREATEST(1, DATE_PART('year', age(last_active_date::date, sign_up_date::date)) * 12 + DATE_PART('month', age(last_active_date::date, sign_up_date::date))))::numeric AS lifetime_value
  FROM user_base
),
show_revenue AS (
  SELECT
    c.show_id,
    c.title,
    c.genre,
    c.production_cost,
    COALESCE(SUM(u.lifetime_value), 0) AS total_revenue
  FROM netflix_content c
  LEFT JOIN user_ltv u ON u.attributed_show_id = c.show_id
  GROUP BY c.show_id, c.title, c.genre, c.production_cost
)
SELECT
  show_id,
  title,
  genre,
  production_cost,
  total_revenue,
  CASE WHEN production_cost = 0 THEN NULL ELSE ROUND( (total_revenue - production_cost)::numeric / production_cost::numeric, 4) END AS roi
FROM show_revenue
ORDER BY roi DESC NULLS LAST;

-- Aggregated ROI by genre
SELECT
  genre,
  SUM(total_revenue) AS total_revenue_by_genre,
  SUM(production_cost) AS total_prod_cost_by_genre,
  CASE WHEN SUM(production_cost) = 0 THEN NULL ELSE ROUND( (SUM(total_revenue) - SUM(production_cost))::numeric / SUM(production_cost)::numeric, 4) END AS genre_roi
FROM (
  SELECT genre, production_cost, total_revenue FROM (
    SELECT c.genre, c.production_cost, COALESCE(SUM(u.monthly_revenue * GREATEST(1, DATE_PART('year', age(u.last_active_date::date, u.sign_up_date::date)) * 12 + DATE_PART('month', age(u.last_active_date::date, u.sign_up_date::date)))),0) AS total_revenue
    FROM netflix_content c
    LEFT JOIN user_base u ON u.attributed_show_id = c.show_id
    GROUP BY c.show_id, c.genre, c.production_cost
  ) t
) s
GROUP BY genre
ORDER BY genre_roi DESC NULLS LAST;
