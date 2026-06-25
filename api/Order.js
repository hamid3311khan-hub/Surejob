const express = require('express')
const router = express.Router()

let orders = []
let orderCounter = 1000

// POST /api/order - Order place karo
router.post('/', (req, res) => {
  const { items, customerName, address, phone } = req.body
  
  if (!items || items.length === 0) {
    return res.status(400).json({ success: false, message: 'Cart khali hai' })
  }
  
  const total = items.reduce((sum, item) => sum + (item.price * item.qty), 0)
  const orderId = 'ORD' + orderCounter++
  
  const newOrder = {
    orderId,
    items,
    customerName: customerName || 'Guest',
    address: address || 'Not Provided',
    phone: phone || 'Not Provided',
    total,
    status: 'Pending',
    paymentStatus: 'Unpaid',
    date: new Date().toLocaleString()
  }
  
  orders.push(newOrder)
  res.json({ success: true, orderId, message: 'Order create ho gaya', total })
})

// GET /api/order/:id - Order details nikalo
router.get('/:id', (req, res) => {
  const order = orders.find(o => o.orderId === req.params.id)
  if (!order) {
    return res.status(404).json({ success: false, message: 'Order nahi mila' })
  }
  res.json({ success: true, order })
})

// POST /api/order/:id/pay - Payment mark karo
router.post('/:id/pay', (req, res) => {
  const order = orders.find(o => o.orderId === req.params.id)
  if (!order) {
    return res.status(404).json({ success: false })
  }
  order.paymentStatus = 'Paid'
  order.status = 'Confirmed'
  res.json({ success: true, message: 'Payment success' })
})

module.exports = router
