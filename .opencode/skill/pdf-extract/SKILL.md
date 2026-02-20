---
name: pdf-extract
description: Extract text, images, tables, and metadata from PDF files. Choose the right library based on extraction needs - text only, structured data, or complex layouts.
---

# PDF Content Extraction

Extract content from PDF files using the best library for your specific use case.

## Quick Decision Guide

| Use Case                    | Recommended Library | Why                                |
| --------------------------- | ------------------- | ---------------------------------- |
| Simple text extraction      | `pdf-parse` (v2+)   | Fast, lightweight, pure TypeScript |
| Complex layouts/coordinates | `pdfjs-dist`        | Full control, precise positioning  |
| Tables/tabular data         | `pdf-data-parser`   | Built for grid-based content       |
| Forms (XFA)                 | `pdf-lib` + custom  | Form field extraction              |
| Browser + Node.js           | `pdf-parse` v2      | Cross-platform, works everywhere   |

---

## Library 1: pdf-parse (Recommended for Text)

**Best for:** Simple text extraction, metadata, fast processing

### Installation

```bash
npm install pdf-parse
```

### Basic Text Extraction

```typescript
import { PDFParse } from "pdf-parse";
import { readFile } from "fs/promises";

async function extractText(filePath: string): Promise<string> {
  const parser = new PDFParse();
  const buffer = await readFile(filePath);

  const result = await parser.parse(buffer);
  return result.text;
}

// Usage
const text = await extractText("./document.pdf");
console.log(text);
```

### Extract with Metadata

```typescript
import { PDFParse } from "pdf-parse";

async function extractWithMetadata(filePath: string) {
  const parser = new PDFParse();
  const buffer = await readFile(filePath);

  const result = await parser.parse(buffer);

  return {
    text: result.text,
    info: result.info, // Document metadata
    numpages: result.numpages,
    version: result.version,
  };
}
```

### Extract Specific Pages

```typescript
import { PDFParse } from "pdf-parse";

async function extractPage(filePath: string, pageNum: number) {
  const parser = new PDFParse();
  const buffer = await readFile(filePath);

  const result = await parser.parse(buffer, {
    max: pageNum,
    min: pageNum,
  });

  return result.text;
}
```

### URL-based Extraction (without downloading full file)

```typescript
import { getHeader } from "pdf-parse/node";

async function checkPDFHeaders(url: string) {
  // Check file size and headers before downloading
  const headers = await getHeader(url, true);
  console.log(`File size: ${headers.size} bytes`);

  if (headers.size > 10 * 1024 * 1024) {
    console.warn("Large PDF - consider streaming");
  }
}
```

---

## Library 2: pdfjs-dist (Mozilla PDF.js)

**Best for:** Complex layouts, coordinates, images, page-by-page control

### Installation

```bash
npm install pdfjs-dist
```

### Basic Text Extraction with Coordinates

```typescript
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf.mjs";
import { readFile } from "fs/promises";
import path from "path";

async function extractWithCoordinates(pdfPath: string) {
  const data = await readFile(pdfPath);
  const dataArray = new Uint8Array(data);

  const pdfDocument = await pdfjsLib.getDocument({
    data: dataArray,
    standardFontDataUrl: path.join(process.cwd(), "node_modules/pdfjs-dist/standard_fonts/"),
  }).promise;

  const numPages = pdfDocument.numPages;
  const results = [];

  for (let pageNum = 1; pageNum <= numPages; pageNum++) {
    const page = await pdfDocument.getPage(pageNum);
    const textContent = await page.getTextContent();

    const pageText = textContent.items.map((item: any) => ({
      text: item.str,
      x: item.transform[4],
      y: item.transform[5],
      font: item.fontName,
      width: item.width,
      height: item.height,
    }));

    results.push({
      page: pageNum,
      items: pageText,
    });
  }

  return results;
}
```

### Extract Images from PDF

```typescript
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf.mjs";

async function extractImages(pdfPath: string) {
  const data = await readFile(pdfPath);
  const pdfDocument = await pdfjsLib.getDocument({ data: new Uint8Array(data) }).promise;

  const images = [];

  for (let pageNum = 1; pageNum <= pdfDocument.numPages; pageNum++) {
    const page = await pdfDocument.getPage(pageNum);
    const ops = await page.getOperatorList();

    for (let i = 0; i < ops.fnArray.length; i++) {
      if (ops.fnArray[i] === pdfjsLib.OPS.paintImageXObject) {
        const imageName = ops.argsArray[i][0];
        const image = await page.objs.get(imageName);

        images.push({
          page: pageNum,
          name: imageName,
          width: image.width,
          height: image.height,
          data: image.data, // Raw image data
        });
      }
    }
  }

  return images;
}
```

### Render Page to Image

```typescript
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf.mjs";
import { createCanvas } from "canvas";
import { writeFile } from "fs/promises";

async function renderPageToImage(pdfPath: string, pageNum: number, outputPath: string) {
  const data = await readFile(pdfPath);
  const pdfDocument = await pdfjsLib.getDocument({ data: new Uint8Array(data) }).promise;

  const page = await pdfDocument.getPage(pageNum);
  const viewport = page.getViewport({ scale: 2.0 }); // Higher scale = better quality

  const canvas = createCanvas(viewport.width, viewport.height);
  const context = canvas.getContext("2d");

  await page.render({
    canvasContext: context,
    viewport: viewport,
  }).promise;

  const buffer = canvas.toBuffer("image/png");
  await writeFile(outputPath, buffer);

  console.log(`Page ${pageNum} saved to ${outputPath}`);
}
```

---

## Library 3: pdf-data-parser (Tables)

**Best for:** Tabular data, structured grid content

### Installation

```bash
npm install pdf-data-parser
```

### Extract Tables

```typescript
import { PdfDataParser } from "pdf-data-parser";

async function extractTables(pdfPath: string) {
  const parser = new PdfDataParser({
    url: pdfPath,
    // Options
    heading: "Table Title", // Filter to specific table
    cells: 3, // Minimum cells per row
    headers: ["Name", "Amount"], // Expected headers
    repeating: false, // Handle repeating headers
  });

  const rows = await parser.parse();
  return rows; // Array of arrays
}
```

### Stream Large PDFs

```typescript
import { PdfDataReader } from "pdf-data-parser";
import { createWriteStream } from "fs";

async function streamToCSV(pdfPath: string, outputPath: string) {
  const reader = new PdfDataReader({
    url: pdfPath,
    cells: 2,
  });

  const output = createWriteStream(outputPath);

  reader.on("data", (row: string[]) => {
    output.write(row.join(",") + "\n");
  });

  reader.on("end", () => {
    output.end();
    console.log("CSV created");
  });
}
```

---

## Best Practices

### 1. Error Handling

```typescript
async function safeExtract(filePath: string) {
  try {
    const buffer = await readFile(filePath);

    // Validate PDF header
    const header = buffer.slice(0, 5).toString();
    if (header !== "%PDF-") {
      throw new Error("Invalid PDF file");
    }

    const result = await parser.parse(buffer);
    return result;
  } catch (error) {
    if (error.message.includes("password")) {
      throw new Error("PDF is password protected");
    }
    if (error.message.includes("damaged")) {
      throw new Error("PDF is corrupted");
    }
    throw error;
  }
}
```

### 2. Memory Management (Large Files)

```typescript
// For large PDFs, process page by page
async function extractLargePDF(pdfPath: string) {
  const data = await readFile(pdfPath);
  const pdfDocument = await pdfjsLib.getDocument({ data: new Uint8Array(data) }).promise;

  // Don't load all pages at once
  for (let i = 1; i <= pdfDocument.numPages; i++) {
    const page = await pdfDocument.getPage(i);
    const text = await page.getTextContent();

    // Process immediately, don't accumulate
    await processPageText(text);

    // Clean up
    page.cleanup();
  }
}
```

### 3. Text Cleaning

```typescript
function cleanExtractedText(text: string): string {
  return text
    .replace(/\s+/g, " ") // Normalize whitespace
    .replace(/[^\x20-\x7E\n]/g, "") // Remove non-printable chars
    .trim();
}
```

### 4. Performance Tips

```typescript
// Parallel extraction for multiple files
async function extractMultiple(files: string[]) {
  const results = await Promise.all(
    files.map((file) => extractText(file).catch((err) => ({ file, error: err }))),
  );
  return results;
}

// Use streams for very large files
import { createReadStream } from "fs";
import { PdfDataReader } from "pdf-data-parser";
```

---

## Common Issues & Solutions

| Issue                | Cause                 | Solution                              |
| -------------------- | --------------------- | ------------------------------------- |
| Text appears garbled | Encoding issue        | Use pdfjs-dist with explicit encoding |
| Missing text         | Scanned image PDF     | Use OCR (Tesseract) before extraction |
| Out of memory        | Large PDF             | Stream processing, page-by-page       |
| Password error       | Encrypted PDF         | Use `pdf-lib` to decrypt first        |
| Missing coordinates  | Wrong library         | Use pdfjs-dist for positioning        |
| Table structure lost | Plain text extraction | Use pdf-data-parser                   |
| Font warnings        | Missing fonts         | Set `standardFontDataUrl` option      |

---

## Complete Example: Document Processor

```typescript
import { PDFParse } from "pdf-parse";
import { readFile } from "fs/promises";

interface DocumentResult {
  text: string;
  metadata: {
    title?: string;
    author?: string;
    pages: number;
    creationDate?: Date;
  };
  summary: string;
}

async function processDocument(filePath: string): Promise<DocumentResult> {
  const parser = new PDFParse();
  const buffer = await readFile(filePath);

  const result = await parser.parse(buffer);

  // Generate summary (first 500 chars)
  const summary = result.text.replace(/\s+/g, " ").slice(0, 500).trim() + "...";

  return {
    text: result.text,
    metadata: {
      title: result.info?.Title,
      author: result.info?.Author,
      pages: result.numpages,
      creationDate: result.info?.CreationDate ? new Date(result.info.CreationDate) : undefined,
    },
    summary,
  };
}

// Usage
const doc = await processDocument("./report.pdf");
console.log(`Document: ${doc.metadata.title}`);
console.log(`Pages: ${doc.metadata.pages}`);
console.log(`Summary: ${doc.summary}`);
```

---

## References

- [pdf-parse npm](https://www.npmjs.com/package/pdf-parse)
- [pdfjs-dist docs](https://mozilla.github.io/pdf.js/)
- [pdf-data-parser GitHub](https://github.com/drewletcher/pdf-data-parser)
- [pdf-lib GitHub](https://github.com/Hopding/pdf-lib)
