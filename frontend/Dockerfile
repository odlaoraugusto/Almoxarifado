# Build multi-stage — só usado no deploy da VPS (docker-compose.vps.yml).
# O deploy na Vercel (se ainda usado) continua via `npm run build` direto,
# sem passar por aqui.
FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite só embute VITE_* no bundle em build time — precisa vir como
# build arg, não dá pra trocar depois num container já buildado.
ARG VITE_API_URL
ARG VITE_ORGANIZACAO
ARG VITE_HOSPITAL_NOME
ARG VITE_HOSPITAL_SIGLA
ENV VITE_API_URL=$VITE_API_URL \
    VITE_ORGANIZACAO=$VITE_ORGANIZACAO \
    VITE_HOSPITAL_NOME=$VITE_HOSPITAL_NOME \
    VITE_HOSPITAL_SIGLA=$VITE_HOSPITAL_SIGLA

RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
