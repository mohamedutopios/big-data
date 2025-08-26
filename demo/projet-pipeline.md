Parfait — voici **la variante “comme sur ton schéma”** : **Cassandra + Node.js** (visualisation) avec Spark Streaming qui lit Kafka et écrit dans Cassandra. C’est un projet complet avec **Dockerfiles + docker-compose**.

---

# 📦 Arborescence

```
pipeline-cassandra/
├─ docker-compose.yml
├─ .env
├─ generator/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ producer.py
├─ spark-app/
│  ├─ Dockerfile
│  └─ jobs/
│     └─ streaming_to_cassandra.py
├─ cassandra/
│  └─ init.cql
└─ node-app/
   ├─ Dockerfile
   ├─ package.json
   ├─ server.js
   └─ public/
      └─ index.html
```

---

# 1) `docker-compose.yml`

```yaml
version: "3.9"

services:
  redpanda:
    image: redpandadata/redpanda:latest
    command:
      - redpanda
      - start
      - --smp
      - "1"
      - --overprovisioned
      - --memory
      - 512M
      - --reserve-memory
      - 0M
      - --node-id
      - "0"
      - --check=false
      - --kafka-addr
      - PLAINTEXT://0.0.0.0:9092,OUTSIDE://0.0.0.0:19092
      - --advertise-kafka-addr
      - PLAINTEXT://redpanda:9092,OUTSIDE://localhost:19092
    ports:
      - "9092:9092"
      - "19092:19092"
      - "9644:9644"

  redpanda-console:
    image: redpandadata/console:latest
    environment:
      - KAFKA_BROKERS=redpanda:9092
    ports:
      - "8080:8080"
    depends_on:
      - redpanda

  cassandra:
    image: cassandra:4.1
    environment:
      - MAX_HEAP_SIZE=512M
      - HEAP_NEWSIZE=128M
    ports:
      - "9042:9042"
    healthcheck:
      test: ["CMD-SHELL", "cqlsh -e 'DESCRIBE KEYSPACES' || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 20

  cql-init:
    image: cassandra:4.1
    depends_on:
      cassandra:
        condition: service_healthy
    volumes:
      - ./cassandra/init.cql:/init/init.cql:ro
    entrypoint: ["/bin/bash","-lc"]
    command: >
      "cqlsh cassandra -f /init/init.cql && echo 'CQL init done'"

  spark-master:
    build:
      context: ./spark-app
      dockerfile: Dockerfile
    environment:
      - SPARK_MODE=master
      - SPARK_MASTER_HOST=spark-master
    ports:
      - "7077:7077"
      - "8081:8080"
    depends_on:
      - redpanda
      - cassandra
      - cql-init
    volumes:
      - ./spark-app/jobs:/opt/bitnami/spark/jobs:ro

  spark-worker:
    image: bitnami/spark:3.5
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
    depends_on:
      - spark-master

  spark-streaming:
    build:
      context: ./spark-app
      dockerfile: Dockerfile
    environment:
      - SPARK_MODE=client
      - KAFKA_BOOTSTRAP_SERVERS=redpanda:9092
      - TOPIC=orders
      - CASSANDRA_HOST=cassandra
      - CASSANDRA_KEYSPACE=analytics
    command: >
      bash -lc "spark-submit
      --master spark://spark-master:7077
      --packages
      org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,
      com.datastax.spark:spark-cassandra-connector_2.12:3.5.0
      /opt/bitnami/spark/jobs/streaming_to_cassandra.py"
    depends_on:
      - spark-master
      - cassandra
      - cql-init
      - redpanda
    volumes:
      - ./spark-app/jobs:/opt/bitnami/spark/jobs:ro

  generator:
    build:
      context: ./generator
      dockerfile: Dockerfile
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=redpanda:9092
      - TOPIC=orders
      - RATE_PER_SEC=5
    depends_on:
      - redpanda

  node:
    build:
      context: ./node-app
      dockerfile: Dockerfile
    environment:
      - CASSANDRA_HOST=cassandra
      - CASSANDRA_KEYSPACE=analytics
    ports:
      - "3000:3000"
    depends_on:
      - cassandra
      - cql-init

```

---

# 2) `.env` (facultatif, pas d’auth Cassandra par défaut)

```env
# vide par défaut
```

---

# 3) Cassandra – init CQL

## `cassandra/init.cql`

```sql
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
```

---

# 4) Générateur (identique à la version Postgres)

## `generator/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY producer.py .
CMD ["python", "producer.py"]
```

## `generator/requirements.txt`

```
kafka-python==2.0.2
python-dateutil==2.9.0
```

## `generator/producer.py`

```python
import os, json, random, time, uuid
from datetime import datetime, timezone
from kafka import KafkaProducer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
TOPIC = os.getenv("TOPIC", "orders")
RATE = int(os.getenv("RATE_PER_SEC", "5"))

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

event_types = ["view", "purchase"]

print(f"Producing to {TOPIC} @ {RATE}/s → {BOOTSTRAP}")
while True:
    for _ in range(RATE):
        et = random.choices(event_types, weights=[0.8, 0.2])[0]
        price = round(random.uniform(5, 200), 2) if et == "purchase" else None
        evt = {
            "event_id": str(uuid.uuid4()),
            "user_id": random.randint(1, 5000),
            "event_type": et,
            "price": price,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        producer.send(TOPIC, evt)
    producer.flush()
    time.sleep(1)
```

---

# 5) Spark

## `spark-app/Dockerfile`

```dockerfile
FROM bitnami/spark:3.5
WORKDIR /opt/bitnami/spark
COPY jobs ./jobs
```

## `spark-app/jobs/streaming_to_cassandra.py`

```python
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, to_timestamp, window,
    sum as _sum, count as _count, to_date
)
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
TOPIC = os.getenv("TOPIC", "orders")
CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "cassandra")
KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "analytics")

spark = (SparkSession.builder
         .appName("orders_stream_to_cassandra")
         .config("spark.cassandra.connection.host", CASSANDRA_HOST)
         .getOrCreate())
spark.sparkContext.setLogLevel("WARN")

schema = StructType([
    StructField("event_id", StringType()),
    StructField("user_id", IntegerType()),
    StructField("event_type", StringType()),
    StructField("price", DoubleType()),
    StructField("timestamp", StringType()),
])

# 1) Stream Kafka
raw = (spark.readStream
       .format("kafka")
       .option("kafka.bootstrap.servers", KAFKA_SERVERS)
       .option("subscribe", TOPIC)
       .option("startingOffsets", "latest")
       .load())

json_df = raw.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")
events = json_df.withColumn("ts", to_timestamp(col("timestamp"))).drop("timestamp")

# 2) Ecriture des événements bruts → table analytics.events
def write_events(batch_df, batch_id):
    (batch_df.select(
        col("event_id").cast("string").alias("event_id"),
        "user_id", "event_type", "price", "ts"
     )
     .write
     .format("org.apache.spark.sql.cassandra")
     .mode("append")
     .options(table="events", keyspace=KEYSPACE)
     .save())

q_events = (events.writeStream
            .outputMode("append")
            .foreachBatch(write_events)
            .option("checkpointLocation", "/tmp/chk/events")
            .start())

# 3) Agrégation CA / minute → table analytics.revenue_per_minute
purchases = events.where(col("event_type") == "purchase")
agg = (purchases
       .groupBy(window(col("ts"), "1 minute"))
       .agg(_sum(col("price")).alias("total_revenue"),
            _count(col("event_id")).alias("purchase_count"))
       .select(
           to_date(col("window.start")).alias("day_bucket"),
           col("window.start").alias("window_start"),
           col("window.end").alias("window_end"),
           col("total_revenue"),
           col("purchase_count")
       ))

def write_agg(batch_df, batch_id):
    (batch_df.write
     .format("org.apache.spark.sql.cassandra")
     .mode("append")
     .options(table="revenue_per_minute", keyspace=KEYSPACE)
     .save())

q_agg = (agg.writeStream
         .outputMode("update")
         .foreachBatch(write_agg)
         .option("checkpointLocation", "/tmp/chk/agg")
         .start())

spark.streams.awaitAnyTermination()
```

---

# 6) Node.js (visualisation simple)

## `node-app/Dockerfile`

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json .
RUN npm install --omit=dev
COPY server.js ./server.js
COPY public ./public
EXPOSE 3000
CMD ["node","server.js"]
```

## `node-app/package.json`

```json
{
  "name": "analytics-dashboard",
  "version": "1.0.0",
  "description": "Minimal dashboard over Cassandra data",
  "main": "server.js",
  "license": "MIT",
  "dependencies": {
    "cassandra-driver": "^4.7.2",
    "express": "^4.19.2"
  }
}
```

## `node-app/server.js`

```js
const express = require("express");
const cassandra = require("cassandra-driver");

const app = express();
app.use(express.static("public"));

const host = process.env.CASSANDRA_HOST || "cassandra";
const keyspace = process.env.CASSANDRA_KEYSPACE || "analytics";

const client = new cassandra.Client({
  contactPoints: [host],
  localDataCenter: "datacenter1",
  keyspace
});

app.get("/api/revenue", async (_, res) => {
  try {
    // On récupère les dernières 120 fenêtres (tri côté Node si besoin)
    const query = `
      SELECT day_bucket, window_start, window_end, total_revenue, purchase_count
      FROM revenue_per_minute
      WHERE day_bucket = toDate(now())
      LIMIT 500;
    `;
    const result = await client.execute(query);
    const rows = result.rows
      .sort((a,b) => new Date(a.window_start) - new Date(b.window_start));
    res.json(rows);
  } catch (e) {
    console.error(e);
    res.status(500).json({error: "query_failed"});
  }
});

app.listen(3000, () => console.log("Dashboard: http://localhost:3000"));
```

## `node-app/public/index.html`

```html
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8"/>
  <title>Dashboard - CA par minute</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: system-ui, Arial, sans-serif; margin: 24px; }
    h1 { margin: 0 0 12px; }
    #wrap { max-width: 900px; }
    .meta { color:#555; margin-bottom:12px; }
  </style>
</head>
<body>
  <div id="wrap">
    <h1>CA par minute</h1>
    <div class="meta">Source : Cassandra (analytics.revenue_per_minute)</div>
    <canvas id="chart" height="100"></canvas>
  </div>

  <script>
    async function load() {
      const res = await fetch("/api/revenue");
      const data = await res.json();
      const labels = data.map(r => new Date(r.window_start).toLocaleTimeString());
      const revenue = data.map(r => r.total_revenue);

      const ctx = document.getElementById('chart').getContext('2d');
      new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [{ label: '€ / minute', data: revenue, fill: false, tension: 0.2 }]
        },
        options: {
          responsive: true,
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    }
    load();
  </script>
</body>
</html>
```

---

# 7) Lancer la démo

```bash
cd pipeline-cassandra
docker compose up -d --build
# attendre 60–90 s (Cassandra + init)
docker compose ps
docker compose logs -f spark-streaming
```

* **Redpanda Console** : [http://localhost:8080](http://localhost:8080) (topic `orders`)
* **Dashboard Node** : [http://localhost:3000](http://localhost:3000) (courbe du **CA par minute**)

Requête manuelle (optionnel) :

```bash
docker compose exec cassandra cqlsh -e "SELECT * FROM analytics.revenue_per_minute LIMIT 5;"
```

Arrêt & reset :

```bash
docker compose down -v
```

---

## 🔎 Ce que la démo montre (pedago débutant)

* **Ingestion** : événements JSON simulés → bus Kafka-compatible (Redpanda).
* **Traitement** : filtrage des achats + **agrégation par minute** (compte + somme).
* **Stockage** : tables Cassandra adaptées à la **lecture par jour** (bucketing).
* **Visualisation** : petite app Node/Express + **Chart.js**.

Si tu veux, je peux te déposer **les deux projets** (Postgres/Metabase **et** Cassandra/Node) fusionnés dans un **mono-repo** avec deux fichiers `docker-compose` et un README unique.
