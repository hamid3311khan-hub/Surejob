import pg from 'pg';
import formidable from 'formidable';
import fs from 'fs';
const { Pool } = pg;

export const config = {
  api: {
    bodyParser: false
  }
};

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

export default async function handler(req, res) {
  if (req.method!== 'POST') {
    return res.status(405).json({ success: false, message: 'Method not allowed' });
  }

  const form = formidable({
    maxFileSize: 1.5 * 1024 * 1024,
    maxTotalFileSize: 3 * 1024,
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
      if (err.code === '23505') {
        res.status(400).json({ success: false, message: 'Phone number already registered' });
      } else {
        res.status(500).json({ success: false, message: 'Database error' });
      }
    }
  });
             }
