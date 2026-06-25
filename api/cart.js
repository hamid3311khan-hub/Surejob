const express = require('express')
const router = express.Router()

// Ye array mein saman store hoga
let cartItems = [
  { id: 1, name: 'Chicken Biryani', price: 250, qty: 2 },
  { id: 3, name: 'Veg Burger', price: 80, qty: 1 }
]

// Dummy products ka data - baad mein DB se aayega
const allProducts = [
  { id: 1, name: 'Chicken Biryani', price: 250 },
  { id: 2, name: 'Paneer Tikka', price: 180 },
  { id: 3, name: 'Veg Burger', price: 80 },
  { id: 4, name: 'Chicken Roll', price: 120 },
  { id: 5, name: 'Cotton Kurta', price: 599 },
  { id: 6, name: 'Jeans', price: 899 },
  { id: 7, name: 'T-Shirt', price: 399 },
  { id: 8, name: 'Aashirvaad Atta 5kg', price: 280 },
  { id: 9, name: 'Tata Salt 1kg', price: 25 }
]

// GET /api/cart - Cart dikhao
router.get('/', (req, res) => {
  res.status(200).json(cartItems)
})

// POST /api/cart - Cart mein REAL mein add karo
router.post('/', (req, res) => {
  const { productId, qty } = req.body
  
  // Product ka data dhundo
  const product = allProducts.find(p => p.id == productId)
  if (!product) {
    return res.status(404).json({ success: false, message: 'Product nahi mila' })
  }
  
  // Check karo cart mein pehle se hai kya
  const existingItem = cartItems.find(item => item.id == productId)
  
  if (existingItem) {
    // Hai to quantity badhao
    existingItem.qty += qty
  } else {
    // Nahi hai to naya add karo
    cartItems.push({
      id: product.id,
      name: product.name,
      price: product.price,
      qty: qty
    })
  }
  
  res.status(200).json({ 
    success: true, 
    message: `${product.name} cart mein add ho gaya`,
    cart: cartItems 
  })
})

module.exports = router
