const express = require("express");

const app = express();
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

module.exports = app;

if (require.main === module) {
  app.listen(8000, () => console.log("Node.js backend listening on 8000"));
}
