import { ChatBody } from '@/types/chat';

export const config = {
  runtime: 'edge',
  api: {
    bodyParser: {
      sizeLimit: '5mb',
    },
  },
};

const generateEndpoint = 'generate';
const chatEndpoint = 'chat';
const chatStreamEndpoint = 'chat/stream';
const generateStreamEndpoint = 'generate/stream';

function buildGeneratePayload(messages: any[]) {
  const userMessage = messages?.at(-1)?.content;
  if (!userMessage) {
    throw new Error('User message not found.');
  }
  return { input_message: userMessage };
}

function buildOpenAIChatPayload(messages: any[]) {
  return {
    messages,
    model: 'string',
    temperature: 0,
    max_tokens: 0,
    top_p: 0,
    use_knowledge_base: true,
    top_k: 0,
    collection_name: 'string',
    stop: true,
    additionalProp1: {},
  };
}

async function processGenerate(response: Response): Promise<Response> {
  const data = await response.text();
  try {
    const parsed = JSON.parse(data);
    const value =
      parsed?.value ||
      parsed?.output ||
      parsed?.answer ||
      (Array.isArray(parsed?.choices)
        ? parsed.choices[0]?.message?.content
        : null);
    return new Response(typeof value === 'string' ? value : JSON.stringify(value));
  } catch {
    return new Response(data);
  }
}

async function processChat(response: Response): Promise<Response> {
  const data = await response.text();
  try {
    const parsed = JSON.parse(data);
    const content =
      parsed?.output ||
      parsed?.answer ||
      parsed?.value ||
      (Array.isArray(parsed?.choices)
        ? parsed.choices[0]?.message?.content
        : null) ||
      parsed ||
      data;
    return new Response(typeof content === 'string' ? content : JSON.stringify(content));
  } catch {
    return new Response(data);
  }
}

async function processGenerateStream(response: Response, encoder: TextEncoder, decoder: TextDecoder, additionalProps: any): Promise<ReadableStream<Uint8Array>> {
  const reader = response?.body?.getReader();
  let buffer = '';
  let streamContent = '';
  let finalAnswerSent = false;
  let counter = 0;

  return new ReadableStream({
    async start(controller) {
      try {
        while (true) {
          const { done, value } = await reader!.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          streamContent += chunk;

          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(5);
              if (data.trim() === '[DONE]') {
                controller.close();
                return;
              }
              try {
                const parsed = JSON.parse(data);
                const content =
                  parsed?.value ||
                  parsed?.output ||
                  parsed?.answer ||
                  parsed?.choices?.[0]?.message?.content ||
                  parsed?.choices?.[0]?.delta?.content;
                if (content && typeof content === 'string') {
                  controller.enqueue(encoder.encode(content));
                }
              } catch {}
            } else if (
              line.includes('<intermediatestep>') &&
              line.includes('</intermediatestep>') &&
              additionalProps.enableIntermediateSteps
            ) {
              controller.enqueue(encoder.encode(line));
            } else if (line.startsWith('intermediate_data: ')) {
              try {
                const data = line.split('intermediate_data: ')[1];
                const payload = JSON.parse(data);
                const intermediateMessage = {
                  id: payload?.id || '',
                  status: payload?.status || 'in_progress',
                  error: payload?.error || '',
                  type: 'system_intermediate',
                  parent_id: payload?.parent_id || 'default',
                  intermediate_parent_id: payload?.intermediate_parent_id || 'default',
                  content: {
                    name: payload?.name || 'Step',
                    payload: payload?.payload || 'No details',
                  },
                  time_stamp: payload?.time_stamp || 'default',
                  index: counter++,
                };
                const msg = `<intermediatestep>${JSON.stringify(intermediateMessage)}</intermediatestep>`;
                controller.enqueue(encoder.encode(msg));
              } catch {}
            }
          }
        }
      } finally {
        if (!finalAnswerSent) {
          try {
            const parsed = JSON.parse(streamContent);
            const value =
              parsed?.value ||
              parsed?.output ||
              parsed?.answer ||
              parsed?.choices?.[0]?.message?.content;
            if (value && typeof value === 'string') {
              controller.enqueue(encoder.encode(value.trim()));
              finalAnswerSent = true;
            }
          } catch {}
        }
        controller.close();
        reader?.releaseLock();
      }
    },
  });
}

async function processChatStream(response: Response, encoder: TextEncoder, decoder: TextDecoder, additionalProps: any): Promise<ReadableStream<Uint8Array>> {
  const reader = response?.body?.getReader();
  let buffer = '';
  let counter = 0;

  return new ReadableStream({
    async start(controller) {
      try {
        while (true) {
          const { done, value } = await reader!.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;

          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(5);
              if (data.trim() === '[DONE]') {
                controller.close();
                return;
              }
              try {
                const parsed = JSON.parse(data);
                const content =
                  parsed.choices?.[0]?.message?.content ||
                  parsed.choices?.[0]?.delta?.content;
                if (content) {
                  controller.enqueue(encoder.encode(content));
                }
              } catch {}
            } else if (
              line.startsWith('intermediate_data: ') &&
              additionalProps.enableIntermediateSteps
            ) {
              try {
                const data = line.split('intermediate_data: ')[1];
                const payload = JSON.parse(data);
                const intermediateMessage = {
                  id: payload?.id || '',
                  status: payload?.status || 'in_progress',
                  error: payload?.error || '',
                  type: 'system_intermediate',
                  parent_id: payload?.parent_id || 'default',
                  intermediate_parent_id: payload?.intermediate_parent_id || 'default',
                  content: {
                    name: payload?.name || 'Step',
                    payload: payload?.payload || 'No details',
                  },
                  time_stamp: payload?.time_stamp || 'default',
                  index: counter++,
                };
                const msg = `<intermediatestep>${JSON.stringify(intermediateMessage)}</intermediatestep>`;
                controller.enqueue(encoder.encode(msg));
              } catch {}
            }
          }
        }
      } finally {
        controller.close();
        reader?.releaseLock();
      }
    },
  });
}

const handler = async (req: Request): Promise<Response> => {
  try {
    const requestBody = await req.json();
    
    const {
      chatCompletionURL = 'http://127.0.0.1:8001/chat/stream',
      messages = [],
      additionalProps = { enableIntermediateSteps: true },
    } = requestBody as ChatBody;

    // Extract the user message from the messages array
    const lastMessage = messages?.at(-1);
    const userMessage = lastMessage?.content;
    
    if (!userMessage && !lastMessage?.attachments?.length) {
      return new Response('No message or attachment provided', { status: 400 });
    }

    // Check if the message has image attachments
    const hasImage = lastMessage?.attachments?.some((att: any) => att.type === 'image');
    let payload = { message: userMessage };

    // If there's an image, perform color analysis first
    if (hasImage && lastMessage?.attachments) {
      const imageAttachment = lastMessage.attachments.find((att: any) => att.type === 'image');
      if (imageAttachment?.content) {
        try {
          // Perform color analysis
          const colorAnalysisResponse = await fetch('http://127.0.0.1:8001/analyze-image-base64', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              image_data: imageAttachment.content,
              num_colors: 5
            }),
          });

          if (colorAnalysisResponse.ok) {
            const colorData = await colorAnalysisResponse.json();
            
            // Generate palette suggestions
            const paletteResponse = await fetch('http://127.0.0.1:8001/color/palette', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                base_color: colorData.colors[0]?.hex_code || '#3498DB',
                scheme: 'complementary',
                num_colors: 5
              }),
            });

            let paletteData = null;
            if (paletteResponse.ok) {
              paletteData = await paletteResponse.json();
            }

            // Generate annotated image
            let annotatedImageData = null;
            try {
              const annotateResponse = await fetch('http://127.0.0.1:8001/annotate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  image_url: imageAttachment.content,
                  colors: colorData.colors.map((color: any) => ({
                    hex: color.hex_code,
                    rgb: [
                      parseInt(color.hex_code.slice(1, 3), 16),
                      parseInt(color.hex_code.slice(3, 5), 16),
                      parseInt(color.hex_code.slice(5, 7), 16)
                    ],
                    proportion: color.percentage
                  }))
                }),
              });

              if (annotateResponse.ok) {
                annotatedImageData = await annotateResponse.json();
              }
            } catch (error) {
              console.error('Image annotation failed:', error);
            }

            // Enhance the message with color analysis results and annotated image
            const colorAnalysisText = `
📸 **图片颜色分析完成**

🎨 **提取的颜色：**
${colorData.colors.map((color: any, i: number) => 
  `${i+1}. ${color.hex_code} (${color.color_name}, ${(color.percentage * 100).toFixed(1)}%)`
).join('\n')}

⚡ **处理信息：**
- 处理时间: ${colorData.processing_time_ms.toFixed(1)}ms
- 算法: ${colorData.algorithm_used}
- 图片尺寸: ${colorData.image_dimensions.width} × ${colorData.image_dimensions.height}

${paletteData ? `🎯 **推荐配色方案** (${paletteData.palette?.palette_type || '互补色'}):
${paletteData.palette?.colors?.join(', ') || ''}
和谐度: ${((paletteData.palette?.harmony_score || 0) * 100).toFixed(0)}%
` : ''}

${annotatedImageData?.success ? `🖼️ **颜色标注图已生成**
![颜色标注图](${annotatedImageData.annotated_image})

📊 **标注信息：**
- 布局: ${annotatedImageData.processing_info.layout}
- 功能: ${annotatedImageData.processing_info.features.join(', ')}
- 最终尺寸: ${annotatedImageData.processing_info.final_size}
` : ''}

${userMessage ? `💬 **用户问题:** ${userMessage}` : ''}`;

            payload = { message: colorAnalysisText };
          }
        } catch (error) {
          console.error('Color analysis failed:', error);
          payload = { message: `${userMessage}\n\n[图片颜色分析失败，但我仍然可以帮助您]` };
        }
      }
    }

    // Use the configured URL or fallback to our backend
    const backendURL = chatCompletionURL || 'http://127.0.0.1:8001/chat/stream';

    const response = await fetch(backendURL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.text();
      return new Response(`Backend Error: ${error}`, { status: 500 });
    }

    // If it's a stream endpoint, process the SSE format
    if (backendURL.includes('stream')) {
      const readable = new ReadableStream({
        async start(controller) {
          const reader = response.body?.getReader();
          if (!reader) return;

          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              // Convert the chunk to text and process SSE format
              const chunk = new TextDecoder().decode(value);
              const lines = chunk.split('\n');
              
              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const data = JSON.parse(line.slice(6));
                    const content = data.choices?.[0]?.delta?.content || '';
                    if (content) {
                      controller.enqueue(new TextEncoder().encode(content));
                    }
                  } catch (e) {
                    // Skip invalid JSON lines
                  }
                }
              }
            }
          } finally {
            controller.close();
            reader.releaseLock();
          }
        },
      });

      return new Response(readable, {
        headers: {
          'Content-Type': 'text/plain; charset=utf-8',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      });
    } else {
      // For non-stream endpoints, process the response
      const data = await response.json();
      return new Response(data.reply || JSON.stringify(data));
    }
  } catch (error: any) {
    console.error('Chat API Error:', error);
    return new Response(`Server Error: ${error.message}`, { status: 500 });
  }
};

export default handler;
