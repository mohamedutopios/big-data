-- Keyspace simple (1 nœud)
CREATE KEYSPACE IF NOT EXISTS analytics
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'};

USE analytics;

-- Tous les événements (écriture simple)
CREATE TABLE IF NOT EXISTS events (
  event_id uuid PRIMARY KEY,
  user_id int,
  event_type text,
  price double,
  ts timestamp
);

-- CA par minute — on choisit un bucketing simple (jour) pour faciliter les lectures
-- PK = (day_bucket, window_start). On pourra filtrer sur le jour et trier par fenêtre.
CREATE TABLE IF NOT EXISTS revenue_per_minute (
  day_bucket date,
  window_start timestamp,
  window_end timestamp,
  total_revenue double,
  purchase_count int,
  PRIMARY KEY ((day_bucket), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);
