const { Pool } = require('pg');
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

module.exports = async (req, res) => {
  try {
    const category = req.query.category;
    let query = 'SELECT * FROM products ORDER BY id';
    let params = [];
    
    if (category) {
      query = 'SELECT * FROM products WHERE category = $1 ORDER BY id';
      params = [category];
    }
    
    const result = await pool.query(query, params);
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Database error' });
  }
};
