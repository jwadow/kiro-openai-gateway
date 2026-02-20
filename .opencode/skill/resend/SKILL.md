---
name: resend
description: Use when working with Resend email platform - sending transactional emails, receiving inbound emails, creating email templates with React Email, handling webhooks, or integrating email into applications.
references:
  - send-email
  - receive-email
  - react-email
---

# Resend Email Platform

Consolidated skill for building email systems with Resend. Use decision trees below to find the right approach, then load detailed references.

## How to Use This Skill

### Reference File Structure

Each feature in `./references/` contains documentation for specific use cases:

| File               | Purpose                      | When to Read                                   |
| ------------------ | ---------------------------- | ---------------------------------------------- |
| `send-email.md`    | Sending transactional emails | Single/batch sends, attachments, scheduling    |
| `receive-email.md` | Receiving inbound emails     | Webhooks, processing received mail, forwarding |
| `react-email.md`   | Building email templates     | React components, styling, rendering           |

### Reading Order

1. Start with this file for quick routing
2. Then read the relevant reference file for your task

## Quick Decision Tree

### "I need to send emails"

```
Need to send emails?
├─ Single email (transactional) → send-email.md
├─ Batch emails (max 100) → send-email.md
├─ Email with attachments → send-email.md (single only)
├─ Scheduled emails → send-email.md (single only)
├─ Marketing/bulk campaigns → Use Resend Broadcasts (dashboard)
└─ AI agent sending emails → send-email.md + moltbot patterns
```

### "I need to receive emails"

```
Need to receive emails?
├─ Set up inbound domain → receive-email.md
├─ Process webhook events → receive-email.md
├─ Get email body/content → receive-email.md (Receiving API)
├─ Download attachments → receive-email.md
├─ Forward received emails → receive-email.md
└─ AI agent receiving emails → receive-email.md + moltbot patterns
```

### "I need to build email templates"

```
Need email templates?
├─ React-based templates → react-email.md
├─ Cross-client compatibility → react-email.md
├─ Reusable components → react-email.md
├─ Tailwind styling → react-email.md
└─ Plain HTML templates → Use Resend dashboard templates
```

## Common Setup

### API Key

Store in environment variable (never commit to code):

```bash
export RESEND_API_KEY=re_xxxxxxxxx
```

### SDK Installation

**Node.js:**

```bash
npm install resend
```

**Python:**

```bash
pip install resend
```

**Go:**

```bash
go get github.com/resend/resend-go/v2
```

### Basic Usage (Node.js)

```typescript
import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

// Send email
const { data, error } = await resend.emails.send({
  from: "Acme <hello@acme.com>",
  to: ["user@example.com"],
  subject: "Hello World",
  html: "<p>Email body here</p>",
});

if (error) {
  console.error("Failed:", error.message);
}
```

## Critical Best Practices

### Always Do

| Practice                      | Why                                |
| ----------------------------- | ---------------------------------- |
| **Idempotency keys**          | Prevent duplicate emails on retry  |
| **Verify webhook signatures** | Prevent spoofed events             |
| **Use test addresses**        | `delivered@resend.dev` for testing |
| **Warm up new domains**       | Gradual volume increase            |
| **Include plain text**        | Accessibility and deliverability   |

### Never Do

| Anti-Pattern                             | Why                        |
| ---------------------------------------- | -------------------------- |
| Test with fake emails (`test@gmail.com`) | Destroys sender reputation |
| Skip webhook verification                | Security vulnerability     |
| Retry 400/422 errors                     | Fix the request instead    |
| Use "no-reply" addresses                 | Hurts deliverability       |
| Send high volume from new domain         | Triggers spam filters      |

## Webhook Events

| Event              | Use Case                      |
| ------------------ | ----------------------------- |
| `email.sent`       | Confirm email accepted        |
| `email.delivered`  | Confirm delivery to inbox     |
| `email.bounced`    | Remove from list, alert user  |
| `email.complained` | Unsubscribe (spam complaint)  |
| `email.opened`     | Track engagement (marketing)  |
| `email.clicked`    | Track link clicks (marketing) |
| `email.received`   | Process inbound emails        |

## Error Handling

| Code     | Action                              |
| -------- | ----------------------------------- |
| 400, 422 | Fix request parameters, don't retry |
| 401, 403 | Check API key / verify domain       |
| 409      | Idempotency conflict - use new key  |
| 429      | Rate limited - exponential backoff  |
| 500      | Server error - retry with backoff   |

## Resources

- [Resend Documentation](https://resend.com/docs)
- [API Reference](https://resend.com/docs/api-reference)
- [React Email](https://react.email)
- [Dashboard](https://resend.com/emails)
