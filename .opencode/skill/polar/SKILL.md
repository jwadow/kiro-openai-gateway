---
name: polar
description: Polar payment platform integration for monetization, subscriptions, and license keys. Use when implementing checkout, managing products, or building customer portals.
---

# Polar Integration

Polar is a merchant-of-record platform for digital products, subscriptions, and license keys.

## What I Do

- Guide implementation of Polar checkout and payments
- Help with subscription management and billing
- Assist with license key validation
- Set up webhook handlers for payment events

## When to Use Me

- Implementing checkout flow for a product
- Adding subscription billing to an app
- Setting up license key validation
- Building a customer portal
- Handling payment webhooks

## Quick Start

```bash
npm install @polar-sh/sdk
```

```typescript
import { Polar } from "@polar-sh/sdk";

const polar = new Polar({
  accessToken: process.env.POLAR_ACCESS_TOKEN!,
  server: "production", // or "sandbox"
});
```

## Key APIs

| API                     | Purpose                           |
| ----------------------- | --------------------------------- |
| `polar.products.*`      | Create/manage products and prices |
| `polar.checkouts.*`     | Create checkout sessions          |
| `polar.subscriptions.*` | Manage subscriptions              |
| `polar.orders.*`        | View order history                |
| `polar.customers.*`     | Customer management               |
| `polar.licenseKeys.*`   | Issue and validate licenses       |

## Environment Variables

| Variable               | Description                     |
| ---------------------- | ------------------------------- |
| `POLAR_ACCESS_TOKEN`   | Organization Access Token (OAT) |
| `POLAR_WEBHOOK_SECRET` | Webhook signing secret          |

## Common Patterns

### Create Checkout

```typescript
const checkout = await polar.checkouts.create({
  productId: "prod_xxx",
  successUrl: "https://myapp.com/success",
});
// Redirect to checkout.url
```

### Validate License Key

```typescript
const result = await polar.licenseKeys.validate({
  key: "XXXX-XXXX-XXXX-XXXX",
  organizationId: "org_xxx",
});
```

### Handle Webhook

```typescript
import { validateEvent } from "@polar-sh/sdk/webhooks";

const event = validateEvent(body, signature, process.env.POLAR_WEBHOOK_SECRET!);
// event.type: "subscription.created", "order.created", etc.
```

## Links

- [Dashboard](https://polar.sh)
- [API Docs](https://docs.polar.sh/api-reference)
- [SDK](https://www.npmjs.com/package/@polar-sh/sdk)
