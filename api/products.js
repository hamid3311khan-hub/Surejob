const { sql } = require('@vercel/postgres');

module.exports = async (req, res) => {
  const { action, category, id } = req.query;

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    // 1. SABHI PRODUCTS DIKHAO - Homepage ke liye
    if (!action && req.method === 'GET') {
      let query = sql`
        SELECT
          p.*,
          v.shop_name,
          CASE
            WHEN p.vendor_id IS NOT NULL THEN 'vendor'
            WHEN p.admin_id IS NOT NULL THEN 'admin'
          END as seller_type
        FROM products p
        LEFT JOIN vendors v ON p.vendor_id = v.id
        WHERE p.is_active = true AND p.stock > 0
      `;

      // Category filter
      if (category) {
        query = sql`
          SELECT
            p.*,
            v.shop_name,
            CASE
              WHEN p.vendor_id IS NOT NULL THEN 'vendor'
              WHEN p.admin_id IS NOT NULL THEN 'admin'
            END as seller_type
          FROM products p
          LEFT JOIN vendors v ON p.vendor_id = v.id
          WHERE p.is_active = true AND p.stock > 0 AND p.category = ${category}
        `;
      }

      const result = await query;
      return res.status(200).json({ products: result.rows });
    }

    // 2. SINGLE PRODUCT DETAIL
    if (action === 'detail' && req.method === 'GET') {
      if (!id) return res.status(400).json({ error: 'Product id required' });

      const result = await sql`
        SELECT
          p.*,
          v.shop_name, v.owner_name, v.phone,
          CASE
            WHEN p.vendor_id IS NOT NULL THEN 'vendor'
            WHEN p.admin_id IS NOT NULL THEN 'admin'
          END as seller_type
        FROM products p
        LEFT JOIN vendors v ON p.vendor_id = v.id
        WHERE p.id = ${id} AND p.is_active = true
      `;

      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Product nahi mila' });
      }

      return res.status(200).json({ product: result.rows[0] });
    }

    // 3. ADMIN KE PRODUCTS ADD KARNA
    if (action === 'admin-add' && req.method === 'POST') {
      const { admin_id, name, description, price, offer_price, category, image_url, stock } = req.body;

      if (!admin_id ||!name ||!price) {
        return res.status(400).json({ error: 'admin_id, name, price required hai' });
      }

      const result = await sql`
        INSERT INTO products (admin_id, name, description, price, offer_price, category, image_url, stock)
        VALUES (${admin_id}, ${name}, ${description}, ${price}, ${offer_price}, ${category}, ${image_url}, ${stock})
        RETURNING *
      `;

      return res.status(201).json({
        message: 'Admin product added',
        product: result.rows[0]
      });
    }

    return res.status(404).json({ error: 'Invalid action' });

  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
