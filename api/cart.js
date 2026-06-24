import { Pool } from 'pg'

const pool = new Pool({
  connectionString: process.env.DATABASE_URL
})

export default async function handler(req, res) {
  // Abhi ke liye dummy cart data bhej rahe
  // Baad mein database se connect karenge
  
  if (req.method === 'GET') {
    // Cart ke items maang raha hai
    const dummyCart = [
      { id: 1, name: 'Chicken Biryani', price: 250, qty: 2 },
      { id: 3, name: 'Veg Burger', price: 80, qty: 1 }
    ]
    return res.status(200).json(dummyCart)
  }

  if (req.method === 'POST') {
    // Cart mein item add kar raha hai
    const { productId, qty } = req.body
    return res.status(200).json({ 
      success: true, 
      message: `Product ${productId} added with qty ${qty}` 
    })
  }

  res.status(405).json({ error: 'Method not allowed' })
}
