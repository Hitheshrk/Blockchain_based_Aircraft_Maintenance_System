const express = require('express');
const bodyParser = require('body-parser');
const { MongoClient } = require('mongodb');
const path = require('path');

const app = express();
const port = 3000;

app.use(bodyParser.json());

const mongoURI = 'mongodb://localhost:27017'; // Replace with your MongoDB connection URI
const dbName = 'login'; // Replace with your MongoDB database name
const collectionName = 'credential'; // Replace with your MongoDB collection name

app.use(express.static(path.join(__dirname, 'public')));

app.post('/login', async (req, res) => {
  const { username, password } = req.body;
  console.log('Received data:', { username, password });

  try {
    const client = new MongoClient(mongoURI, { useNewUrlParser: true, useUnifiedTopology: true });
    await client.connect();

    const db = client.db(dbName);
    const collection = db.collection(collectionName);

    const user = await collection.findOne({ username, password });

    if (user) {
      res.json({ success: true });
    } else {
      res.json({ success: false });
    }

    client.close();
  } catch (error) {
    console.error(error);
    res.status(500).json({ success: false, error: 'Internal Server Error' });
  }
});

// Redirect root URL to index.html
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(port, () => {
  console.log(`Server is running at http://localhost:${port}`);
});
