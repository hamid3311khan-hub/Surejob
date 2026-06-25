const express = require('express')
const router = express.Router()
const { Pool } = require('pg')

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
})

// Get cart items
router.get('/', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT c.id, c.qty, p.id as product_id, p.name, p.price, p.offer_price, p.image_url, p.vendor_id
      FROM cart c 
      JOIN products p ON c.product_id = p.id 
      WHERE c.session_id = 'guest'
    `)
    res.json(result.rows)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// Add to cart
router.post('/', async (req, res) => {
  try {
    const { productId, qty } = req.body
    
    const existing = await pool.query(
      'SELECT * FROM cart WHERE product_id = $1 AND session_id = $2',
      [productId, 'guest']
    )
    
    if (existing.rows.length > 0) {
      await pool.query(
        'UPDATE cart SET qty = qty + $1 WHERE product_id = $2 AND session_id = $3',
        [qty, productId, 'guest']
      )
    } else {
      await pool.query(
        'INSERT INTO cart (product_id, qty, session_id) VALUES ($1, $2, $3)',
        [productId, qty, 'guest']
      )
    }
    
    res.json({ success: true, message: 'Cart mein add ho gaya' })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// Remove from cart
router.delete('/:id', async (req, res) => {
  try {
    await pool.query('DELETE FROM cart WHERE id = $1 AND session_id = $2', [req.params.id, 'guest'])
    res.json({ success: true })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// Clear cart
router.delete('/', async (req, res) => {
  try {
    await pool.query('DELETE FROM cart WHERE session_id = $1', ['guest'])
    res.json({ success: true })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

module.exports = router
