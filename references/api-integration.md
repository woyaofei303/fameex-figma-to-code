# Server-Backed Interface Integration

Load only when the selected Figma node or existing branch contains a real query, mutation, upload, or backend-owned status. This reference supplements the visual workflow; it does not authorize an endpoint or invent a contract.

## Contract Manifest

Complete one entry for each independently owned server interaction before editing UI code. Use `unresolved` for missing facts and keep dependent controls unavailable until they are established.

```yaml
consumer_app: apps/admin | apps/web | apps/futures-admin | legacy-admin
route: <owning route>
source_of_truth: <PRD, backend contract, real payload, existing service, or user correction>
endpoint: <exact path>
method: GET | POST | PUT | PATCH | DELETE
proxy_prefix: <required app prefix or none>
auth_scope: <session/origin/role assumptions and observed result>
request_query_or_body: <field names, types, omission rules, encoding>
response_fields: <raw fields actually consumed>
inbound_normalization: <API to UI conversion at the boundary>
outbound_normalization: <UI to API conversion at the boundary>
query_key: <identity fields and tab/market/filter/page inputs>
enabled_condition: <route, active tab, prerequisites, and permission gates>
mutation_refresh: <exact invalidation, refetch, cache update, or none>
loading_error_empty_states: <observable UI behavior for each applicable state>
verification: <focused test plus browser/network evidence>
```

The manifest is an evidence record, not a design proposal. Figma sample rows, labels, pair names, and unlocked controls do not establish API values, permissions, or enum meanings.

## Integration Sequence

1. Identify the consumer app and route before choosing a service. A service in another FameEX app is a candidate dependency, not proof that its authentication, proxy, or response shape is compatible.
2. Trace the request from component or hook through the shared transport. Confirm prefix handling, credentials, request encoding, and whether the transport unwraps or transforms responses.
3. Preserve backend identity values internally. Normalize labels only at the display or request boundary; never derive mutation identifiers from formatted text.
4. Give each list query a key containing every value that changes its result. Gate it with the route/tab prerequisites in `enabled_condition` so inactive tabs do not issue requests.
5. Keep sibling tabs' filters and pagination independent unless the product contract explicitly shares them. A filter change resets only the affected pagination. Reuse the owning Admin page's field/control width pattern across sibling tabs; do not introduce a feature-global magic width from one screenshot.
6. On mutation success, refresh only the affected data using the repository's established invalidation or refetch pattern. On failure, retain actionable form state and established feedback.
7. Model loading, error, empty, disabled, and unavailable states. Do not replace missing contracts or failed authorization with mock data, hard-coded pairs, or false success.

## Uploads and Multipart Requests

- Confirm the endpoint, multipart field names, accepted response field, file restrictions, and final submission behavior independently.
- Use `FormData` when contracted. Do not manually force `Content-Type: multipart/form-data` in the browser unless the repository transport generates the boundary and network evidence proves it.
- Confirm whether the shared fetch layer returns the raw payload, `data`, or another normalized shape before reading fields.
- Do not invent MIME, size, dimension, count, or validation limits from the Figma frame.

## Focused Verification

Automated coverage should prove, where applicable:

- Exact endpoint, method, request fields, encoding, and boundary normalization.
- Query keys and `enabled` gates, including no inactive-tab request.
- Independent tab/filter/pagination state and affected-page reset.
- Mutation payload identity and affected-list invalidation or refetch.
- Loading, error, empty, disabled, retry, and duplicate-request behavior.
- Upload field names, response unwrapping, and no unsafe fixed multipart header.

In the real owning app/session, capture sanitized browser evidence for method, path, query/body field names, status, response keys consumed by the adapter, and post-mutation refresh. Never record credentials, cookies, tokens, personal data, or file binary.

## Quick Reference

```text
Authority: real payload/user correction > backend contract/PRD > repository behavior > Figma samples
Cross-app endpoint: verify auth, origin, proxy, schema, and semantics in the consumer app
Queries: complete key + explicit enabled gate + independent tab state
Mutations: exact identity + pending/error behavior + affected refresh only
Uploads: FormData field contract + transport unwrapping + browser-generated boundary
UI filters: owning-app pattern + sibling-tab consistency + no one-frame magic width
Evidence: focused test + owning-package command + sanitized network/state proof
```

## Common Mistakes

- Copying an endpoint prefix, enum number, pair formatter, or width from one PR without checking the current consumer app.
- Importing another app's UI/store code because its endpoint looks reusable.
- Running Admin tests from the workspace root and accepting a result produced with the Web alias configuration.
- Omitting tab/market/filter inputs from a query key or allowing inactive tabs to query.
- Optimistically closing a form without proving the mutation refreshes the visible list.
- Treating a transport-transformed payload as the raw backend response.
