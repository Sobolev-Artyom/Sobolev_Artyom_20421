# Первая стадия: сборка приложения
FROM node:20-alpine

# Рабочая директория
WORKDIR /news_pgsql

# Копируем файлы в рабочую директорию
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем все остальные файлы
COPY . .

# Открываем порт 3000
EXPOSE 3000

# Запускаем Nginx
CMD ["npm","run","dev"]
