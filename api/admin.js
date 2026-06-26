const { Pool } = require('pg');
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,DELETE,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const { action } = req.query;

  try {
    if (action === 'vendors' && req.method === 'GET') {
      const result = await pool.query(`SELECT id, shop_name, owner_name, email, phone, is_approved, created_at FROM vendors ORDER BY created_at DESC`);
      return res.status(200).json({ vendors: result.rows });
    }

    if (action === 'approve-vendor' && req.method === 'POST') {
      const { vendor_id } = req.body;
      await pool.query(`UPDATE vendors SET is_approved = true WHERE id = $1`, [vendor_id]);
      return res.status(200).json({ message: 'Vendor approved' });
    }

    if (action === 'reject-vendor' && req.method === 'DELETE') {
      const { vendor_id } = req.body;
      await pool.query(`DELETE FROM vendors WHERE id = $1`, [vendor_id]);
      return res.status(200).json({ message: 'Vendor rejected' });
    }

    if (action === 'my-products' && req.method === 'GET') {
      const { admin_id } = req.query;
      const result = await pool.query(`SELECT * FROM products WHERE admin_id = $1 ORDER BY created_at DESC`, [admin_id]);
      return res.status(200).json({ products: result.rows });
    }

    if (action === 'delete-product' && req.method === 'DELETE') {
      const { product_id, admin_id } = req.body;
      await pool.query(`DELETE FROM products WHERE id = $1 AND admin_id = $2`, [product_id, admin_id]);
      return res.status(200).json({ message: 'Product deleted' });
    }

    if (action === 'orders' && req.method === 'GET') {
      const result = await pool.query(`
        SELECT o.*, u.name as customer_name, u.email as customer_email
        FROM orders o JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
      `);
      return res.status(200).json({ orders: result.rows });
    }

    if (action === 'stats' && req.method === 'GET') {
      const vendors = await pool.query(`SELECT COUNT(*) FROM vendors WHERE is_approved = true`);
      const pending = await pool.query(`SELECT COUNT(*) FROM vendors WHERE is_approved = false`);
      const products = await pool.query(`SELECT COUNT(*) FROM products WHERE is_active = true`);
      const orders = await pool.query(`SELECT COUNT(*) FROM orders`);
      const revenue = await pool.query(`SELECT SUM(total_amount) FROM orders WHERE payment_status = 'paid'`);

      return res.status(200).json({
        total_vendors: vendors.rows[0].count,
        pending_vendors: pending.rows[0].count,
        total_products: products.rows[0].count,
        total_orders: orders.rows[0].count,
        total_revenue: revenue.rows[0].sum || 0
      });
    }

    return res.status(404).json({ error: 'Invalid action' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
