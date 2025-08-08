ARG BUN_VERSION=1.2.19
FROM oven/bun:${BUN_VERSION}-alpine as base

ENV NODE_ENV=production
WORKDIR /app

FROM base as builder

RUN apk update && apk add --no-cache \
    build-base 

COPY ./printed_barcode_api/bun.lock ./printed_barcode_api/package.json ./

RUN bun install -ci --frozen-lockfile

COPY printed_barcode_api/ ./

FROM base as runner

COPY --from=builder /app /app

EXPOSE 3000
CMD ["bun", "run", "start"]
