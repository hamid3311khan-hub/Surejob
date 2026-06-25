const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

module.exports = async (req, res) => {
  try {
    // Vendors table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS vendors (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        phone VARCHAR(20) UNIQUE NOT NULL,
        shop_name VARCHAR(100),
        password VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
      )
    `);

    // Products table with vendor
    await pool.query(`
      CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        vendor_id INTEGER REFERENCES vendors(id),
        name VARCHAR(100) NOT NULL,
        price INTEGER NOT NULL,
        offer_price INTEGER,
        category INTEGER NOT NULL,
        image_url TEXT,
        description TEXT,
        active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT NOW()
      )
    `);

    // Cart table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS cart (
        id SERIAL PRIMARY KEY,
        product_id INTEGER REFERENCES products(id),
        qty INTEGER NOT NULL,
        session_id VARCHAR(100) DEFAULT 'guest'
      )
    `);

    // Orders table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        order_id VARCHAR(20) UNIQUE NOT NULL,
        vendor_id INTEGER REFERENCES vendors(id),
        customer_name VARCHAR(100),
        phone VARCHAR(20),
        address TEXT,
        total INTEGER NOT NULL,
        status VARCHAR(20) DEFAULT 'Pending',
        payment_status VARCHAR(20) DEFAULT 'Unpaid',
        payment_method VARCHAR(20),
        created_at TIMESTAMP DEFAULT NOW()
      )
    `);

    // Order items table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS order_items (
        id SERIAL PRIMARY KEY,
        order_id VARCHAR(20) REFERENCES orders(order_id),
        product_id INTEGER REFERENCES products(id),
        qty INTEGER NOT NULL,
        price INTEGER NOT NULL
      )
    `);

    // Default vendor
    await pool.query(`
      INSERT INTO vendors (name, phone, shop_name, password) VALUES
      ('Phatak Admin', '9999999999', 'Phatakcart', 'admin123')
      ON CONFLICT (phone) DO NOTHING
    `);

    // Default products
    await pool.query(`
      INSERT INTO products (vendor_id, name, price, offer_price, category, image_url, description) VALUES
      (1, 'Chicken Biryani', 250, 199, 1, 'https://images.unsplash.com/photo-1563379091339-03246963d96c?w=300', 'Special offer - 50 off'),
      (1, 'Paneer Tikka', 180, 150, 1, 'https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=300', 'Fresh Paneer'),
      (1, 'Veg Burger', 80, 60, 1, 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=300', 'Buy 2 Get 1 Free'),
      (1, 'Chicken Roll', 120, 100, 1, 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=300', 'Spicy Roll'),
      (1, 'Cheese Pizza', 299, 249, 1, 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=300', 'Extra Cheese'),
      (1, 'Veg Momos', 100, 80, 1, 'https://images.unsplash.com/photo-1625220194771-7ebdea0b70b9?w=300', 'Steamed Hot'),
      (1, 'Samosa', 20, 15, 1, 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=300', '2 for 30'),
      (1, 'Masala Dosa', 90, 70, 1, 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=300', 'South Special'),
      (1, 'Chicken 65', 220, 180, 1, 'https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=300', 'Boneless'),
      (1, 'Cold Coffee', 60, 50, 1, 'https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=300', 'Chilled')
      ON CONFLICT DO NOTHING
    `);

    res.json({ message: 'Database setup complete. All tables ready.' });
  } catch (err) {
    console.error('Setup Error:', err);
    res.status(500).json({ error: err.message });
  }
};

app.use('/api/vendor', require('./api/vendor'))
app.use('/api/products', require('./api/products'))
app.use('/api/order', require('./api/order'))

app.get('/vendor', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'vendor.html'))
})
app.get('/order', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'order.html'))
})
app.get('/payment', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'payment.html'))
})
