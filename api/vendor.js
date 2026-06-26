const express = require('express')
const router = express.Router()
const { Pool } = require('pg')

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
})

// Vendor Login
router.post('/login', async (req, res) => {
  try {
    const { phone, password } = req.body
    const result = await pool.query(
      'SELECT id, name, shop_name FROM vendors WHERE phone = $1 AND password = $2',
      [phone, password]
    )
    if (result.rows.length === 0) {
      return res.status(401).json({ success: false, message: 'Galat phone ya password' })
    }
    res.json({ success: true, vendor: result.rows[0] })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// Vendor Register
router.post('/register', async (req, res) => {
  try {
    const { name, phone, shop_name, password } = req.body
    const result = await pool.query(
      'INSERT INTO vendors (name, phone, shop_name, password) VALUES ($1, $2, $3, $4) RETURNING id',
      [name, phone, shop_name, password]
    )
    res.json({ success: true, vendorId: result.rows[0].id })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// Get vendor products
router.get('/:id/products', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM products WHERE vendor_id = $1 ORDER BY id DESC',
      [req.params.id]
    )
    res.json(result.rows)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// Add product
router.post('/:id/products', async (req, res) => {
  try {
    const { name, price, offer_price, category, image_url, description } = req.body
    await pool.query(
      'INSERT INTO products (vendor_id, name, price, offer_price, category, image_url, description) VALUES ($1, $2, $3, $4, $5, $6, $7)',
      [req.params.id, name, price, offer_price, category, image_url, description]
    )
    res.json({ success: true, message: 'Product add ho gaya' })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// Update product
router.put('/products/:productId', async (req, res) => {
  try {
    const { name, price, offer_price, image_url, description, active } = req.body
    await pool.query(
      'UPDATE products SET name=$1, price=$2, offer_price=$3, image_url=$4, description=$5, active=$6 WHERE id=$7',
      [name, price, offer_price, image_url, description, active, req.params.productId]
    )
    res.json({ success: true })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// Delete product
router.delete('/products/:productId', async (req, res) => {
  try {
    await pool.query('DELETE FROM products WHERE id = $1', [req.params.productId])
    res.json({ success: true })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// Get vendor orders
router.get('/:id/orders', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT o.*, json_agg(json_build_object(
        'name', p.name, 'qty', oi.qty, 'price', oi.price
      )) as items
      FROM orders o
      LEFT JOIN order_items oi ON o.order_id = oi.order_id
      LEFT JOIN products p ON oi.product_id = p.id
      WHERE o.vendor_id = $1
      GROUP BY o.id
      ORDER BY o.created_at DESC
    `, [req.params.id])
    res.json(result.rows)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// Update order status
router.put('/orders/:orderId/status', async (req, res) => {
  try {
    const { status } = req.body
    await pool.query(
      'UPDATE orders SET status = $1 WHERE order_id = $2',
      [status, req.params.orderId]
    )
    res.json({ success: true })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

// Vendor Login
router.post('/login', async (req, res) => {
  try {
    const { phone, password } = req.body;
    const result = await pool.query('SELECT * FROM vendors WHERE phone = $1', [phone]);

    if (result.rows.length === 0) {
      return res.status(401).json({ error: 'Vendor not found' });
    }

    const vendor = result.rows[0];
    const validPass = await bcrypt.compare(password, vendor.password);

    if (!validPass) {
      return res.status(401).json({ error: 'Wrong password' });
    }

    const token = jwt.sign({ vendorId: vendor.id }, process.env.JWT_SECRET || 'secret_key_123');
    res.json({
      success: true,
      token,
      vendor: {
        id: vendor.id,
        shop_name: vendor.shop_name,
        active: vendor.active,
        kyc_status: vendor.kyc_status
      }
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
module.exports = router
