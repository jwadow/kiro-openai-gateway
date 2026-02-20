# shadcn/ui Form Components

Form, Field, Input Group, and new 2026 components.

## Form (React Hook Form + Zod)

```tsx
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form"

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
})

function LoginForm() {
  const form = useForm({ resolver: zodResolver(schema), defaultValues: { email: "", password: "" } })

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(console.log)} className="space-y-6">
        <FormField control={form.control} name="email" render={({ field }) => (
          <FormItem>
            <FormLabel>Email</FormLabel>
            <FormControl><Input type="email" {...field} /></FormControl>
            <FormMessage />
          </FormItem>
        )} />
        <Button type="submit">Sign In</Button>
      </form>
    </Form>
  )
}
```

## Field (2026)

Simpler form abstraction:

```tsx
import { Field, FieldLabel, FieldDescription, FieldGroup, FieldSet } from "@/components/ui/field"

<FieldSet>
  <FieldGroup>
    <Field>
      <FieldLabel htmlFor="email">Email</FieldLabel>
      <Input id="email" type="email" />
      <FieldDescription>Never shared.</FieldDescription>
    </Field>
    <Field orientation="horizontal">
      <Checkbox id="terms" />
      <FieldLabel htmlFor="terms">Accept terms</FieldLabel>
    </Field>
  </FieldGroup>
</FieldSet>

<!-- Responsive layout -->
<Field orientation="responsive">
  <FieldContent>
    <FieldLabel>Name</FieldLabel>
    <FieldDescription>Display name</FieldDescription>
  </FieldContent>
  <Input placeholder="Evil Rabbit" />
</Field>
```

## Input Group (2026)

```tsx
import { InputGroup, InputGroupAddon, InputGroupInput, InputGroupButton } from "@/components/ui/input-group"

<InputGroup>
  <InputGroupAddon><SearchIcon /></InputGroupAddon>
  <InputGroupInput placeholder="Search..." />
</InputGroup>

<InputGroup>
  <InputGroupAddon>https://</InputGroupAddon>
  <InputGroupInput placeholder="example.com" />
  <InputGroupAddon align="inline-end">
    <InputGroupButton>Go</InputGroupButton>
  </InputGroupAddon>
</InputGroup>
```

## Spinner (2026)

```tsx
import { Spinner } from "@/components/ui/spinner"

<Spinner />

<Button disabled>
  <Spinner />Loading...
</Button>
```

## Kbd (2026)

```tsx
import { Kbd, KbdGroup } from "@/components/ui/kbd"

<KbdGroup>
  <Kbd>Cmd</Kbd>
  <Kbd>K</Kbd>
</KbdGroup>
```

## Button Group (2026)

```tsx
import { ButtonGroup } from "@/components/ui/button-group"

<ButtonGroup>
  <Button>Archive</Button>
  <Button>Report</Button>
  <DropdownMenu>
    <DropdownMenuTrigger asChild>
      <Button size="icon"><MoreIcon /></Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent>...</DropdownMenuContent>
  </DropdownMenu>
</ButtonGroup>
```

## Item (2026)

```tsx
import { Item, ItemContent, ItemMedia, ItemTitle, ItemDescription, ItemActions } from "@/components/ui/item"

<Item variant="outline">
  <ItemMedia variant="icon"><UserIcon /></ItemMedia>
  <ItemContent>
    <ItemTitle>Profile</ItemTitle>
    <ItemDescription>Manage account</ItemDescription>
  </ItemContent>
  <ItemActions><Button size="sm">Edit</Button></ItemActions>
</Item>

<Item asChild>
  <a href="/dashboard"><ItemContent><ItemTitle>Dashboard</ItemTitle></ItemContent></a>
</Item>
```

## Empty (2026)

```tsx
import { Empty, EmptyIcon, EmptyTitle, EmptyDescription, EmptyActions } from "@/components/ui/empty"

<Empty>
  <EmptyIcon><InboxIcon /></EmptyIcon>
  <EmptyTitle>No messages</EmptyTitle>
  <EmptyDescription>Send your first message.</EmptyDescription>
  <EmptyActions><Button>New Message</Button></EmptyActions>
</Empty>
```
