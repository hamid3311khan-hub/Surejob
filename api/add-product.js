import pg from 'pg';
import formidable from 'formidable';
import fs from 'fs';
const { Pool } = pg;

export const config = {
  api: { bodyParser: false }
};

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

export default async function handler(req, res) {
  if (req.method!== 'POST') return res.status(405).json({ message: 'Method not allowed' });

  const form = formidable({ maxFileSize: 5 * 1024 });

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
      // Products table banao agar nahi hai
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
}
