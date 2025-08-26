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
