import { NextApiRequest, NextApiResponse } from 'next';

export const config = {
  api: {
    bodyParser: {
      sizeLimit: '10mb',
    },
  },
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { image_url, num_colors = 5, min_percentage = 0.05 } = req.body;

    if (!image_url) {
      return res.status(400).json({ error: '请提供图片URL' });
    }

    // 调用后端API - 使用base64图片分析端点
    const response = await fetch('http://localhost:8001/analyze-image-base64', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image_data: image_url,
        num_colors: parseInt(num_colors)
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    return res.status(200).json(data);
  } catch (error) {
    console.error('Color analysis API error:', error);
    return res.status(500).json({ error: '颜色分析失败' });
  }
}
