use axum::{
    routing::{get, post},
    Router, Json, extract::Multipart, response::IntoResponse,
};
use std::net::SocketAddr;
use tower_http::cors::CorsLayer;
use serde_json::json;

#[tokio::main]
async fn main() {
    // Initialize logging
    env_logger::init();

    // Define routes
    let app = Router::new()
        .route("/health", get(health_check))
        .route("/api/analyze-brief", post(analyze_brief))
        .layer(CorsLayer::permissive());

    // Run server
    let addr = SocketAddr::from(([0, 0, 0, 0], 8080));
    println!("Rust API Service listening on {}", addr);
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn health_check() -> impl IntoResponse {
    Json(json!({ "status": "ok", "service": "legal-judge-api-rust" }))
}

#[derive(serde::Serialize, serde::Deserialize)]
struct AnalyzeResponse {
    ocr_text: String,
    predicted_outcome: OutcomePrediction,
    top_cases: Vec<CaseResult>,
    judge_opinion: String,
}

#[derive(serde::Serialize, serde::Deserialize)]
struct OutcomePrediction {
    label: String,
    probabilities: std::collections::HashMap<String, f64>,
}

#[derive(serde::Serialize, serde::Deserialize)]
struct CaseResult {
    case_name: String,
    citation: String,
    relevance_score: f64,
    snippet: String,
}

async fn analyze_brief(mut multipart: Multipart) -> impl IntoResponse {
    println!("Received analysis request...");
    
    // 1. Extract PDF from multipart
    let mut pdf_bytes = Vec::new();
    while let Some(field) = multipart.next_field().await.unwrap() {
        if field.name() == Some("file") {
            if let Ok(bytes) = field.bytes().await {
                pdf_bytes = bytes.to_vec();
                println!("Got PDF bytes: {} bytes", pdf_bytes.len());
            }
        }
    }

    if pdf_bytes.is_empty() {
        return Json(json!({ "error": "No file uploaded" })).into_response();
    }

    // 2. Call Python OCR Service
    let client = reqwest::Client::new();
    // Assuming OCR service runs on port 8000
    let part = reqwest::multipart::Part::bytes(pdf_bytes)
        .file_name("brief.pdf")
        .mime_str("application/pdf")
        .unwrap();
    
    let form = reqwest::multipart::Form::new().part("file", part);

    println!("Sending to OCR service...");
    // Mocking response for now if OCR is down
    let ocr_text = match client.post("http://localhost:8000/ocr/pdf")
        .multipart(form)
        .send()
        .await {
            Ok(resp) => {
                if let Ok(json) = resp.json::<serde_json::Value>().await {
                    json["full_text"].as_str().unwrap_or("No text returned").to_string()
                } else {
                    "OCR Failed to parse JSON".to_string()
                }
            },
            Err(e) => {
                println!("OCR Service Error: {}", e);
                "Error contacting OCR service (Is it running?). Using mock text.".to_string()
            }
        };

    println!("OCR Complete. Length: {}", ocr_text.len());

    // 3. (Todo) Vector Search & Prediction
    // Returning dummy data for Phase 2A demo
    let response = AnalyzeResponse {
        ocr_text: ocr_text.chars().take(500).collect::<String>() + "...", // Truncate for preview
        predicted_outcome: OutcomePrediction {
            label: "PLAINTIFF_WINS".to_string(),
            probabilities: std::collections::HashMap::from([
                ("PLAINTIFF_WINS".to_string(), 0.85),
                ("DEFENDANT_WINS".to_string(), 0.10),
                ("MIXED".to_string(), 0.05),
            ]),
        },
        top_cases: vec![
            CaseResult {
                case_name: "Hilder v. St. Peter".to_string(),
                citation: "478 A.2d 202 (Vt. 1984)".to_string(),
                relevance_score: 0.92,
                snippet: "Implied warranty of habitability exists in every residential lease...".to_string(),
            },
            CaseResult {
                case_name: "Javins v. First National Realty".to_string(),
                citation: "428 F.2d 1071".to_string(),
                relevance_score: 0.88,
                snippet: "Leases of urban dwellings contain implied warranty...".to_string(),
            }
        ],
        judge_opinion: "Based on the precedents of Hilder and Javins, the court finds that the landlord breach...".to_string(),
    };

    Json(response).into_response()
}
