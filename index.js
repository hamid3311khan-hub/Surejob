const express = require('express')
const app = express()
const port = process.env.PORT || 10000

// Tera products wala API route
app.get('/api/products', (req, res) => {
  // Yaha tu DB se products fetch karta tha
  res.json([
    { id: 1, name: 'Chicken Biryani', price: 250 },
    { id: 2, name: 'Paneer Tikka', price: 180 }
  ])
})

// Setup wala route
app.get('/api/setup', (req, res) => {
  res.json({ status: 'DB Connected' })
})

// Server start
app.listen(port, () => {
  console.log(`Server running on port ${port}`)
})
