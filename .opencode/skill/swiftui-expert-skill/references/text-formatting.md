# SwiftUI Text Formatting Reference

## Modern Text Formatting

**Never use C-style `String(format:)` with Text. Always use format parameters.**

## Number Formatting

### Basic Number Formatting

```swift
let value = 42.12345

// Modern (Correct)
Text(value, format: .number.precision(.fractionLength(2)))
// Output: "42.12"

Text(abs(value), format: .number.precision(.fractionLength(2)))
// Output: "42.12" (absolute value)

// Legacy (Avoid)
Text(String(format: "%.2f", abs(value)))
```

### Integer Formatting

```swift
let count = 1234567

// With grouping separator
Text(count, format: .number)
// Output: "1,234,567" (locale-dependent)

// Without grouping
Text(count, format: .number.grouping(.never))
// Output: "1234567"
```

### Decimal Precision

```swift
let price = 19.99

// Fixed decimal places
Text(price, format: .number.precision(.fractionLength(2)))
// Output: "19.99"

// Significant digits
Text(price, format: .number.precision(.significantDigits(3)))
// Output: "20.0"

// Integer-only
Text(price, format: .number.precision(.integerLength(1...)))
// Output: "19"
```

## Currency Formatting

```swift
let price = 19.99

// Correct - with currency code
Text(price, format: .currency(code: "USD"))
// Output: "$19.99"

// With locale
Text(price, format: .currency(code: "EUR").locale(Locale(identifier: "de_DE")))
// Output: "19,99 €"

// Avoid - manual formatting
Text(String(format: "$%.2f", price))
```

## Percentage Formatting

```swift
let percentage = 0.856

// Correct - with precision
Text(percentage, format: .percent.precision(.fractionLength(1)))
// Output: "85.6%"

// Without decimal places
Text(percentage, format: .percent.precision(.fractionLength(0)))
// Output: "86%"

// Avoid - manual calculation
Text(String(format: "%.1f%%", percentage * 100))
```

## Date and Time Formatting

### Date Formatting

```swift
let date = Date()

// Date only
Text(date, format: .dateTime.day().month().year())
// Output: "Jan 23, 2026"

// Full date
Text(date, format: .dateTime.day().month(.wide).year())
// Output: "January 23, 2026"

// Short date
Text(date, style: .date)
// Output: "1/23/26"
```

### Time Formatting

```swift
let date = Date()

// Time only
Text(date, format: .dateTime.hour().minute())
// Output: "2:30 PM"

// With seconds
Text(date, format: .dateTime.hour().minute().second())
// Output: "2:30:45 PM"

// 24-hour format
Text(date, format: .dateTime.hour(.defaultDigits(amPM: .omitted)).minute())
// Output: "14:30"
```

### Relative Date Formatting

```swift
let futureDate = Date().addingTimeInterval(3600)

// Relative formatting
Text(futureDate, style: .relative)
// Output: "in 1 hour"

Text(futureDate, style: .timer)
// Output: "59:59" (counts down)
```

## String Searching and Comparison

### Localized String Comparison

**Use `localizedStandardContains()` for user-input filtering, not `contains()`.**

```swift
let searchText = "café"
let items = ["Café Latte", "Coffee", "Tea"]

// Correct - handles diacritics and case
let filtered = items.filter { $0.localizedStandardContains(searchText) }
// Matches "Café Latte"

// Wrong - exact match only
let filtered = items.filter { $0.contains(searchText) }
// Might not match "Café Latte" depending on normalization
```

**Why**: `localizedStandardContains()` handles case-insensitive, diacritic-insensitive matching appropriate for user-facing search.

### Case-Insensitive Comparison

```swift
let text = "Hello World"
let search = "hello"

// Correct - case-insensitive
if text.localizedCaseInsensitiveContains(search) {
    // Match found
}

// Also correct - for exact comparison
if text.lowercased() == search.lowercased() {
    // Equal
}
```

### Localized Sorting

```swift
let names = ["Zoë", "Zara", "Åsa"]

// Correct - locale-aware sorting
let sorted = names.sorted { $0.localizedStandardCompare($1) == .orderedAscending }
// Output: ["Åsa", "Zara", "Zoë"]

// Wrong - byte-wise sorting
let sorted = names.sorted()
// Output may not be correct for all locales
```

## Attributed Strings

### Basic Attributed Text

```swift
// Using Text concatenation
Text("Hello ")
    .foregroundStyle(.primary)
+ Text("World")
    .foregroundStyle(.blue)
    .bold()

// Using AttributedString
var attributedString = AttributedString("Hello World")
attributedString.foregroundColor = .primary
if let range = attributedString.range(of: "World") {
    attributedString[range].foregroundColor = .blue
    attributedString[range].font = .body.bold()
}
Text(attributedString)
```

### Markdown in Text

```swift
// Simple markdown
Text("This is **bold** and this is *italic*")

// With links
Text("Visit [Apple](https://apple.com) for more info")

// Multiline markdown
Text("""
# Title
This is a paragraph with **bold** text.
- Item 1
- Item 2
""")
```

## Text Measurement

### Measuring Text Height

```swift
// Wrong (Legacy) - GeometryReader trick
struct MeasuredText: View {
    let text: String
    @State private var textHeight: CGFloat = 0
    
    var body: some View {
        Text(text)
            .background(
                GeometryReader { geometry in
                    Color.clear
                        .onAppear {
                            textWidth = geometry.size.height
                        }
                }
            )
    }
}

// Modern (correct)
struct MeasuredText: View {
    let text: String
    @State private var textHeight: CGFloat = 0
    
    var body: some View {
        Text(text)
            .onGeometryChange(for: CGFloat.self) { geometry in
                geometry.size.height
            } action: { newValue in
                textHeight = newValue
            }
    }
}
```

## Summary Checklist

- [ ] Use `.format` parameters with Text instead of `String(format:)`
- [ ] Use `.currency(code:)` for currency formatting
- [ ] Use `.percent` for percentage formatting
- [ ] Use `.dateTime` for date/time formatting
- [ ] Use `localizedStandardContains()` for user-input search
- [ ] Use `localizedStandardCompare()` for locale-aware sorting
- [ ] Use Text concatenation or AttributedString for styled text
- [ ] Use markdown syntax for simple text formatting
- [ ] All formatting respects user's locale and preferences

**Why**: Modern format parameters are type-safe, localization-aware, and integrate better with SwiftUI's text rendering.
