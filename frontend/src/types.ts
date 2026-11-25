export interface Column {
  name: string;
  type: string;
}

export interface QueryResult {
  columns: Column[];
  rows: string[][];
  row_count: number;
  truncated: boolean;
}

export interface GenieStatus {
  status: string;
  text: string | null;
  description: string | null;
  sql: string | null;
  statement_id: string | null;
  attachment_id: string | null;
  result: QueryResult | null;
  tables_used: string[];
  suggested_questions: string[];
  error: string | null;
}

export interface AskResponse {
  conversation_id: string;
  message_id: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  genieStatus?: GenieStatus;
  startedAt?: number;
  completedAt?: number;
}

export interface Conversation {
  id: string | null;
  title: string;
  messages: Message[];
}

export interface TableInfo {
  name: string;
  type: string;
  column_count: number;
  comment: string;
}

export interface SpaceInfo {
  space_id: string;
  space_name: string;
  description: string;
  catalog: string;
  tables: TableInfo[];
}
