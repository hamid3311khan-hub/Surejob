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
    if (action === 'add' && req.method === 'POST') {
      const { user_id, product_id, quantity } = req.body;
      const existing = await pool.query(`SELECT * FROM cart WHERE user_id = $1 AND product_id = $2`, [user_id, product_id]);
      
      if (existing.rows.length > 0) {
        await pool.query(`UPDATE cart SET quantity = quantity + $1 WHERE user_id = $2 AND product_id = $3`, [quantity, user_id, product_id]);
      } else {
        await pool.query(`INSERT INTO cart (user_id, product_id, quantity) VALUES ($1, $2, $3)`, [user_id, product_id, quantity]);
      }
      return res.status(200).json({ message: 'Added to cart' });
    }

    if (action === 'get' && req.method === 'GET') {
      const { user_id } = req.query;
      const result = await pool.query(`
        SELECT c.*, p.name, p.price, p.image 
        FROM cart c 
        JOIN products p ON c.product_id = p.id 
        WHERE c.user_id = $1
      `, [user_id]);
      return res.status(200).json({ cart: result.rows });
    }

    if (action === 'delete' && req.method === 'DELETE') {
      const { cart_id } = req.body;
      await pool.query(`DELETE FROM cart WHERE id = $1`, [cart_id]);
      return res.status(200).json({ message: 'Removed from cart' });
    }

    if (action === 'clear' && req.method === 'DELETE') {
      const { user_id } = req.body;
      await pool.query(`DELETE FROM cart WHERE user_id = $1`, [user_id]);
      return res.status(200).json({ message: 'Cart cleared' });
    }

    return res.status(404).json({ error: 'Invalid action' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
