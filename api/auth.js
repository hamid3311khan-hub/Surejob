const { sql } = require('@vercel/postgres');
const bcrypt = require('bcryptjs');

module.exports = async (req, res) => {
  const { action } = req.query;

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    // 1. PUBLIC USER REGISTER
    if (action === 'register' && req.method === 'POST') {
      const { name, email, phone, password, address } = req.body;

      if (!name ||!email ||!password) {
        return res.status(400).json({ error: 'Name, email, password required hai' });
      }

      const hashedPassword = await bcrypt.hash(password, 10);

      const result = await sql`
        INSERT INTO users (name, email, phone, password, address)
        VALUES (${name}, ${email}, ${phone}, ${hashedPassword}, ${address})
        RETURNING id, name, email, phone
      `;

      return res.status(201).json({
        message: 'Register success',
        user: result.rows[0]
      });
    }

    // 2. PUBLIC USER LOGIN
    if (action === 'login' && req.method === 'POST') {
      const { email, password } = req.body;

      const result = await sql`SELECT * FROM users WHERE email = ${email}`;

      if (result.rows.length === 0) {
        return res.status(401).json({ error: 'User nahi mila' });
      }

      const user = result.rows[0];
      const isValid = await bcrypt.compare(password, user.password);

      if (!isValid) {
        return res.status(401).json({ error: 'Galat password' });
      }

      return res.status(200).json({
        message: 'Login success',
        user: { id: user.id, name: user.name, email: user.email, phone: user.phone }
      });
    }

    // 3. ADMIN LOGIN
    if (action === 'admin-login' && req.method === 'POST') {
      const { email, password } = req.body;

      const result = await sql`SELECT * FROM admin WHERE email = ${email}`;

      if (result.rows.length === 0) {
        return res.status(401).json({ error: 'Admin nahi mila' });
      }

      const admin = result.rows[0];
      const isValid = await bcrypt.compare(password, admin.password);

      if (!isValid) {
        return res.status(401).json({ error: 'Galat password' });
      }

      return res.status(200).json({
        message: 'Admin login success',
        admin: { id: admin.id, name: admin.name, email: admin.email }
      });
    }

    return res.status(404).json({ error: 'Invalid action' });

  } catch (error) {
    if (error.code === '23505') {
      return res.status(400).json({ error: 'Email already registered hai' });
    }
    res.status(500).json({ error: error.message });
  }
};
