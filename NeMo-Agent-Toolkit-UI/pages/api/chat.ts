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

    // If there's an image, include it in the message for intelligent NIM processing
    if (hasImage && lastMessage?.attachments) {
      const imageAttachment = lastMessage.attachments.find((att: any) => att.type === 'image');
      if (imageAttachment?.content) {
        // Include image data in the message for backend processing
        payload = { 
          message: `${userMessage} ${imageAttachment.content}` 
        };
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
