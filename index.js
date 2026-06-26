const express = require('express');
const { Pool } = require('pg');
const path = require('path');
const app = express();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

app.use(express.json());
app.use(express.static('public')); // public folder serve karega

// Vendor API - Orders laao
app.get('/api/vendor', async (req, res) => {
  try {
    const vendorId = 1;
    const result = await pool.query(`
      SELECT id, order_id, customer_name, phone, address, 
             total, status, payment_status, payment_method, created_at
      FROM orders 
      WHERE vendor_id = $1
      ORDER BY id DESC
    `, [vendorId]);
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Vendor API - Status update
app.put('/api/vendor', async (req, res) => {
  try {
    const { id, status } = req.body;
    await pool.query(`UPDATE orders SET status = $1 WHERE id = $2`, [status, id]);
    res.json({ message: `Order ${id} status updated to ${status}` });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Teri baki API routes yahan daal... cart.js, order.js wale

// HTML pages serve karo
app.get('/vendor', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'vendor.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
