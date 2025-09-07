import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { base_color, scheme = 'complementary', num_colors = 5 } = req.body;

    if (!base_color) {
      return res.status(400).json({ error: 'Base color is required' });
    }

    // Call the backend palette generation service
    const response = await fetch('http://localhost:8001/color/palette', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        base_color,
        scheme,
        num_colors,
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const result = await response.json();
    res.status(200).json(result);
  } catch (error) {
    console.error('Palette generation error:', error);
    res.status(500).json({ 
      error: 'Failed to generate palette',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
