const { Client } = require('pg');

module.exports = async (req, res) => {
  const client = new Client({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false }
  });
  
  try {
    await client.connect();
    await client.query(`
      DROP TABLE IF EXISTS menu, orders, biryani_menu, biryani_orders CASCADE;
      
      CREATE TABLE IF NOT EXISTS categories (id SERIAL PRIMARY KEY, name VARCHAR(50), icon VARCHAR(20));
      CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, category_id INT, name VARCHAR(100), price INTEGER);
      CREATE TABLE IF NOT EXISTS orders (id SERIAL PRIMARY KEY, order_number VARCHAR(20) UNIQUE, customer_name VARCHAR(100), mobile VARCHAR(15), address TEXT, items JSONB, total_amount INTEGER, status VARCHAR(20) DEFAULT 'NEW', order_time TIMESTAMP DEFAULT NOW());
      
      INSERT INTO categories (name, icon) VALUES ('Food', '🍗'), ('Dress', '👗'), ('Grocery', '🛒') ON CONFLICT DO NOTHING;
      INSERT INTO products (category_id, name, price) VALUES (1, 'Chicken Biryani Half', 200), (1, 'Chicken Biryani Full', 320), (1, 'Mutton Biryani Full', 270) ON CONFLICT DO NOTHING;
    `);
    res.status(200).send('DB Setup Done ✅ Phatakcart Ready');
  } catch (err) {
    res.status(500).send('Error: ' + err.message);
  } finally {
    await client.end();
  }
};
