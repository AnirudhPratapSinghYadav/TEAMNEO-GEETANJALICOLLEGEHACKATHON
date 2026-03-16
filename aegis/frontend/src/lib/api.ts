const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface TestPromptRequest {
  prompt: string;
  department?: string;
  user_name?: string;
  model?: string;
}

export interface DetectedItem {
  type: string;
  value?: string;
  confidence?: number;
}

export interface TestPromptResponse {
  request_id: string;
  decision: "APPROVE" | "REDACT" | "BLOCK" | "ESCALATE" | "TRANSFORM";
  risk_score: number;
  risk_level: "NONE" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  detections: DetectedItem[];
  explanation?: string;
  redacted_prompt?: string;
}

export async function testPrompt(
  payload: TestPromptRequest
): Promise<TestPromptResponse> {
  const response = await fetch(`${API_BASE_URL}/api/admin/test-prompt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<TestPromptResponse>;
}
