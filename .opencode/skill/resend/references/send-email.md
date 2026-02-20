# Send Email with Resend

## Overview

Resend provides two endpoints for sending emails:

| Approach   | Endpoint             | Use Case                                                                  |
| ---------- | -------------------- | ------------------------------------------------------------------------- |
| **Single** | `POST /emails`       | Individual transactional emails, emails with attachments, scheduled sends |
| **Batch**  | `POST /emails/batch` | Multiple distinct emails in one request (max 100), bulk notifications     |

**Choose batch when:**

- Sending 2+ distinct emails at once
- Reducing API calls is important (rate limit: 2 requests/second by default)
- No attachments or scheduling needed

**Choose single when:**

- Sending one email
- Email needs attachments
- Email needs to be scheduled
- Different recipients need different timing

## Quick Start

1. **Detect project language** from config files (package.json, requirements.txt, go.mod, etc.)
2. **Install SDK** (preferred) or use cURL
3. **Choose single or batch** based on decision matrix above
4. **Implement best practices** - Idempotency keys, error handling, retries

## Single Email

**Endpoint:** `POST /emails` (prefer SDK over cURL)

### Required Parameters

| Parameter        | Type     | Description                                         |
| ---------------- | -------- | --------------------------------------------------- |
| `from`           | string   | Sender address. Format: `"Name <email@domain.com>"` |
| `to`             | string[] | Recipient addresses (max 50)                        |
| `subject`        | string   | Email subject line                                  |
| `html` or `text` | string   | Email body content                                  |

### Optional Parameters

| Parameter      | Type     | Description                       |
| -------------- | -------- | --------------------------------- |
| `cc`           | string[] | CC recipients                     |
| `bcc`          | string[] | BCC recipients                    |
| `reply_to`     | string[] | Reply-to addresses                |
| `scheduled_at` | string   | Schedule send time (ISO 8601)     |
| `attachments`  | array    | File attachments (max 40MB total) |
| `tags`         | array    | Key/value pairs for tracking      |
| `headers`      | object   | Custom headers                    |

### Example (Node.js)

```typescript
import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

const { data, error } = await resend.emails.send(
  {
    from: "Acme <onboarding@resend.dev>",
    to: ["delivered@resend.dev"],
    subject: "Hello World",
    html: "<p>Email body here</p>",
  },
  { idempotencyKey: `welcome-email/${userId}` },
);

if (error) {
  console.error("Failed:", error.message);
  return;
}
console.log("Sent:", data.id);
```

### Example (Python)

```python
import resend
import os

resend.api_key = os.environ["RESEND_API_KEY"]

params: resend.Emails.SendParams = {
    "from": "Acme <onboarding@resend.dev>",
    "to": ["delivered@resend.dev"],
    "subject": "Hello World",
    "html": "<p>Email body here</p>",
}

email = resend.Emails.send(params)
print(email)
```

## Batch Email

**Endpoint:** `POST /emails/batch`

### Limitations

- **No attachments** - Use single sends for emails with attachments
- **No scheduling** - Use single sends for scheduled emails
- **Atomic** - If one email fails validation, the entire batch fails
- **Max 100 emails** per request
- **Max 50 recipients** per individual email in the batch

### Example (Node.js)

```typescript
import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

const { data, error } = await resend.batch.send(
  [
    {
      from: "Acme <notifications@acme.com>",
      to: ["delivered@resend.dev"],
      subject: "Order Shipped",
      html: "<p>Your order has shipped!</p>",
    },
    {
      from: "Acme <notifications@acme.com>",
      to: ["delivered@resend.dev"],
      subject: "Order Confirmed",
      html: "<p>Your order is confirmed!</p>",
    },
  ],
  { idempotencyKey: `batch-orders/${batchId}` },
);

if (error) {
  console.error("Batch failed:", error.message);
  return;
}
console.log(
  "Sent:",
  data.map((e) => e.id),
);
```

## Large Batches (100+ Emails)

For sends larger than 100 emails, chunk into multiple batch requests:

1. **Split into chunks** of 100 emails each
2. **Use unique idempotency keys** per chunk: `<batch-prefix>/chunk-<index>`
3. **Send chunks in parallel** for better throughput
4. **Track results** per chunk to handle partial failures

## Best Practices

### Idempotency Keys

Prevent duplicate emails when retrying failed requests.

| Key Facts           |                                                                  |
| ------------------- | ---------------------------------------------------------------- |
| **Format (single)** | `<event-type>/<entity-id>` (e.g., `welcome-email/user-123`)      |
| **Format (batch)**  | `batch-<event-type>/<batch-id>` (e.g., `batch-orders/batch-456`) |
| **Expiration**      | 24 hours                                                         |
| **Max length**      | 256 characters                                                   |

### Error Handling

| Code     | Action                                            |
| -------- | ------------------------------------------------- |
| 400, 422 | Fix request parameters, don't retry               |
| 401, 403 | Check API key / verify domain, don't retry        |
| 409      | Idempotency conflict - use new key or fix payload |
| 429      | Rate limited - retry with exponential backoff     |
| 500      | Server error - retry with exponential backoff     |

### Retry Strategy

```typescript
async function sendWithRetry(emailData, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    const { data, error } = await resend.emails.send(emailData);

    if (!error) return data;

    // Don't retry client errors
    if (error.statusCode >= 400 && error.statusCode < 500 && error.statusCode !== 429) {
      throw error;
    }

    // Exponential backoff for rate limits and server errors
    const delay = Math.pow(2, i) * 1000;
    await new Promise((r) => setTimeout(r, delay));
  }
  throw new Error("Max retries exceeded");
}
```

## Deliverability

### Required

| Practice                       | Why                                     |
| ------------------------------ | --------------------------------------- |
| **Valid SPF, DKIM, DMARC**     | Authenticate email, prevent spoofing    |
| **Links match sending domain** | Mismatched domains trigger spam filters |
| **Include plain text version** | Accessibility and deliverability        |
| **Avoid "no-reply" addresses** | Use real addresses for trust signals    |
| **Keep body under 102KB**      | Gmail clips larger messages             |

### Recommended

| Practice                               | Why                                                  |
| -------------------------------------- | ---------------------------------------------------- |
| **Use subdomains**                     | Protects reputation (e.g., `notifications.acme.com`) |
| **Disable tracking for transactional** | Open/click tracking can trigger spam filters         |

## Webhooks

Track email delivery status in real-time:

| Event                            | When to use                          |
| -------------------------------- | ------------------------------------ |
| `email.delivered`                | Confirm successful delivery          |
| `email.bounced`                  | Remove from mailing list, alert user |
| `email.complained`               | Unsubscribe user (spam complaint)    |
| `email.opened` / `email.clicked` | Track engagement (marketing only)    |

**Always verify webhook signatures:**

```typescript
const event = resend.webhooks.verify({
  payload,
  headers: {
    "svix-id": req.headers.get("svix-id"),
    "svix-timestamp": req.headers.get("svix-timestamp"),
    "svix-signature": req.headers.get("svix-signature"),
  },
  secret: process.env.RESEND_WEBHOOK_SECRET,
});
```

## Tags

Key/value pairs for tracking and filtering:

```typescript
tags: [
  { name: "user_id", value: "usr_123" },
  { name: "email_type", value: "welcome" },
  { name: "plan", value: "enterprise" },
];
```

**Constraints:** ASCII letters, numbers, underscores, dashes only. Max 256 chars each.

## Templates

Use pre-built templates instead of sending HTML:

```typescript
const { data, error } = await resend.emails.send({
  from: "Acme <hello@acme.com>",
  to: ["delivered@resend.dev"],
  subject: "Welcome!",
  template: {
    id: "tmpl_abc123",
    variables: {
      USER_NAME: "John", // Case-sensitive!
      ORDER_TOTAL: "$99.00",
    },
  },
});
```

**Important:** Variable names are **case-sensitive**. Templates must be **published** before use.

## Testing

**Never test with fake addresses at real providers (`test@gmail.com`)** - destroys reputation.

### Safe Testing

| Method         | Address                 | Result                        |
| -------------- | ----------------------- | ----------------------------- |
| **Delivered**  | `delivered@resend.dev`  | Simulates successful delivery |
| **Bounced**    | `bounced@resend.dev`    | Simulates hard bounce         |
| **Complained** | `complained@resend.dev` | Simulates spam complaint      |

## Domain Warm-up

New domains must gradually increase volume:

**New domain schedule:**
| Day | Max emails/day |
|-----|---------------|
| 1 | 150 |
| 2 | 250 |
| 3 | 400 |
| 4 | 700 |
| 5 | 1,000 |
| 6 | 1,500 |
| 7 | 2,000 |

**Monitor:** Bounce rate < 4%, Spam complaint rate < 0.08%

## Common Mistakes

| Mistake                          | Fix                                   |
| -------------------------------- | ------------------------------------- |
| Retrying without idempotency key | Always include - prevents duplicates  |
| Batch for attachments            | Use single sends instead              |
| Retrying 400/422 errors          | Fix request, don't retry              |
| Tracking on transactional        | Disable for receipts, password resets |
| Testing with fake emails         | Use `delivered@resend.dev`            |
| High volume on new domain        | Warm up gradually                     |
