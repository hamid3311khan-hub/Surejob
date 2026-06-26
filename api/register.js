const express = require('express');
const router = express.Router();
const { Pool } = require('pg');
const bcrypt = require('bcrypt');
const formidable = require('formidable');
const path = require('path');
const fs = require('fs');

const pool = new Pool({ connectionString: process.env.DATABASE_URL });

// Uploads folder banao agar nahi hai
const uploadDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });

router.post('/', (req, res) => {
  const form = new formidable.IncomingForm();
  form.uploadDir = uploadDir;
  form.keepExtensions = true;
  form.maxFileSize = 5 * 1024 * 1024; // 5MB

  form.parse(req, async (err, fields, files) => {
    if (err) return res.status(500).json({ error: 'File upload failed' });

    try {
      const hashedPass = await bcrypt.hash(fields.password[0], 10);

      const result = await pool.query(
        `INSERT INTO vendors (shop_name, owner_name, phone, address, password, aadhar_file, electricity_file, kyc_status, active)
         VALUES ($1,$2,$3,$4,$5,$6,$7,'pending',false) RETURNING id`,
        [
          fields.shop_name[0],
          fields.owner_name[0],
          fields.phone[0],
          fields.address[0],
          hashedPass,
          files.aadhar?.[0]?.newFilename || null,
          files.electricity?.[0]?.newFilename || null
        ]
      );

      res.json({ success: true, vendorId: result.rows[0].id, message: 'Registered successfully' });
    } catch (e) {
      res.status(500).json({ error: e.message });
    }
  });
});

module.exports = router;
