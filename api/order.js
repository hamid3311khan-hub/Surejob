const express = require('express')
const router = express.Router()
const { Pool } = require('pg')

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
})

// Create order
router.post('/', async (req, res) => {
  try {
    const { customerName, phone, address } = req.body
    
    const cartItems = await pool.query(`
      SELECT c.product_id, c.qty, p.price, p.offer_price, p.vendor_id
      FROM cart c 
      JOIN products p ON c.product_id = p.id 
      WHERE c.session_id = 'guest'
    `)
    
    if (cartItems.rows.length === 0) {
      return res.status(400).json({ success: false, error: 'Cart khali hai' })
    }
    
    const vendorOrders = {}
    cartItems.rows.forEach(item => {
      const vid = item.vendor_id
      if (!vendorOrders[vid]) vendorOrders[vid] = []
      vendorOrders[vid].push(item)
    })
    
    const orderIds = []
    let grandTotal = 0
    
    for (const vendorId in vendorOrders) {
      const items = vendorOrders[vendorId]
      const orderId = 'PH' + Date.now() + vendorId
      let total = 0
      
      items.forEach(item => {
        total += (item.offer_price || item.price) * item.qty
      })
      
      await pool.query(`
        INSERT INTO orders (order_id, vendor_id, customer_name, phone, address, total, status, payment_status) 
        VALUES ($1, $2, $3, $4, $5, $6, 'Pending', 'Unpaid')
      `, [orderId, vendorId, customerName, phone, address, total])
      
      for (const item of items) {
        await pool.query(`
          INSERT INTO order_items (order_id, product_id, qty, price) 
          VALUES ($1, $2, $3, $4)
        `, [orderId, item.product_id, item.qty, item.offer_price || item.price])
      }
      
      orderIds.push(orderId)
      grandTotal += total
    }
    
    await pool.query('DELETE FROM cart WHERE session_id = $1', ['guest'])
    
    res.json({ success: true, orderIds, total: grandTotal })
  } catch (err) {
    res.status(500).json({ success: false, error: err.message })
  }
})

// Payment update
router.post('/:orderId/pay', async (req, res) => {
  try {
    const { paymentMethod } = req.body
    await pool.query(
      'UPDATE orders SET payment_status = $1, payment_method = $2, status = $3 WHERE order_id = $4',
      ['Paid', paymentMethod, 'Confirmed', req.params.orderId]
    )
    res.json({ success: true })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

module.exports = router
