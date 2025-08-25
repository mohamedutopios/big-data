parfait — voici un module **très bien découpé**, avec **explications, choix d’architecture, schémas ASCII, données d’exemple, métriques, pseudo-code et snippets**. Tu peux l’intégrer tel quel dans ton support et t’en servir pour une démo live.

---

# 🧪 Cas d’usage concrets & démonstrations

## 1) Détection de fraude bancaire en temps réel

### 🎯 Objectif métier

Réduire les pertes liées à la fraude **sans bloquer** les clients légitimes (équilibre entre **rappel** et **faux positifs**), décision < **50 ms**.

### 🔗 Sources & schéma minimal d’événement (Kafka `transactions`)

* **Key** = `transaction_id`
* **Value (JSON/Avro)** :

```json
{
  "transaction_id":"tx_987654",
  "timestamp":"2025-08-16T12:00:05Z",
  "account_id":"acc_123",
  "card_hash":"4a1f...ed",
  "amount": 249.90,
  "currency":"EUR",
  "merchant_id":"m_445",
  "merchant_category":"electronics",
  "channel":"ecom",
  "country":"FR",
  "device_id":"dvc_771",
  "ip":"83.12.45.21",
  "lat":48.85, "lon":2.35
}
```

### 🧱 Architecture logique

```
[Apps/Terminals] → Kafka (transactions) → Stream compute (Flink/Spark)
                                  │                  │
                                  │                  ├─> Online features (Redis/Feature Store)
                                  │                  ├─> Model Serving (REST/gRPC, <20ms)
                                  │                  └─> Decision Engine (rules + score)
                                  └─> Object Storage (S3/ADLS) → Training (batch) → Registry (MLflow)
```

### 🛠️ Features critiques (fenêtres & graphes)

* **Vélocité par carte / device / IP** (1min/5min/1h): `count_tx_1m`, `sum_amount_5m`, `uniq_merchant_1h`
* **Dérive géographique**: distance (Haversine) vs dernière transaction, `km_per_min`
* **Profil temporel**: z-score montant vs moyenne 7j (`(amount - mean_7d)/std_7d`)
* **Risque marchand**: fréquence fraude historique par `merchant_id` ou `MCC`
* **Graph features** (si dispo): communs `device_id` ↔ `account_id` ↔ `ip` (communautés anormales)

**Exemple calcul pas-à-pas (z-score)**
Moyenne 7j = 60 €, écart-type 7j = 40 €. Nouvelle transaction = 249,90 €
`z = (249,90 - 60) / 40 = 4,75` → anomalie forte.

### 🤖 Modèles & décision

* **Temps réel**: Gradient Boosted Trees / XGBoost / LightGBM (robuste, rapide) + **règles explicites** (cap sur montant, pays blacklistés, 3D Secure manqué…).
* **Anomalie**: Isolation Forest / Autoencoder (détection zero-day).
* **Décision**: `ALLOW` si score<0.5 ; `CHALLENGE` (3DS/SCA) si 0.5–0.8 ; `BLOCK` >0.8.
  **Reason codes** loggés (explicabilité: SHAP top-features).

### 📈 KPIs & surveillance

* **Capture fraude** (recall) ↑ ; **false positive rate** ↓ ; **latence P95** < 50 ms ; **€ fraude évitée** ; **taux frictions**.
* **Drift**: distribution features vs training ; recalibrage mensuel.

### 🔧 Snippet (Structured Streaming PySpark – fenêtres & score factice)

```python
# lecture Kafka → JSON
df = (spark.readStream.format("kafka")
      .option("kafka.bootstrap.servers","kafka:9092")
      .option("subscribe","transactions")
      .load())

from pyspark.sql.functions import from_json, col, window, avg, stddev, count
schema = "transaction_id string, timestamp timestamp, account_id string, amount double, merchant_id string, device_id string, ip string, country string"
json = df.selectExpr("CAST(value AS STRING) v").select(from_json(col("v"), schema).alias("j")).select("j.*")

# fenêtres 1 minute par compte
win = (json
  .withWatermark("timestamp","2 minutes")
  .groupBy("account_id", window("timestamp","1 minute"))
  .agg(count("*").alias("cnt_1m"), avg("amount").alias("avg_1m"), stddev("amount").alias("std_1m")))

# jointure simple (ex.: seuils métier en mémoire)
scored = win.selectExpr("account_id","cnt_1m","avg_1m","coalesce(std_1m,0.01) as std_1m")\
            .withColumn("score", (col("cnt_1m")/5.0) + (col("avg_1m")/200.0))

(scored.writeStream
 .outputMode("update")
 .format("memory")
 .queryName("fraud_scores")
 .start())
```

---

## 2) Analyse de sentiments sur les réseaux sociaux

### 🎯 Objectif

Mesurer en **quasi temps réel** la perception d’une marque/campagne, détecter les **pics négatifs** (crise), informer le **service client**.

### 🔗 Données & pipeline

* Connecteurs API (X/Twitter, Reddit, avis, forums, TikTok via fournisseurs), **langID**, horodatage, métriques d’engagement, texte.
* **Kafka** topics : `social_raw`, `social_clean`, `social_sentiment`.

**Événement (simplifié)**

```json
{"post_id":"p_889","ts":"2025-08-16T10:04:00Z","source":"twitter","lang":"fr",
 "text":"Livraison en retard, très déçu !","engagement":{"likes":2,"replies":1}}
```

### 🧼 Pré-traitement

* Déduplication, détection langue, nettoyage (URLs, emojis → tokens), normalisation (lowercase), stopwords spécifiques, correction légère.

### 🤖 Modélisation

* **Modèle**: Transformer multilingue fine-tuned (3 classes pos/neu/neg) + **aspects** (produit, prix, SAV) via **topic/aspect extraction** (KeyBERT / BERTopic).
* **Sorties**: `label`, `confidence`, `aspects[]`.
* **Agrégation**: **indice de sentiment pondéré** par engagement, par **jour/source/aspect**.

### 📊 Exemple d’agrégation & alerte

* Sur 1h: 150 posts, 60 neg, 30 neu, 60 pos → score = `(pos - neg)/(total)` = 0.0 → neutre ;
* Pic négatif si score < −0.25 **et** `neg > mean_7d_neg + 2σ` → Slack/PagerDuty.

### 🖥️ Dashboard

* Courbe sentiment (P5/P50/P95), **wordcloud négatif**, top aspects négatifs, temps de réponse SAV, comparatif concurrents.

### ⚠️ Pièges & remèdes

* **Sarcasme**: utiliser emojis/punctuations comme features ;
* **Bruits/Spams**: règles + modèles de spam ;
* **Biais langue**: évaluer par langue ; dataset annoté équilibré.

---

## 3) Chaîne logistique prédictive (Demand & ETA + réassort)

### 🎯 Objectif

Réduire **ruptures** et **stocks morts**, améliorer **OTIF** (On-Time-In-Full) et **taux de service**.

### 🔗 Données

* Commandes (SKU, quantité, prix, canal), stocks, historiques ventes, **lead time** fournisseurs, promotions, météo/jours fériés, capteurs transport (température, position), coûts.

### 🧮 Prévisions & réassort

* **Demand forecasting** par SKU/site: modèles hiérarchiques (Prophet, ETS), gradient boosting (XGBoost) avec promos/prix/concurrence.
* **ROP (Reorder Point)** :

  * Moyenne demande/jour `μ_d`, écart-type `σ_d` ; lead time moyen `μ_L`, écart-type `σ_L`.
  * Demande moyenne pendant lead time `μ = μ_d * μ_L`.
  * Écart-type pendant lead time `σ = sqrt( μ_L * σ_d² + μ_d² * σ_L² )`.
  * **Safety stock** = `z * σ` (ex. z=1,65 pour 95%).
  * **ROP** = `μ + safety stock`.

**Exemple chiffré (clair et reproductible)**
`μ_d=100`, `σ_d=20`, `μ_L=5`, `σ_L=1`
`μ = 100*5 = 500`
`σ = sqrt(5*400 + 100^2*1) = sqrt(2000 + 10000) = sqrt(12000) ≈ 109,54`
Safety stock = `1,65 * 109,54 ≈ 180,75` → **181**
**ROP ≈ 500 + 181 = 681 unités**

### 🚚 ETA prédictive & risques transport

* Features: route, transporteur, météo, trafic, jour/heure, historique retard, saturation quai.
* Modèles: GBDT / time-to-event (survival).
* Actions: **ré-allocation** stock, re-routing, alerte magasin.

### 📈 KPIs

MAPE prévision ↓, taux de rupture ↓, stock moyen ↓, OTIF ↑, **inventory turns** ↑, **€ working capital** ↓.

---

# ⚙️ Démo conceptuelle – Pipeline simple (Kafka → Data Lake → Spark → BI)

## 🧩 Schéma général

```
           ┌───────────────┐
           │  Producers    │  (apps web, capteurs, APIs)
           └───────┬───────┘
                   │  (events JSON/Avro)
             Kafka Topics
     ┌──────────┬───────────┬───────────┐
     │ orders   │ inventory │ social    │
     └────┬─────┴─────┬─────┴─────┬─────┘
          │           │           │
          ▼           ▼           ▼
   Spark Structured Streaming (jobs)
          │           │           │
          └────→ Data Lake (raw → silver → gold) [Parquet/Delta]
                           │
                           ▼
              BI / Analytics (Tableau / Power BI / Databricks SQL)
```

## 1) Ingestion (Kafka)

### a) Topics & schémas

* `orders` (clé: `order_id`) – commandes
* `inventory` – mises à jour stock
* `social_raw` – posts réseaux sociaux

**Exemple `orders` (JSON)**

```json
{"order_id":"o_1001","ts":"2025-08-16T12:10:00Z","customer_id":"c_77",
 "items":[{"sku":"A123","qty":2,"price":19.9},{"sku":"B200","qty":1,"price":49}],
 "channel":"web","store_id":null,"city":"Lille","country":"FR"}
```

### b) Bonnes pratiques

* **Avro/Protobuf + Schema Registry** (compatibilité schéma)
* Clés bien choisies (partitionnement par `customer_id`/`store_id` si besoin d’ordering)

## 2) Stockage (Data Lake zones)

```
/datalake/
  raw/    (ingestion brute par date)/topic=orders/...
  silver/ (nettoyé, colonnes atomiques, types)
  gold/   (tables métier prêtes BI : ventes_jour, top_SKU, forecast)
```

## 3) Traitement (Spark)

### a) Job streaming – normaliser `orders` (raw → silver)

```python
from pyspark.sql.functions import from_json, col, explode

orders_raw = (spark.readStream.format("kafka")
  .option("kafka.bootstrap.servers","kafka:9092")
  .option("subscribe","orders")
  .load())

schema = """
 order_id string, ts timestamp, customer_id string,
 items array<struct<sku:string,qty:int,price:double>>,
 channel string, store_id string, city string, country string
"""

json = orders_raw.selectExpr("CAST(value AS STRING) as v")\
                 .select(from_json(col("v"), schema).alias("j")).select("j.*")

# éclater les items
orders_flat = json.withColumn("item", explode(col("items")))\
                  .select("order_id","ts","customer_id","channel","city","country",
                          col("item.sku").alias("sku"),
                          col("item.qty").alias("qty"),
                          col("item.price").alias("price"))

# écrire en Delta/Parquet (silver)
(orders_flat.writeStream
 .format("delta")
 .option("checkpointLocation","/datalake/_chk/orders_silver")
 .option("path","/datalake/silver/orders")
 .outputMode("append").start())
```

### b) Job batch/stream – agrégations (silver → gold)

```sql
-- Vue ventes par jour/ville/sku
CREATE OR REPLACE TEMP VIEW v_orders AS
SELECT date(ts) AS d, city, sku, SUM(qty) AS units, SUM(qty*price) AS revenue
FROM delta.`/datalake/silver/orders`
GROUP BY date(ts), city, sku;

-- Table gold
CREATE TABLE delta.`/datalake/gold/daily_sales`
AS SELECT * FROM v_orders;
```

**Idées “gold” supplémentaires**

* `top_sku_7d`, `conversion_by_channel`, `stock_cover_days` (jointure stock).

## 4) Visualisation (Tableau / Power BI)

* **Connexion**: dossier `/datalake/gold/` (Parquet/Delta via connec. Spark/Databricks/ODBC).
* **Dashboards**:

  * *Sales Overview*: revenu & unités par jour, ville, canal, top produits.
  * *Operations*: couverture de stock (jours), ruptures prédites (si forecast).
  * *Social*: courbe sentiment, top sujets négatifs.

## 5) Observabilité & gouvernance (indispensable)

* **Qualité**: tests Great Expectations (valeurs non nulles, domaines).
* **Lineage**: Atlas/OpenLineage (raw→silver→gold).
* **Sécu**: chiffrement au repos, **ABAC** (masquage email/PII), audit accès.
* **Coûts**: tags FinOps, auto-stop streams inactifs.

---

# 📚 Annexes pratiques

## A) Checklists de run (pour la démo)

1. Créer topics Kafka + Schema Registry.
2. Lancer producteurs de test (`kafka-producer-perf`, scripts Python).
3. D démarrer jobs Spark (stream + batch).
4. Vérifier écritures `/datalake/silver` (Parquet/Delta).
5. Construire `gold` (SQL) et brancher BI.
6. Définir 3 KPIs et une alerte (latence stream > 2 min, fichiers orphelins, null rate > x%).

## B) Jeux de données de test (mini)

* **orders**: 5 villes, 20 SKU, trafic 50–200 events/min.
* **inventory**: stock initial + mises à jour toutes 5 min.
* **social\_raw**: 10–50 msgs/min avec 20% négatif (emoji & URLs).

## C) Schéma de décision fraude (simple)

```
Score(model)  →  <0.5 ALLOW
              →  0.5–0.8 CHALLENGE (3DS/SCA)
              →  >0.8 BLOCK
+ Rules overrides (sanctions, pays bloqués) + Reason codes (SHAP)
```

## D) Pièges à éviter

* Lake “raw only” → **data swamp** (mettez des contrats/qualité).
* POC notebooks sans **MLOps** (registry, monitoring, canary).
* Topics Kafka sans **clé stable** (re-partitionnement casse l’ordering).
* Tables “gold” non documentées (définitions KPI ambiguës).

---

Si tu veux, je peux te **packager cette démo** en deux variantes :

* **100% local** (Docker Compose: Kafka + Spark + MinIO + Superset)
* **Cloud** (Databricks + S3/ADLS + Power BI Service)

Tu préfères laquelle pour un atelier live ?
