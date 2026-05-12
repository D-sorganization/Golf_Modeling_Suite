//! Integration tests for the LLM HTTP roundtrip and SSE streaming.
//!
//! Uses `wiremock` to stand up an in-process OpenAI-compatible mock so we
//! exercise the full reqwest -> response-parsing path without hitting a
//! real provider.

use ai_backend::config::AIConfig;
use ai_backend::llm::AIEngine;
use wiremock::matchers::{method, path};
use wiremock::{Mock, MockServer, ResponseTemplate};

#[tokio::test(flavor = "multi_thread")]
async fn chat_completion_roundtrip_parses_choices() {
    let server = MockServer::start().await;
    Mock::given(method("POST"))
        .and(path("/v1/chat/completions"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "id": "chatcmpl-xyz",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "hello world"},
                "finish_reason": "stop"
            }]
        })))
        .mount(&server)
        .await;

    let mut cfg = AIConfig::try_new(
        "test-key".into(),
        format!("{}/v1", server.uri()),
        "gpt-test".into(),
        ":memory:".into(),
    )
    .unwrap();
    // Default chat_path is /chat/completions — that's exactly what we want.
    let _ = &mut cfg;

    // We can't run AIEngine::try_generate_response inside a tokio test (it
    // builds its own runtime via block_on). Spawn it on a blocking thread.
    let result = tokio::task::spawn_blocking(move || {
        let engine = AIEngine::try_new(cfg).unwrap();
        engine.try_generate_response("ping".into())
    })
    .await
    .unwrap();

    assert_eq!(result.unwrap(), "hello world");
}

#[tokio::test(flavor = "multi_thread")]
async fn chat_completion_http_error_surfaces() {
    let server = MockServer::start().await;
    Mock::given(method("POST"))
        .and(path("/v1/chat/completions"))
        .respond_with(ResponseTemplate::new(401).set_body_string("unauthorized"))
        .mount(&server)
        .await;

    let cfg = AIConfig::try_new(
        "bad-key".into(),
        format!("{}/v1", server.uri()),
        "gpt-test".into(),
        ":memory:".into(),
    )
    .unwrap();

    let result = tokio::task::spawn_blocking(move || {
        let engine = AIEngine::try_new(cfg).unwrap();
        engine.try_generate_response("ping".into())
    })
    .await
    .unwrap();

    let err = result.unwrap_err();
    assert!(err.contains("401"), "expected 401 in error, got: {}", err);
}

#[tokio::test(flavor = "multi_thread")]
async fn stream_response_parses_sse_deltas() {
    let server = MockServer::start().await;

    // Build a fake SSE body. The mock server replays it verbatim; reqwest
    // sees it as a chunked HTTP/1.1 stream because wiremock uses hyper.
    let sse_body = concat!(
        "data: {\"choices\":[{\"delta\":{\"content\":\"Hel\"}}]}\n\n",
        "data: {\"choices\":[{\"delta\":{\"content\":\"lo \"}}]}\n\n",
        "data: {\"choices\":[{\"delta\":{\"content\":\"world\"}}]}\n\n",
        "data: [DONE]\n\n",
    );

    Mock::given(method("POST"))
        .and(path("/v1/chat/completions"))
        .respond_with(
            ResponseTemplate::new(200)
                .set_body_string(sse_body)
                .insert_header("content-type", "text/event-stream"),
        )
        .mount(&server)
        .await;

    let cfg = AIConfig::try_new(
        "test-key".into(),
        format!("{}/v1", server.uri()),
        "gpt-test".into(),
        ":memory:".into(),
    )
    .unwrap();

    let deltas = tokio::task::spawn_blocking(move || {
        let engine = AIEngine::try_new(cfg).unwrap();
        engine.try_stream_response("ping".into())
    })
    .await
    .unwrap()
    .unwrap();

    assert_eq!(deltas, vec!["Hel", "lo ", "world"]);
}
