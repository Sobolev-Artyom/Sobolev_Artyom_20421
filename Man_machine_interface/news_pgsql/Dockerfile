FROM node:18-alpine

WORKDIR /app
RUN apk update && apk add openssl
COPY package.json package-lock.json ./
COPY app ./app
COPY public ./public
COPY next.config.ts .
COPY tsconfig.json .
COPY tailwind.config.ts .
COPY postcss.config.mjs .
COPY prisma ./prisma

ENV NEXT_TELEMENTRY_DIASABLED 1

CMD \
    npx prisma generate;\
    npx prisma migrate dev --name; \
    npx prisma db seed; \
    npm run dev;
