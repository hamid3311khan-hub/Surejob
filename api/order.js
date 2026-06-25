const express = require('express')
const router = express.Router()
const { Pool } = require('pg')

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
})

router.post('/', async (req, res) => {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    const { customerName, phone, address } = req.body

    const cartResult = await client.query(`
      SELECT c.qty, p.id, p.name, p.price, p.offer_price, p.vendor_id
      FROM cart c
      JOIN products p ON c.product_id = p.id
      WHERE c.session_id = 'guest'
    `)

    if (cartResult.rows.length === 0) throw new Error('Cart khali hai')

    // Group by vendor
    const vendorOrders = {}
    cartResult.rows.forEach(item => {
      const price = item.offer_price || item.price
      if (!vendorOrders[item.vendor_id]) {
        vendorOrders[item.vendor_id] = { items: [], total: 0 }
      }
      vendorOrders[item.vendor_id].items.push({
        id: item.id, name: item.name, qty: item.qty, price
      })
      vendorOrders[item.vendor_id].total += price * item.qty
    })

    const orderIds = []
    for (const vendorId in vendorOrders) {
      const orderId = 'ORD' + Date.now() + vendorId
      const { items, total } = vendorOrders[vendorId]

      await client.query(
        'INSERT INTO orders (order_id, vendor_id, customer_name, phone, address, total) VALUES ($1, $2, $3, $4, $5, $6)',
        [orderId, vendorId, customerName, phone, address, total]
      )

      for (const item of items) {
        await client.query(
          'INSERT INTO order_items (order_id, product_id, qty, price) VALUES ($1, $2, $3, $4)',
          [orderId, item.id, item.qty, item.price]
        )
      }
      orderIds.push(orderId)
    }

    await client.query('DELETE FROM cart WHERE session_id = $1', ['guest'])
    await client.query('COMMIT')

    res.json({ success: true, orderIds, total: Object.values(vendorOrders).reduce((s, o) => s + o.total, 0) })

  } catch (err) {
    await client.query('ROLLBACK')
    res.status(500).json({ success: false, error: err.message })
  } finally {
    client.release()
  }
})

router.post('/:id/pay', async (req, res) => {
  try {
    const { paymentMethod } = req.body
    await pool.query(
      "UPDATE orders SET payment_status = 'Paid', status = 'Confirmed', payment_method = $1 WHERE order_id = $2",
      [paymentMethod, req.params.id]
    )
    res.json({ success: true })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

module.exports = router
