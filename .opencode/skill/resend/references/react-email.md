# React Email

Build and send HTML emails using React components. A modern, component-based approach to email development that works across all major email clients by compiling to compatible HTML.

## When to Use

- Creating transactional emails (welcome, password reset, order confirmation)
- Building notification or marketing email templates
- Need consistent rendering across Gmail, Outlook, Apple Mail, Yahoo
- Want component reusability and TypeScript support in emails
- Integrating with email providers like Resend, SendGrid, Postmark

**When NOT to use:**

- Simple plain-text emails
- Emails that don't need cross-client compatibility
- Projects without React/Node.js

## Installation

### New Project

```bash
npx create-email@latest
cd react-email-starter
npm install
npm run dev
```

The server runs at localhost:3000 with a preview interface for templates in the `emails` folder.

### Existing Project

```bash
npm install react-email @react-email/preview-server -D -E
npm install @react-email/components react react-dom -E
```

Add script to package.json:

```json
{
  "scripts": {
    "email:dev": "email dev --dir src/emails"
  }
}
```

## Basic Email Template

```tsx
import {
  Html,
  Head,
  Preview,
  Body,
  Container,
  Heading,
  Text,
  Button,
  Tailwind,
  pixelBasedPreset,
} from "@react-email/components";

interface WelcomeEmailProps {
  name: string;
  verificationUrl: string;
}

export default function WelcomeEmail({ name, verificationUrl }: WelcomeEmailProps) {
  return (
    <Html lang="en">
      <Tailwind
        config={{
          presets: [pixelBasedPreset],
          theme: {
            extend: {
              colors: {
                brand: "#007bff",
              },
            },
          },
        }}
      >
        <Head />
        <Body className="bg-gray-100 font-sans">
          <Preview>Welcome - Verify your email</Preview>
          <Container className="max-w-xl mx-auto p-5">
            <Heading className="text-2xl text-gray-800">Welcome!</Heading>
            <Text className="text-base text-gray-800">Hi {name}, thanks for signing up!</Text>
            <Button
              href={verificationUrl}
              className="bg-brand text-white px-5 py-3 rounded block text-center no-underline box-border"
            >
              Verify Email
            </Button>
          </Container>
        </Body>
      </Tailwind>
    </Html>
  );
}

WelcomeEmail.PreviewProps = {
  name: "John Doe",
  verificationUrl: "https://example.com/verify/abc123",
} satisfies WelcomeEmailProps;

export { WelcomeEmail };
```

## Essential Components

**Core Structure:**

- `Html` - Root wrapper with `lang` attribute
- `Head` - Meta elements, styles, fonts
- `Body` - Main content wrapper
- `Container` - Centers content (max-width layout)
- `Section` - Layout sections
- `Row` & `Column` - Multi-column layouts (table-based)
- `Tailwind` - Enables Tailwind CSS utility classes

**Content:**

- `Preview` - Inbox preview text (place after `Body` opening tag)
- `Heading` - h1-h6 headings
- `Text` - Paragraphs
- `Button` - Styled link buttons
- `Link` - Hyperlinks
- `Img` - Images (use absolute URLs)
- `Hr` - Horizontal dividers

**Specialized:**

- `CodeBlock` - Syntax-highlighted code
- `CodeInline` - Inline code
- `Markdown` - Render markdown
- `Font` - Custom web fonts

## Styling Rules

### Always Do

| Rule                           | Why                                           |
| ------------------------------ | --------------------------------------------- |
| Use `pixelBasedPreset`         | Email clients don't support `rem` units       |
| Use `Row`/`Column` for layouts | Table-based layouts work everywhere           |
| Specify border type            | Always: `border-solid`, `border-dashed`, etc. |
| Use `box-border` on buttons    | Consistent sizing                             |
| Use PNG/JPEG images            | SVG/WEBP not supported                        |
| Use absolute image URLs        | Relative paths won't work                     |

### Never Do

| Rule                             | Why                                      |
| -------------------------------- | ---------------------------------------- |
| Use flexbox/grid                 | Not supported in email clients           |
| Use media queries (`sm:`, `md:`) | Most email clients ignore them           |
| Use theme selectors (`dark:`)    | Inconsistent support                     |
| Use SVG/WEBP images              | Not supported                            |
| Write template vars in JSX       | Use props: `{props.name}` not `{{name}}` |

## Rendering

### Convert to HTML

```tsx
import { render } from "@react-email/components";
import { WelcomeEmail } from "./emails/welcome";

const html = await render(
  <WelcomeEmail name="John" verificationUrl="https://example.com/verify" />,
);
```

### Convert to Plain Text

```tsx
const text = await render(
  <WelcomeEmail name="John" verificationUrl="https://example.com/verify" />,
  { plainText: true },
);
```

## Sending with Resend

```tsx
import { Resend } from "resend";
import { WelcomeEmail } from "./emails/welcome";

const resend = new Resend(process.env.RESEND_API_KEY);

const { data, error } = await resend.emails.send({
  from: "Acme <onboarding@resend.dev>",
  to: ["user@example.com"],
  subject: "Welcome to Acme",
  react: <WelcomeEmail name="John" verificationUrl="https://example.com/verify" />,
});

if (error) {
  console.error("Failed to send:", error);
}
```

Resend accepts React components directly. It automatically generates a plain-text version if not provided.

## Common Patterns

### Responsive Container

```tsx
<Container className="max-w-xl mx-auto p-5">
  {/* Content stays centered and readable on all devices */}
</Container>
```

### Two-Column Layout

```tsx
<Row>
  <Column className="w-1/2">
    <Text>Left content</Text>
  </Column>
  <Column className="w-1/2">
    <Text>Right content</Text>
  </Column>
</Row>
```

**Note:** Columns won't stack on mobile. Design with this in mind.

### CTA Button

```tsx
<Button
  href="https://example.com"
  className="bg-blue-600 text-white px-6 py-3 rounded block text-center no-underline box-border"
>
  Click Here
</Button>
```

### Footer with Links

```tsx
<Section className="text-center text-gray-500 text-sm">
  <Text>
    <Link href="https://example.com/unsubscribe" className="text-gray-500 underline">
      Unsubscribe
    </Link>
    {" | "}
    <Link href="https://example.com/preferences" className="text-gray-500 underline">
      Preferences
    </Link>
  </Text>
  <Text>123 Main St, City, State 12345</Text>
</Section>
```

## Best Practices

1. **Test across clients** - Gmail, Outlook, Apple Mail, Yahoo
2. **Keep responsive** - Max-width ~600px
3. **Use absolute image URLs** - Host on reliable CDN
4. **Provide plain text version** - Required for accessibility
5. **Add TypeScript types** - Define interfaces for all props
6. **Include PreviewProps** - For development testing
7. **Keep under 102KB** - Gmail clips larger emails

## Common Mistakes

| Mistake                           | Fix                                      |
| --------------------------------- | ---------------------------------------- |
| Using flexbox/grid                | Use `Row` and `Column` components        |
| Using `rem` units                 | Use `pixelBasedPreset` with Tailwind     |
| Using SVG images                  | Use PNG or JPG instead                   |
| Using media queries               | Design mobile-first with stacked layouts |
| Template vars in JSX (`{{name}}`) | Use props: `{props.name}`                |
| Missing border type               | Always specify: `border-solid`, etc.     |
| Emails over 102KB                 | Gmail clips - reduce size                |

## Resources

- [React Email Documentation](https://react.email/docs)
- [React Email GitHub](https://github.com/resend/react-email)
- [Email Client CSS Support](https://www.caniemail.com)
