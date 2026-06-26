const express = require('express')
const path = require('path')
const app = express()
const PORT = process.env.PORT || 10000

app.use(express.json())
app.use(express.static('public'))

// Database setup route
app.use('/api/setup', require('./api/setup'))

// API routes
app.use('/api/vendor', require('./api/vendor'))
app.use('/api/products', require('./api/products'))
app.use('/api/cart', require('./api/cart'))
app.use('/api/order', require('./api/order'))

// Page routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'))
})

app.get('/food', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'food.html'))
})

app.get('/dress', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'dress.html'))
})

app.get('/grocery', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'grocery.html'))
})

app.get('/cart', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'cart.html'))
})

app.get('/vendor', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'vendor.html'))
})

app.get('/order', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'order.html'))
})

app.get('/payment', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'payment.html'))
})

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`)
})
