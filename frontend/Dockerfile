FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* /app/
RUN if [ -f pnpm-lock.yaml ]; then npm i -g pnpm && pnpm i; \
    elif [ -f yarn.lock ]; then yarn; \
    else npm i; fi

COPY . /app

EXPOSE 5173

CMD ["bash", "-lc", "if [ -f pnpm-lock.yaml ]; then pnpm dev --host 0.0.0.0 --port 5173; elif [ -f yarn.lock ]; then yarn dev --host 0.0.0.0 --port 5173; else npm run dev -- --host 0.0.0.0 --port 5173; fi"]

