export interface Notebook {
  id: string
  name: string
  description?: string
  sources_count: number
  created_at: string
  updated_at: string
}

// Category Assignment for documents
export interface CategoryAssignment {
  category: string
  score: number
  confidence: 'high' | 'medium' | 'low'
  is_auto: boolean
  suggested?: string
}

export interface Document {
  id: string
  notebook_id: string
  filename: string
  file_type: string
  chunks_count: number
  status: string
  summary?: string
  key_topics?: string[]
  categories?: CategoryAssignment[]
  created_at: string
}

// Web search source
export interface WebSource {
  title: string
  url: string
  content: string
  score: number
}

// Enhanced Citation with file-type-specific metadata
export interface Citation {
  citation_id: number
  document_id: string
  filename: string
  file_type: string
  raw_text: string
  chunk_index: number
  relevance_score: number
  citation_text: string
  source_type?: string

  // PDF fields
  page_number?: number
  paragraph_start?: number
  paragraph_end?: number

  // DOCX fields
  heading?: string
  heading_level?: number
  section_path?: string
  is_table?: boolean
  table_name?: string

  // TXT fields
  line_start?: number
  line_end?: number

  // Position fields
  char_start?: number
  char_end?: number
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  citations?: Citation[]
  web_sources?: WebSource[]
  timestamp: string
}

export interface Source {
  document_id: string
  filename: string
  chunk_index: number
  score: number
  source_type?: 'document' | 'web'
}

// Notebook Overview
export interface NotebookOverview {
  notebook_id: string
  notebook_name: string
  overview: string
  suggested_questions: string[]
  total_sources: number
  main_topics: string[]
  documents: DocumentSummary[]
  cached?: boolean
}

export interface DocumentSummary {
  id: string
  filename: string
  summary: string
  key_topics: string[]
  categories: CategoryAssignment[]
}

// Category info
export interface CategoryInfo {
  name: string
  description: string
  type: 'ACM' | 'Extended' | 'Custom'
  keywords: string[]
}

export interface Quiz {
  id: string
  notebook_id: string
  total_questions: number
  difficulty: 'easy' | 'medium' | 'hard'
  questions: Question[]
  created_at: string
}

export interface Question {
  id: string
  question: string
  options: string[]
  correct_answer: string
  explanation: string
}

export interface QuizResult {
  quiz_id: string
  score: number
  correct_count: number
  total_questions: number
  results: QuestionResult[]
}

export interface QuestionResult {
  question_id: string
  user_answer: string
  correct_answer: string
  is_correct: boolean
}

export interface ChatResponse {
  response: string
  sources: Source[]
  citations?: Citation[]
  web_sources?: WebSource[]
  metadata?: Record<string, any>
}

export interface SummaryResponse {
  summary: string
  key_points: string[]
  word_count: number
}

export interface ApiError {
  detail: string
  status_code: number
}
