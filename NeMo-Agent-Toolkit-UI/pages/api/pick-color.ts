import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { image_url, x, y } = req.body;

    if (!image_url) {
      return res.status(400).json({ error: '请提供图片URL' });
    }

    if (typeof x !== 'number' || typeof y !== 'number') {
      return res.status(400).json({ error: '请提供有效的坐标' });
    }

    // 调用后端API
    const response = await fetch('http://localhost:8001/pick-color', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image_url,
        x: Math.round(x),
        y: Math.round(y)
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    return res.status(200).json(data);
  } catch (error) {
    console.error('Pick color API error:', error);
    return res.status(500).json({ error: '点击取色失败' });
  }
}
