# Receive Emails with Resend

## Overview

Resend processes incoming emails for your domain and sends webhook events to your endpoint. **Webhooks contain metadata only** - you must call separate APIs to retrieve email body and attachments.

## Quick Start

1. **Configure receiving domain** - Use Resend's `.resend.app` domain or add MX record for custom domain
2. **Set up webhook** - Subscribe to `email.received` event
3. **Retrieve content** - Call Receiving API for body, Attachments API for files

## Domain Setup

### Option 1: Resend-Managed Domain (Fastest)

Use your auto-generated address: `<anything>@<your-id>.resend.app`

No DNS configuration needed. Find your address in Dashboard -> Emails -> Receiving -> "Receiving address".

### Option 2: Custom Domain

Add MX record to receive at `<anything>@yourdomain.com`.

| Setting      | Value                        |
| ------------ | ---------------------------- |
| **Type**     | MX                           |
| **Host**     | Your domain or subdomain     |
| **Value**    | Provided in Resend dashboard |
| **Priority** | 10 (lowest number wins)      |

**Critical:** Your MX record must have the lowest priority value, or emails won't route to Resend.

### Subdomain Recommendation

If you already have MX records (e.g., Google Workspace, Microsoft 365):

| Approach                        | Result                                                        |
| ------------------------------- | ------------------------------------------------------------- |
| **Use subdomain** (recommended) | `support.acme.com` -> Resend, `acme.com` -> existing provider |
| **Use root domain**             | All email routes to Resend (breaks existing email)            |

```dns
# Receive at support.acme.com without affecting acme.com
support.acme.com.  MX  10  <resend-mx-value>
```

## Webhook Setup

### Subscribe to `email.received`

Dashboard -> Webhooks -> Add Webhook -> Select `email.received`

For local development, use tunneling:

```bash
ngrok http 3000
# Use https://abc123.ngrok.io/api/webhook as endpoint
```

### Webhook Payload Structure

**Important:** Payload contains metadata only, not email body or attachments.

```json
{
  "type": "email.received",
  "created_at": "2024-02-22T23:41:12.126Z",
  "data": {
    "email_id": "a1b2c3d4-...",
    "from": "sender@example.com",
    "to": ["support@acme.com"],
    "cc": [],
    "bcc": [],
    "subject": "Question about my order",
    "attachments": [
      {
        "id": "att_abc123",
        "filename": "receipt.pdf",
        "content_type": "application/pdf"
      }
    ]
  }
}
```

### Verify Webhook Signatures

Always verify signatures to prevent spoofed events:

```typescript
import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(req: Request) {
  const payload = await req.text();

  const event = resend.webhooks.verify({
    payload,
    headers: {
      "svix-id": req.headers.get("svix-id"),
      "svix-timestamp": req.headers.get("svix-timestamp"),
      "svix-signature": req.headers.get("svix-signature"),
    },
    secret: process.env.RESEND_WEBHOOK_SECRET,
  });

  if (event.type === "email.received") {
    // Process the email
  }

  return new Response("OK", { status: 200 });
}
```

## Retrieving Email Content

Webhooks exclude email body. Call the Receiving API:

```typescript
if (event.type === "email.received") {
  const { data: email } = await resend.emails.receiving.get(event.data.email_id);

  console.log(email.html); // HTML body
  console.log(email.text); // Plain text body
  console.log(email.headers); // Email headers
}
```

**Why this design?** Serverless environments have request body size limits. Separating content retrieval supports large emails and attachments.

## Handling Attachments

### Get Attachment Metadata and Download URLs

```typescript
const { data: attachments } = await resend.emails.receiving.attachments.list({
  emailId: event.data.email_id,
});

for (const attachment of attachments) {
  console.log(attachment.filename);
  console.log(attachment.download_url); // Valid for 1 hour
  console.log(attachment.expires_at);
}
```

### Download Attachment Content

```typescript
const response = await fetch(attachment.download_url);
const buffer = await response.arrayBuffer();

// Save to storage, process, etc.
await saveToStorage(attachment.filename, buffer);
```

**Important:** `download_url` expires after 1 hour. Call the API again for a fresh URL if needed.

## Forwarding Emails

Complete workflow to receive and forward an email with attachments:

```typescript
import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(req: Request) {
  const payload = await req.text();
  const event = resend.webhooks.verify({
    /* ... */
  });

  if (event.type === "email.received") {
    // 1. Get email content
    const { data: email } = await resend.emails.receiving.get(event.data.email_id);

    // 2. Get attachments (if any)
    const { data: attachmentList } = await resend.emails.receiving.attachments.list({
      emailId: event.data.email_id,
    });

    // 3. Download and encode attachments
    const attachments = await Promise.all(
      attachmentList.map(async (att) => {
        const res = await fetch(att.download_url);
        const buffer = Buffer.from(await res.arrayBuffer());
        return {
          filename: att.filename,
          content: buffer.toString("base64"),
        };
      }),
    );

    // 4. Forward the email
    await resend.emails.send({
      from: "Support System <system@acme.com>",
      to: ["team@acme.com"],
      subject: `Fwd: ${email.subject}`,
      html: email.html,
      text: email.text,
      attachments,
    });
  }

  return new Response("OK", { status: 200 });
}
```

## Routing by Recipient

All emails to your domain arrive at the same webhook. Route based on the `to` field:

```typescript
if (event.type === "email.received") {
  const recipient = event.data.to[0];

  if (recipient.includes("support@")) {
    await handleSupportEmail(event.data);
  } else if (recipient.includes("billing@")) {
    await handleBillingEmail(event.data);
  } else {
    await handleUnknownEmail(event.data);
  }
}
```

## Common Mistakes

| Mistake                                      | Fix                                                              |
| -------------------------------------------- | ---------------------------------------------------------------- |
| Expecting body in webhook payload            | Webhook has metadata only - call `resend.emails.receiving.get()` |
| MX record not lowest priority                | Ensure Resend's MX has lowest number (highest priority)          |
| Adding MX to root domain with existing email | Use subdomain to avoid breaking existing email service           |
| Using expired download_url                   | URLs expire after 1 hour - call attachments API again            |
| Not verifying webhook signatures             | Always verify - attackers can send fake events                   |
| Forgetting to return 200 OK                  | Resend retries on non-200 responses                              |

## Storage Note

Resend stores received emails even if:

- Webhook isn't configured yet
- Webhook endpoint is down

View all received emails in Dashboard -> Emails -> Receiving tab.
