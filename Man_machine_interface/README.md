# Новостной сайт с использованием PostgreSQL

## В результате выполнения задания, я написал сайт, используя платформу Node.js и ЯП JavaScript. Также я использовал PostgreSQL для управления своей базой данных(БД), Prisma и Prisma Seeding для заполнения БД, Tailwindcss для верстки сайта, а также Nginx для создания прокси сервера и Docker для контейнеризации всего приложения. Сейчас разберемся, как это все работает.

### Для создания базы данных и как результат новостного сайта, нам нужно определить модель наших новостей, которая будет потом использоваться для формирования структуры в таблице БД и на новостной странице сайта:
shema.prisma
```rust
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model news {
  id          Int      @id @default(autoincrement())
  title       String   @unique
  date        DateTime @db.Date
  text        String
  image       String? 
}
```
