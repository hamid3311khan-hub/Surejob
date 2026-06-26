const { Pool } = require('pg');
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,DELETE,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    // 1. SABHI VENDORS DEKHO - Approved + Pending
    if (action === 'vendors' && req.method === 'GET') {
      const result = await sql`
        SELECT id, shop_name, owner_name, email, phone, is_approved, created_at
        FROM vendors ORDER BY created_at DESC
      `;
      return res.status(200).json({ vendors: result.rows });
    }

    // 2. VENDOR APPROVE KARO
    if (action === 'approve-vendor' && req.method === 'POST') {
      const { vendor_id } = req.body;

      await sql`UPDATE vendors SET is_approved = true WHERE id = ${vendor_id}`;
      return res.status(200).json({ message: 'Vendor approved ho gaya' });
    }

    // 3. VENDOR REJECT/DELETE KARO
    if (action === 'reject-vendor' && req.method === 'DELETE') {
      const { vendor_id } = req.body;

      await sql`DELETE FROM vendors WHERE id = ${vendor_id}`;
      return res.status(200).json({ message: 'Vendor reject ho gaya' });
    }

    // 4. ADMIN KE PRODUCTS DEKHO
    if (action === 'my-products' && req.method === 'GET') {
      const { admin_id } = req.query;

      const result = await sql`
        SELECT * FROM products
        WHERE admin_id = ${admin_id}
        ORDER BY created_at DESC
      `;
      return res.status(200).json({ products: result.rows });
    }

    // 5. ADMIN PRODUCT DELETE KARO
    if (action === 'delete-product' && req.method === 'DELETE') {
      const { product_id, admin_id } = req.body;

      await sql`
        DELETE FROM products
        WHERE id = ${product_id} AND admin_id = ${admin_id}
      `;
      return res.status(200).json({ message: 'Product delete ho gaya' });
    }

    // 6. SABHI ORDERS DEKHO
    if (action === 'orders' && req.method === 'GET') {
      const result = await sql`
        SELECT
          o.*,
          u.name as customer_name,
          u.email as customer_email
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
      `;
      return res.status(200).json({ orders: result.rows });
    }

    // 7. DASHBOARD STATS
    if (action === 'stats' && req.method === 'GET') {
      const vendors = await sql`SELECT COUNT(*) FROM vendors WHERE is_approved = true`;
      const pending = await sql`SELECT COUNT(*) FROM vendors WHERE is_approved = false`;
      const products = await sql`SELECT COUNT(*) FROM products WHERE is_active = true`;
      const orders = await sql`SELECT COUNT(*) FROM orders`;
      const revenue = await sql`SELECT SUM(total_amount) FROM orders WHERE payment_status = 'paid'`;

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
