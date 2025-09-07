import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { 
      foreground_color, 
      background_color, 
      text_size = 'normal', 
      wcag_level = 'AA',
      check_colorblind = true 
    } = req.body;

    if (!foreground_color || !background_color) {
      return res.status(400).json({ error: 'Foreground and background colors are required' });
    }

    // Call the backend accessibility check service
    const response = await fetch('http://localhost:8001/color/contrast', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: foreground_color,
        background: background_color,
        text_size,
        wcag_level,
        check_colorblind
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const result = await response.json();
    
    // Extract accessibility data from the backend response
    if (result.success && result.accessibility) {
      res.status(200).json(result.accessibility);
    } else {
      throw new Error('Invalid response from backend');
    }
  } catch (error) {
    console.error('Accessibility check error:', error);
    res.status(500).json({ 
      error: 'Failed to check accessibility',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
