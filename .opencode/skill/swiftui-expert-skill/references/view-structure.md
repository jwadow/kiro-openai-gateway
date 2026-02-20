# SwiftUI View Structure Reference

## View Structure Principles

SwiftUI's diffing algorithm compares view hierarchies to determine what needs updating. Proper view composition directly impacts performance.

## Prefer Modifiers Over Conditional Views

**Prefer "no-effect" modifiers over conditionally including views.** When you introduce a branch, consider whether you're representing multiple views or two states of the same view.

### Use Opacity Instead of Conditional Inclusion

```swift
// Good - same view, different states
SomeView()
    .opacity(isVisible ? 1 : 0)

// Avoid - creates/destroys view identity
if isVisible {
    SomeView()
}
```

**Why**: Conditional view inclusion can cause loss of state, poor animation performance, and breaks view identity. Using modifiers maintains view identity across state changes.

### When Conditionals Are Appropriate

Use conditionals when you truly have **different views**, not different states:

```swift
// Correct - fundamentally different views
if isLoggedIn {
    DashboardView()
} else {
    LoginView()
}

// Correct - optional content
if let user {
    UserProfileView(user: user)
}
```

## Extract Subviews, Not Computed Properties

### The Problem with @ViewBuilder Functions

When you use `@ViewBuilder` functions or computed properties for complex views, the entire function re-executes on every parent state change:

```swift
// BAD - re-executes complexSection() on every tap
struct ParentView: View {
    @State private var count = 0

    var body: some View {
        VStack {
            Button("Tap: \(count)") { count += 1 }
            complexSection()  // Re-executes every tap!
        }
    }

    @ViewBuilder
    func complexSection() -> some View {
        // Complex views that re-execute unnecessarily
        ForEach(0..<100) { i in
            HStack {
                Image(systemName: "star")
                Text("Item \(i)")
                Spacer()
                Text("Detail")
            }
        }
    }
}
```

### The Solution: Separate Structs

Extract to separate `struct` views. SwiftUI can skip their `body` when inputs don't change:

```swift
// GOOD - ComplexSection body SKIPPED when its inputs don't change
struct ParentView: View {
    @State private var count = 0

    var body: some View {
        VStack {
            Button("Tap: \(count)") { count += 1 }
            ComplexSection()  // Body skipped during re-evaluation
        }
    }
}

struct ComplexSection: View {
    var body: some View {
        ForEach(0..<100) { i in
            HStack {
                Image(systemName: "star")
                Text("Item \(i)")
                Spacer()
                Text("Detail")
            }
        }
    }
}
```

### Why This Works

1. SwiftUI compares the `ComplexSection` struct (which has no properties)
2. Since nothing changed, SwiftUI skips calling `ComplexSection.body`
3. The complex view code never executes unnecessarily

## When @ViewBuilder Functions Are Acceptable

Use for small, simple sections that don't affect performance:

```swift
struct SimpleView: View {
    @State private var showDetails = false

    var body: some View {
        VStack {
            headerSection()  // OK - simple, few views
            if showDetails {
                detailsSection()
            }
        }
    }

    @ViewBuilder
    private func headerSection() -> some View {
        HStack {
            Text("Title")
            Spacer()
            Button("Toggle") { showDetails.toggle() }
        }
    }

    @ViewBuilder
    private func detailsSection() -> some View {
        Text("Some details here")
            .font(.caption)
    }
}
```

## When to Extract Subviews

Extract complex views into separate subviews when:
- The view has multiple logical sections or responsibilities
- The view contains reusable components
- The view body becomes difficult to read or understand
- You need to isolate state changes for performance
- The view is becoming large (keep views small for better performance)

## Container View Pattern

### Avoid Closure-Based Content

Closures can't be compared, causing unnecessary re-renders:

```swift
// BAD - closure prevents SwiftUI from skipping updates
struct MyContainer<Content: View>: View {
    let content: () -> Content

    var body: some View {
        VStack {
            Text("Header")
            content()  // Always called, can't compare closures
        }
    }
}

// Usage forces re-render on every parent update
MyContainer {
    ExpensiveView()
}
```

### Use @ViewBuilder Property Instead

```swift
// GOOD - view can be compared
struct MyContainer<Content: View>: View {
    @ViewBuilder let content: Content

    var body: some View {
        VStack {
            Text("Header")
            content  // SwiftUI can compare and skip if unchanged
        }
    }
}

// Usage - SwiftUI can diff ExpensiveView
MyContainer {
    ExpensiveView()
}
```

## ZStack vs overlay/background

Use `ZStack` to **compose multiple peer views** that should be layered together and jointly define layout.

Prefer `overlay` / `background` when you’re **decorating a primary view**.  
Not primarily because they don’t affect layout size, but because they **express intent and improve readability**: the view being modified remains the clear layout anchor.

A key difference is **size proposal behavior**:
- In `overlay` / `background`, the child view implicitly adopts the size proposed to the parent when it doesn’t define its own size, making decorative attachments feel natural and predictable.
- In `ZStack`, each child participates independently in layout, and no implicit size inheritance exists. This makes it better suited for peer composition, but less intuitive for simple decoration.

Use `ZStack` (or another container) when the “decoration” **must explicitly participate in layout sizing**—for example, when reserving space, extending tappable/visible bounds, or preventing overlap with neighboring views.

### Examples: Choosing Between overlay/background and ZStack

```swift
// GOOD - correct usage
// Decoration that should not change layout sizing belongs in overlay/background
Button("Continue") {
    // action
}
.overlay(alignment: .trailing) {
    Image(systemName: "lock.fill")
        .padding(.trailing, 8)
}

// BAD - incorrect usage
// Using ZStack when overlay/background is enough and layout sizing should remain anchored to the button
ZStack(alignment: .trailing) {
    Button("Continue") {
        // action
    }
    Image(systemName: "lock.fill")
        .padding(.trailing, 8)
}

// GOOD - correct usage
// Capsule is taking a parent size for rendering
HStack(spacing: 12) {
    HStack {
        Image(systemName: "tray")
        Text("Inbox")
    }
    Text("Next")
}
.background {
    Capsule()
        .strokeBorder(.blue, lineWidth: 2)
}

// BAD - incorrect usage
// overlay does not contribute to measured size, so the Capsule is taking all available space if no explicit size is set
ZStack(alignment: .topTrailing) {
    HStack(spacing: 12) {
        HStack {
            Image(systemName: "tray")
            Text("Inbox")
        }
        Text("Next")
    }

    Capsule()
        .strokeBorder(.blue, lineWidth: 2)
}
```

## Summary Checklist

- [ ] Prefer modifiers over conditional views for state changes
- [ ] Complex views extracted to separate subviews
- [ ] Views kept small for better performance
- [ ] `@ViewBuilder` functions only for simple sections
- [ ] Container views use `@ViewBuilder let content: Content`
- [ ] Extract views when they have multiple responsibilities or become hard to read
