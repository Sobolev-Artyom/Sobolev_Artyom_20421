# Первая стадия: сборка приложения
FROM node:20 AS builder

# Рабочая директория
WORKDIR /news_pgsql

# Копируем файлы в рабочую директорию
COPY package.json package-lock.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем все остальные файлы
COPY . .

# Строим проект
RUN npm run dev

# Вторая стадия: запуск приложения через Nginx
FROM nginx:alpine

# Копируем конфигурацию Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Рабочая директория
WORKDIR /usr/share/nginx/html

# Копируем собранные файлы из первой стадии
COPY --from=builder /news_pgsql/build ./build

# Открываем порт 80
EXPOSE 80

# Запускаем Nginx
CMD ["npm","run","dev","nginx", "-g", "daemon off;"]
