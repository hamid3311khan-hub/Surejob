const express = require('express')
const path = require('path')
const app = express()
const port = process.env.PORT || 10000

app.use(express.json())
app.use(express.static('public')) // HTML files ke liye

// HOME PAGE ROUTE - YE ZARURI HAI ⚠️
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'))
})

// TERA PRODUCTS API - SAME RAHEGA
app.get('/api/products', (req, res) => {
  res.json([
    { id: 1, name: 'Chicken Biryani', price: 250 },
    { id: 2, name: 'Paneer Tikka', price: 180 }
  ])
})

// SETUP API - SAME RAHEGA  
app.get('/api/setup', (req, res) => {
  res.json({ status: 'DB Connected' })
})

// CART API - NAYA ADD KAR
app.get('/api/cart', (req, res) => {
  res.json([
    { id: 1, name: 'Chicken Biryani', price: 250, qty: 2 },
    { id: 3, name: 'Veg Burger', price: 80, qty: 1 }
  ])
})

app.listen(port, () => {
  console.log(`Server running on port ${port}`)
})
