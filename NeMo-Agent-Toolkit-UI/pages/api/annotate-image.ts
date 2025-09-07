import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { image_url, colors } = req.body;

    if (!image_url || !colors) {
      return res.status(400).json({ error: 'Missing image_url or colors' });
    }

    // Call backend annotate endpoint
    const response = await fetch('http://localhost:8001/annotate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image_url,
        colors,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return res.status(response.status).json({ 
        error: `Backend error: ${errorText}` 
      });
    }

    const data = await response.json();
    return res.status(200).json(data);

  } catch (error) {
    console.error('Annotation API error:', error);
    return res.status(500).json({ 
      error: 'Failed to annotate image' 
    });
  }
}
