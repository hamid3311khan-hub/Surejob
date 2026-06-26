const { Pool } = require('pg');
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const { action } = req.query;

  try {
    if (action === 'create' && req.method === 'POST') {
      const Razorpay = require('razorpay');
      const razorpay = new Razorpay({
        key_id: process.env.RAZORPAY_KEY_ID,
        key_secret: process.env.RAZORPAY_KEY_SECRET
      });

      const { user_id, items, total_amount } = req.body;
      
      const razorpayOrder = await razorpay.orders.create({
        amount: total_amount * 100,
        currency: 'INR',
        receipt: `order_${Date.now()}`
      });

      const orderResult = await pool.query(`
        INSERT INTO orders (user_id, total_amount, razorpay_order_id)
        VALUES ($1, $2, $3) RETURNING id
      `, [user_id, total_amount, razorpayOrder.id]);

      const orderId = orderResult.rows[0].id;

      for (let item of items) {
        await pool.query(`
          INSERT INTO order_items (order_id, product_id, quantity, price)
          VALUES ($1, $2, $3, $4)
        `, [orderId, item.product_id, item.quantity, item.price]);
      }

      await pool.query(`DELETE FROM cart WHERE user_id = $1`, [user_id]);

      return res.status(200).json({ 
        order_id: orderId,
        razorpay_order_id: razorpayOrder.id,
        amount: total_amount * 100,
        key: process.env.RAZORPAY_KEY_ID
      });
    }

    if (action === 'verify' && req.method === 'POST') {
      const { razorpay_order_id, razorpay_payment_id } = req.body;
      await pool.query(`
        UPDATE orders 
        SET payment_status = 'paid', razorpay_payment_id = $1, status = 'confirmed'
        WHERE razorpay_order_id = $2
      `, [razorpay_payment_id, razorpay_order_id]);
      return res.status(200).json({ message: 'Payment verified' });
    }

    return res.status(404).json({ error: 'Invalid action' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
