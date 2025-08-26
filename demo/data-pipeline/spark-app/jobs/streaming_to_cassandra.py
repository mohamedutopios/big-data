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
