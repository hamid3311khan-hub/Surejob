const express = require('express');
const path = require('path');
const app = express();

app.use(express.json());
app.use(express.static('public'));

// Import Routes - Har file ka control alag
const registerRoute = require('./api/register');
const vendorRoute = require('./api/vendor');

// Use Routes - Sab link ho gaye
app.use('/api/register', registerRoute);
app.use('/api/vendor', vendorRoute);

// HTML Pages Serve Karo
app.get('/vendor', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'vendor.html'));
});

app.get('/register', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'register.html'));
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
