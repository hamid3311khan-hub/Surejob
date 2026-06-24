const express = require('express');
const path = require('path');
const productsAPI = require('./api/products.js');
const setupAPI = require('./api/setup.js');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// API Routes
app.get('/api/products', productsAPI);
app.get('/api/setup', setupAPI);

app.listen(PORT, () => {
  console.log(`Phatakcart server running on port ${PORT}`);
});
