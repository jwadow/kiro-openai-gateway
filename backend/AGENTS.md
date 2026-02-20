# backend/AGENTS.md - Backend Component Guidelines

**Parent:** See root [AGENTS.md](../AGENTS.md) for project overview, TypeScript conventions, and build commands.

## Overview

Node.js/Express RESTful API serving port 3005. JWT authentication, MongoDB (Mongoose ODM), Zod validation, role-based access control. Handles user management, API keys, payments (SePay), usage tracking, and admin operations.

## File Structure

```
src/
├── routes/          # Express route definitions (admin.routes.ts, auth.routes.ts, etc.)
├── controllers/     # Request validation, response formatting (user-key.controller.ts)
├── services/        # Business logic (auth.service.ts, payment.service.ts)
├── repositories/    # Data access, MongoDB queries (user.repository.ts, user-key.repository.ts)
├── models/          # Mongoose schemas with IModel interfaces (user-key.model.ts)
├── dtos/            # Zod validation schemas for API input/output (user-key.dto.ts)
├── middleware/      # Auth, role checks, error logging (auth.middleware.ts, role.middleware.ts)
├── db/              # MongoDB connection (mongodb.ts)
├── scripts/         # One-off utilities (tsx src/scripts/*.ts)
├── index.ts         # Express app entry point
└── seed.ts          # Database seeding (npm run seed)
```

## Where to Look

| Task | Start Here |
|------|-----------|
| Add REST endpoint | `dtos/` → `services/` → `controllers/` → `routes/` |
| Modify auth logic | `services/auth.service.ts`, `middleware/auth.middleware.ts` |
| Add model field | `models/*.model.ts` → update interface + schema |
| Change payment flow | `services/payment.service.ts`, `models/payment.model.ts` |
| Query optimization | `repositories/*.repository.ts` (use `.lean()` for read-only) |
| Add admin endpoint | `routes/admin.routes.ts` (use `requireAdmin` middleware) |
| Error handling | Check `middleware/error-logger.middleware.ts` |

## Layered Architecture (STRICT)

**Flow:** `routes → controllers → services → repositories → models`

1. **Routes** (`routes/*.routes.ts`)
   - Register Express routes
   - Apply middleware (auth, role checks)
   - Delegate to controllers
   - Example: `router.post('/keys', requireAdmin, (req, res) => userKeyController.create(req, res))`

2. **Controllers** (`controllers/*.controller.ts`)
   - Parse/validate request (Zod DTOs)
   - Call service layer
   - Format response JSON
   - Handle HTTP-specific errors (400, 401, 404, 500)

3. **Services** (`services/*.service.ts`)
   - Business logic ONLY
   - No req/res objects
   - Return typed data or throw errors
   - Orchestrate multiple repositories

4. **Repositories** (`repositories/*.repository.ts`)
   - MongoDB queries (Mongoose API)
   - Use `.lean()` for read-only queries (performance)
   - Return model interfaces (IUserKey, IUser)
   - NO business logic

5. **Models** (`models/*.model.ts`)
   - Mongoose schemas + TypeScript interfaces
   - Interface: `export interface IUserKey { _id: string; ... }`
   - Schema: `const userKeySchema = new mongoose.Schema({ ... })`
   - Export: `export const UserKey = mongoose.model<IUserKey>('UserKey', userKeySchema, 'collection_name')`

## Backend-Specific Conventions

### DTOs with Zod (Required)
```typescript
// dtos/user-key.dto.ts
export const CreateUserKeyDTO = z.object({
  name: z.string().min(1).max(100),
  notes: z.string().max(500).optional(),
});
export type CreateUserKeyInput = z.infer<typeof CreateUserKeyDTO>;

// Controller usage
const input = CreateUserKeyDTO.parse(req.body); // Throws ZodError if invalid
```

### Error Handling Pattern
```typescript
try {
  const input = CreateUserKeyDTO.parse(req.body);
  const result = await service.createKey(input);
  res.status(201).json(result);
} catch (error: any) {
  if (error instanceof z.ZodError) {
    res.status(400).json({ error: 'Validation failed', details: error.errors });
    return;
  }
  console.error('Create key error:', error);
  res.status(500).json({ error: 'Failed to create key' });
}
```

### Import Extensions (.js)
Always use `.js` extension in relative imports (TypeScript quirk for ES modules):
```typescript
import { userKeyService } from '../services/userkey.service.js'; // ✅ Correct
import { userKeyService } from '../services/userkey.service';    // ❌ Wrong
```

### MongoDB Query Optimization
Use `.lean()` for read-only queries (returns plain objects, faster):
```typescript
async findAll(): Promise<IUserKey[]> {
  return UserKey.find().sort({ createdAt: -1 }).lean(); // ✅ Faster
}
```

### Authentication
- JWT tokens: `Authorization: Bearer <token>` (preferred)
- Basic auth: Deprecated but supported for backward compatibility
- Middleware: `authMiddleware` (any auth), `jwtAuth` (JWT only), `requireAdmin` (admin role)

## Anti-Patterns (DO NOT)

1. **Bypassing service layer** - Controllers calling repositories directly (breaks business logic isolation)
2. **Skipping DTO validation** - Accepting `req.body` without Zod parse (security risk)
3. **Hardcoding secrets** - Use `process.env.*` from `.env` file
4. **Ignoring .lean()** - Returning full Mongoose documents for read-only queries (performance penalty)
5. **Business logic in controllers** - Controllers are HTTP adapters only
6. **Forgetting .js extensions** - Relative imports will fail at runtime

## Key Scripts

```bash
npm run dev      # tsx watch mode (hot reload)
npm run build    # Compile TypeScript to dist/
npm run seed     # Database seeding (initial data)
npm run lint     # ESLint check

# Run one-off scripts
tsx src/scripts/generate-referral-codes.ts
tsx src/scripts/migrate-users-to-usernew.ts
```

## Testing Database Changes

No test framework yet. Manual verification:
1. Call API endpoint via curl/Postman
2. Check MongoDB collection directly
3. Monitor backend logs (`npm run dev` output)

---

**Remember:** This guide covers BACKEND-ONLY patterns. See root AGENTS.md for general TypeScript conventions, project structure, and GoProxy/Frontend specifics.
