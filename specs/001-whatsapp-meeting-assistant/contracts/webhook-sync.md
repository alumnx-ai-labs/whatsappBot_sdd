# Contract: `POST /webhook-sync`

Owner: Backend WhatsApp Webhook Controller. This is the **only** entrypoint for customer conversations.
The React frontend never calls this endpoint.

## Accepted request shapes

The controller MUST accept both shapes and normalize to one internal representation before any further
processing (research.md item 7).

### Shape A — Approved normalized contract

```json
{
  "phone": "+919494151816",
  "text": "Hello Oscar",
  "message_id": "a-unique-id-per-inbound-message"
}
```

### Shape B — Raw SkaleBot payload

```json
{
  "query": "hi",
  "callback": "",
  "mediaUrl": "",
  "phoneNumber": "919949014298"
}
```

Field mapping: `query → text`, `phoneNumber → phone`. `message_id` is absent in this shape; the
normalizer derives a fallback idempotency key as defined by the approved provider delivery contract.

## Normalization pipeline (in order)

1. **Validate payload**: request body must match Shape A or Shape B (server-side schema validation); anything
   else → `400 Bad Request` with no processing.
2. **Normalize payload** to `{ phone, text, messageId }`.
3. **Normalize phone number** to canonical E.164 (research.md item 6). Malformed/unparseable phone →
   `400 Bad Request` (never guessed, per spec edge cases).
4. **Check message idempotency**: look up `InboundMessage` by `messageId`.
   - If found: return the previously stored `cachedResponse` verbatim. No agent invocation, no booking
     side effects.
   - If not found: insert a new `InboundMessage` row (`processingStatus = RECEIVED`) and continue.
5. **Determine message ownership** (research.md item 8):
   - If not owned by this bot → respond `{ "handled": false }`, mark `InboundMessage.processingStatus =
     PROCESSED`, cache that response, stop.
   - If owned → continue.
6. **Load or create active ConversationSession** for the canonical phone.
7. **Identify returning vs. new visitor** (Customer lookup by canonical phone).
8. **Invoke LangChain Agent** with current session context + normalized text.
9. **Apply deterministic Business Rules** to the agent's structured output (confirmation checks,
   validation, state-machine transition eligibility).
10. **Update ConversationSession** state/context.
11. **If booking required**: invoke Booking Service → Hello Oscar Adapter → persist result
    (`BookingStateTransition` logged for every step).
12. **Generate WhatsApp reply** (via agent's reply-generation responsibility, constrained to the final
    deterministic outcome — never a pre-Hello-Oscar "confirmed" message).
13. **Persist `InboundMessage.cachedResponse`**, set `processingStatus = PROCESSED`.
14. **Return** `{ "handled": true, "reply": "<assistant response>" }`.

## Response contracts

### Handled

```json
{
  "handled": true,
  "reply": "Hi. Looks like you've visited here for the first time.\n\nPlease share your name and business name."
}
```

### Not handled (shared-number rule)

```json
{ "handled": false }
```

## Ownership rule (explicit)

`handled: true` is returned **only** when:
- An active `ConversationSession` already exists for the canonical phone (owned by this bot), **or**
- The message matches the approved, case-insensitive first-contact routing trigger `Hello Oscar`.

Generic greetings (`hi`, `hello`, `hie`, and equivalents) with **no** active session **MUST** return
`{ "handled": false }`. This is enforced as a business rule, not left to LangChain agent judgment.

## Error handling

- Invalid/unparseable payload: `400`, `{"handled": false}` is NOT returned for malformed requests — this
  is a hard validation failure, distinct from the "not owned" business outcome. Response body:
  `{ "error": "invalid_payload", "details": [...] }`.
- Unexpected internal failure after ownership is confirmed: respond `500` (SkaleBot/WhatsApp layer is
  expected to retry; idempotency ledger prevents duplicate side effects on retry). Never respond with a
  fabricated `reply` claiming success.

## Traceability

FR-001, FR-001a, FR-002–FR-014, FR-024, NFR-001, NFR-002, NFR-006, spec Edge Cases (duplicate delivery,
shared-number ownership, malformed phone).
