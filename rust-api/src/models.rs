/// Rust data models matching Python Pydantic schemas
/// These models ensure type-safe communication between Rust API gateway and Python services

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CaseLawDocument {
    pub case_name: String,
    pub year: i32,
    pub court: String,
    pub opinion_type: String,
    pub facts: String,
    pub issue: String,
    pub reasoning: String,
    pub holding: String,
    pub final_judgment: String,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub case_number: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub petitioner: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub respondent: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub lower_court: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub procedural_history: Option<String>,
    
    pub document_id: String,
    pub ingestion_timestamp: String,
    pub validation_status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchRequest {
    pub query: String,
    #[serde(default = "default_top_k")]
    pub top_k: i32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub section_filter: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub year_range: Option<Vec<i32>>,
    #[serde(default = "default_min_similarity")]
    pub min_similarity: f64,
}

fn default_top_k() -> i32 { 10 }
fn default_min_similarity() -> f64 { 0.6 }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    pub case_name: String,
    pub year: i32,
    pub court: String,
    pub section_type: String,
    pub similarity_score: f64,
    pub snippet: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub full_document: Option<CaseLawDocument>,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResponse {
    pub status: String,
    pub query: String,
    pub results: Vec<SearchResult>,
    pub total_results: usize,
    pub search_time_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PredictionRequest {
    pub facts: String,
    pub issue: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutcomePrediction {
    pub outcome: String,
    pub probabilities: HashMap<String, f64>,
    pub confidence: f64,
    pub supporting_cases: Vec<String>,
    pub explanation: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PredictionResponse {
    pub status: String,
    pub predicted_outcome: String,
    pub probabilities: HashMap<String, f64>,
    pub confidence: f64,
    pub supporting_cases: Vec<SupportingCase>,
    pub explanation: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SupportingCase {
    pub case_name: String,
    pub year: i32,
    pub similarity_score: f64,
    pub outcome: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OpinionRequest {
    pub case_context: CaseContext,
    #[serde(default = "default_opinion_type")]
    pub opinion_type: String,
    #[serde(default = "default_max_precedents")]
    pub max_precedents: i32,
}

fn default_opinion_type() -> String { "per_curiam".to_string() }
fn default_max_precedents() -> i32 { 5 }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CaseContext {
    pub case_number: String,
    pub petitioner: String,
    pub respondent: String,
    pub lower_court: String,
    pub facts: String,
    pub issue: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub procedural_history: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeneratedOpinion {
    pub full_text: String,
    pub sections: HashMap<String, String>,
    pub cited_precedents: Vec<String>,
    pub generation_metadata: HashMap<String, serde_json::Value>,
    pub disclaimer: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OpinionResponse {
    pub status: String,
    pub opinion: GeneratedOpinion,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IngestionResult {
    pub document_id: String,
    pub case_name: String,
    pub status: String,
    pub sections_extracted: Vec<String>,
    pub validation_errors: Vec<String>,
    pub processing_time_seconds: f64,
    pub vector_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub service: String,
    pub version: String,
    pub components: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatsResponse {
    pub total_cases_indexed: i64,
    pub vector_index_size_mb: i64,
    pub total_searches_performed: i64,
    pub total_opinions_generated: i64,
    pub average_search_time_ms: f64,
    pub average_opinion_generation_time_ms: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorResponse {
    pub status: String,
    pub error: String,
    pub details: Option<String>,
}
