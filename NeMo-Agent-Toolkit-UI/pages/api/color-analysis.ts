import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { image_data, num_colors = 5 } = req.body;

    if (!image_data) {
      return res.status(400).json({ error: 'Image data is required' });
    }

    // Call the backend base64 image analysis service
    const response = await fetch('http://localhost:8001/analyze-image-base64', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image_data: image_data,
        num_colors: num_colors,
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const result = await response.json();
    res.status(200).json(result);
  } catch (error) {
    console.error('Color analysis error:', error);
    res.status(500).json({ 
      error: 'Failed to analyze colors',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
