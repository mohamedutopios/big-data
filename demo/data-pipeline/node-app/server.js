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
