import express from 'express';
import pg from 'pg';
import formidable from 'formidable';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const { Pool } = pg;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = process.env.PORT || 10000;

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

// Static files serve kar - public folder
app.use(express.static('public'));
app.use(express.json());

// REGISTER API - YAHAN BAN GAYA
app.post('/api/register', (req, res) => {
  const form = formidable({
    maxFileSize: 1.5 * 1024 * 1024,
    maxTotalFileSize: 3 * 1024 * 1024,
  });

  form.parse(req, async (err, fields, files) => {
    if (err) {
      return res.status(400).json({
        success: false,
        message: 'File bahut badi hai. 1.5MB se chhoti rakho'
      });
    }

    const shopName = fields.shopName?.[0];
    const phone = fields.phone?.[0];
    const password = fields.password?.[0];
    const address = fields.address?.[0];
    const aadhar = files.aadhar?.[0];
    const electricity = files.electricity?.[0];

    if (!shopName ||!phone ||!password ||!address ||!aadhar ||!electricity) {
      return res.status(400).json({
        success: false,
        message: 'Saare fields aur documents chahiye'
      });
    }

    try {
      const aadharBase64 = 'data:' + aadhar.mimetype + ';base64,' + fs.readFileSync(aadhar.filepath, 'base64');
      const electricityBase64 = 'data:' + electricity.mimetype + ';base64,' + fs.readFileSync(electricity.filepath, 'base64');

      await pool.query(
        `INSERT INTO vendors (shop_name, phone, password, address, aadhar_url, electricity_bill_url, kyc_status, active)
         VALUES ($1, $2, $3, $4, $5, $6, 'pending', false)`,
        [shopName, phone, password, address, aadharBase64, electricityBase64]
      );

      res.status(200).json({ success: true, message: 'Registration ho gaya!' });
    } catch (err) {
      console.log('DB Error:', err);
      if (err.code === '23505') {
        res.status(400).json({ success: false, message: 'Phone number already registered' });
      } else {
        res.status(500).json({ success: false, message: 'Database error' });
      }
    }
  });
});

// VENDOR LOGIN API - YE BHI YAHAN DAAL DE
app.post('/api/vendor-login', async (req, res) => {
  const { phone, password } = req.body;

  if (!phone ||!password) {
    return res.status(400).json({ success: false, message: 'Phone aur Password daalo' });
  }

  try {
    const result = await pool.query(
      'SELECT id, shop_name, kyc_status, active FROM vendors WHERE phone = $1 AND password = $2',
      [phone, password]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ success: false, message: 'Phone ya Password galat hai' });
    }

    const vendor = result.rows[0];

    if (!vendor.active) {
      return res.status(403).json({
        success: false,
        message: 'Account abhi approve nahi hua. Admin 24 hours mein verify karega'
      });
    }

    res.status(200).json({ success: true, vendor });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

// ADD PRODUCT API
app.post('/api/add-product', (req, res) => {
  const form = formidable({ maxFileSize: 1.5 * 1024 });

  form.parse(req, async (err, fields, files) => {
    if (err) return res.status(500).json({ success: false, message: 'Upload error' });

    const vendorId = fields.vendorId?.[0];
    const name = fields.name?.[0];
    const price = fields.price?.[0];
    const stock = fields.stock?.[0];
    const image = files.image?.[0];

    if (!vendorId ||!name ||!price ||!stock ||!image) {
      return res.status(400).json({ success: false, message: 'Saare fields bharo' });
    }

    try {
      await pool.query(`
        CREATE TABLE IF NOT EXISTS products (
          id SERIAL PRIMARY KEY,
          vendor_id INTEGER NOT NULL,
          name VARCHAR(255) NOT NULL,
          price INTEGER NOT NULL,
          stock INTEGER NOT NULL,
          image_url TEXT,
          active BOOLEAN DEFAULT true,
          created_at TIMESTAMP DEFAULT NOW()
        );
      `);

      const imageBase64 = 'data:' + image.mimetype + ';base64,' + fs.readFileSync(image.filepath, 'base64');

      await pool.query(
        `INSERT INTO products (vendor_id, name, price, stock, image_url)
         VALUES ($1, $2, $3, $4, $5)`,
        [vendorId, name, price, stock, imageBase64]
      );

      res.status(200).json({ success: true, message: 'Product added' });
    } catch (err) {
      res.status(500).json({ success: false, message: err.message });
    }
  });
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
