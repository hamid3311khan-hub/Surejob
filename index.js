const express = require('express')
const path = require('path')
const app = express()
const port = process.env.PORT || 10000

// Middleware
app.use(express.json())
app.use(express.static('public'))

// PAGES KE ROUTES
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'))
})

app.get('/food', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'food.html'))
})

app.get('/cart', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'cart.html'))
})

// API ROUTES
app.get('/api/products', (req, res) => {
  res.json([
    { id: 1, name: 'Chicken Biryani', price: 250 },
    { id: 2, name: 'Paneer Tikka', price: 180 }
  ])
})

app.get('/api/cart', (req, res) => {
  res.json([
    { id: 1, name: 'Chicken Biryani', price: 250, qty: 2 },
    { id: 3, name: 'Veg Burger', price: 80, qty: 1 }
  ])
})

app.get('/api/setup', (req, res) => {
  res.json({ status: 'DB Connected' })
})

// SERVER START
app.listen(port, () => {
  console.log(`Server running on port ${port}`)
})
