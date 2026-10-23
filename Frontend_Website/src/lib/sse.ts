import { API_BASE_URL } from './api';

export interface SseDoubtChunk {
  id: string;
  stage: 'analyzing' | 'reasoning' | 'solution' | string;
  delta: string;
}

export interface StreamStageEvent {
  stage: number;
  status: string;
}

export async function streamDoubtSolution(
  payload: {
    query: string;
    subject: string;
    exam?: string;
    language?: string;
    mode?: 'socratic_hint' | 'step_by_step';
  },
  onChunk: (chunk: SseDoubtChunk) => void,
  onDone: () => void,
  onError: (err: string) => void
): Promise<void> {
  try {
    const token = localStorage.getItem('eklavya_token');
    const res = await fetch(`${API_BASE_URL}/api/ai-hub/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok || !res.body) {
      throw new Error(`Stream error: HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data:')) continue;
        const dataStr = trimmed.slice(5).trim();
        if (dataStr === '[DONE]') {
          onDone();
          return;
        }
        try {
          const parsed = JSON.parse(dataStr);
          onChunk(parsed);
        } catch {
          // ignore malformed line
        }
      }
    }
    onDone();
  } catch (err: any) {
    onError(err?.message || 'Failed to stream Socratic explanation');
  }
}

export async function streamDoubtSolver(
  payload: {
    studentId: string;
    prompt: string;
    subject: string;
    language?: string;
  },
  callbacks: {
    onStage: (st: StreamStageEvent) => void;
    onToken: (tk: { text: string }) => void;
    onDone: () => void;
  }
): Promise<void> {
  try {
    const token = localStorage.getItem('eklavya_token');
    const res = await fetch(`${API_BASE_URL}/api/ai-hub/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok || !res.body) {
      throw new Error(`Stream error: HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data:')) continue;
        const dataStr = trimmed.slice(5).trim();
        if (dataStr === '[DONE]') {
          callbacks.onDone();
          return;
        }
        try {
          const parsed = JSON.parse(dataStr);
          if (parsed.stage && parsed.status) {
            callbacks.onStage({ stage: Number(parsed.stage), status: parsed.status });
          }
          if (parsed.text) {
            callbacks.onToken({ text: parsed.text });
          } else if (parsed.delta) {
            callbacks.onToken({ text: parsed.delta });
          }
        } catch {
          // ignore malformed line
        }
      }
    }
    callbacks.onDone();
  } catch {
    callbacks.onDone();
  }
}
