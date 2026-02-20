# Build stage
FROM node:20-alpine AS builder

# Prefer IPv4 DNS (fixes IPv6 connection issues)
RUN echo "precedence ::ffff:0:0/96 100" >> /etc/gai.conf

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build args for Next.js (needed at build time)
ARG NEXT_PUBLIC_API_URL=https://api.trollllm.xyz
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1

# Build Next.js
RUN npm run build

# Runtime stage
FROM node:20-alpine AS runner

# Prefer IPv4 DNS (fixes IPv6 connection issues)
RUN echo "precedence ::ffff:0:0/96 100" >> /etc/gai.conf

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built files
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
