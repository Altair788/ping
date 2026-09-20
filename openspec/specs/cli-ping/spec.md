# cli-ping Specification

## Purpose
Поведенческий контракт CLI-скрипта `ping.py`, измеряющего скорость загрузки данных с указанного URL путём последовательных HTTP GET и печатающего отчёт в человекочитаемом или JSON-формате.

## Requirements

### Requirement: CLI interface
The script SHALL accept `--url` as a required argument and SHALL accept `--count`, `--timeout`, and `--json` as optional arguments. The script SHALL print a usage message and exit with code 2 when invoked with `--help` is not given but no `--url` is provided, or when `--url` is not a syntactically valid HTTP/HTTPS URL.

#### Scenario: Valid invocation with required URL
- **WHEN** user runs `python ping.py --url https://example.com/file.bin`
- **THEN** script proceeds with default `--count` of 10 and default `--timeout` of 10 seconds

#### Scenario: Missing required URL
- **WHEN** user runs `python ping.py` without `--url`
- **THEN** script prints an error to stderr describing the missing argument and exits with code 2

#### Scenario: Invalid URL scheme
- **WHEN** user runs `python ping.py --url file:///etc/passwd`
- **THEN** script prints an error indicating only http/https URLs are accepted and exits with code 2

#### Scenario: Non-URL string
- **WHEN** user runs `python ping.py --url "not a url"`
- **THEN** script prints an error indicating the value is not a valid URL and exits with code 2

#### Scenario: Custom count and timeout
- **WHEN** user runs `python ping.py --url URL --count 3 --timeout 30`
- **THEN** script performs exactly 3 requests with a 30-second per-request timeout

### Requirement: Sequential measurement
The script SHALL perform exactly `--count` HTTP GET requests to the specified URL, executed sequentially in a single connection lifecycle. The script SHALL NOT pipeline, multiplex, or parallelize the requests.

#### Scenario: Default count of 10
- **WHEN** user runs `python ping.py --url URL` without `--count`
- **THEN** script performs exactly 10 sequential GET requests before printing the report

#### Scenario: Timing of one request covers full body transfer
- **WHEN** script measures a single request
- **THEN** the recorded duration covers from the moment the request is initiated until the last byte of the response body has been received by the client

### Requirement: Per-request measurement
For each successful request, the script SHALL record the number of bytes received in the response body and the elapsed time in seconds. The script SHALL NOT count response headers, framing overhead, or TLS handshake bytes toward the recorded bytes for the purpose of throughput calculation.

#### Scenario: Bytes counted are response body only
- **WHEN** script receives a successful response
- **THEN** recorded `bytes` equals the length of the response body as reported by the server or the number of body bytes actually read, whichever is smaller

### Requirement: Partial failure handling
If a single request fails (DNS resolution failure, connection refused, timeout, non-2xx status, or any other error), the script SHALL record the failure, SHALL continue with the remaining requests, and SHALL include the failure count in the report. The script SHALL NOT abort the entire measurement on the first failure.

#### Scenario: One request fails mid-measurement
- **WHEN** request #3 of 10 fails with a timeout
- **THEN** script continues with requests #4..#10 and reports 1 failed request

#### Scenario: All requests fail
- **WHEN** every one of the 10 requests fails
- **THEN** script prints a report indicating all requests failed and prints the last observed error message

### Requirement: Human-readable report
When `--json` is not provided, the script SHALL print a human-readable report to stdout containing: the per-request outcomes (numbered), the total bytes downloaded, the total elapsed time, the aggregate throughput in MB/s, and the per-request throughput statistics (minimum, maximum, mean in MB/s). Failed requests SHALL be listed with their error message.

#### Scenario: Human report on full success
- **WHEN** all 10 requests succeed and `--json` is not set
- **THEN** stdout contains a numbered list of 10 per-request results, a summary line with aggregate MB/s, and a summary line with min/max/mean

#### Scenario: Human report with one failure
- **WHEN** 9 requests succeed and 1 fails and `--json` is not set
- **THEN** stdout contains 9 numbered per-request results, an explicit entry for the failed request with its error, and a summary indicating "1 of 10 failed"

### Requirement: Machine-readable report
When `--json` is provided, the script SHALL print a single JSON object to stdout with all report fields encoded as numbers or strings, suitable for programmatic consumption. The script SHALL NOT mix human-readable text with JSON output.

#### Scenario: JSON output structure
- **WHEN** user runs `python ping.py --url URL --json`
- **THEN** stdout contains exactly one parseable JSON object with fields: url, count, succeeded, failed, total_bytes, total_time_s, aggregate_mbps, per_request_mbps (array of numbers, one per successful request)

### Requirement: Exit codes
The script SHALL exit with code 0 when all requested measurements succeed. The script SHALL exit with code 1 when at least one requested measurement fails (regardless of how many succeeded). The script SHALL exit with code 2 when input validation fails before any HTTP request is attempted.

#### Scenario: Exit 0 on full success
- **WHEN** all `--count` requests succeed
- **THEN** script exits with code 0

#### Scenario: Exit 1 on partial failure
- **WHEN** at least one of the `--count` requests fails and at least one succeeds
- **THEN** script exits with code 1

#### Scenario: Exit 2 on invalid URL
- **WHEN** `--url` fails validation
- **THEN** script exits with code 2 and no HTTP request is attempted
