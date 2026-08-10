export interface KnownModel {
  name: string;
  repo_id: string;
  filename: string;
  description: string;
}

export interface LocalModel {
  name: string;
  path: string;
  repo_id: string;
  filename: string;
  size_bytes: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}
