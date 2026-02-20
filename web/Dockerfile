FROM node:20-alpine AS build
WORKDIR /web
COPY package*.json ./
RUN npm install
COPY . .
ARG VITE_API_BASE_URL=/api
ARG VITE_API_KEY=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_API_KEY=$VITE_API_KEY
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /web/dist /usr/share/nginx/html
COPY nginx/frontend.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
