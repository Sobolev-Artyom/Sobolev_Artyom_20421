# Новостной сайт с использованием PostgreSQL

### В результате выполнения задания, я написал сайт, используя платформу Node.js и ЯП JavaScript. Также я использовал PostgreSQL для управления своей базой данных(БД), Prisma и Prisma Seeding для заполнения БД, Tailwindcss для верстки сайта, а также Nginx для создания прокси сервера и Docker для контейнеризации всего приложения. Сейчас разберемся, как это все работает.
_________
## Создание БД
### Для создания базы данных и как результат новостного сайта, нам нужно определить модель наших новостей, которая будет потом использоваться для формирования структуры в таблице БД и на новостной странице сайта. Для этого нам нужно инициализировать prisma в нашем проекте и создать в соответствующей папке следующую структуру:
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
### После создания модели, нам нужно ее сгенерировать в @prisma-client. Для этого нужно выполнить миграцию и генерацию:
 npx prisma generate; npx prisma migrate dev --name init.

### Затем необходимо провести заполнение БД. Сделать это можно с помощью Prisma Seeding. Необходимо также создать единственный экземпляр PrismaClient через Singleton. Для этого мы создаем следующие файлы с кодом: 
db.ts
```rust
import { PrismaClient } from "@prisma/client";
const prismaClientSingleton = () => {
    return new PrismaClient
}

declare const globalThis: {
    prismaGlobal: ReturnType<typeof prismaClientSingleton>;
} & typeof global;

const prisma = globalThis.prismaGlobal ?? prismaClientSingleton()

export default prisma

if (process.env.NODE_ENV !== 'production') globalThis.prismaGlobal = prisma
```
seed.ts
```rust
import prisma from '../app/lib/db'

async function main() {
    const newsarray = [
        {
         title: 'PostgreSQL 17.2, 16.6, 15.10, 14.15, 13.18, and 12.22 Released!',
         date: new Date('2024-11-21'),
         text: 'The PostgreSQL Global Development Group has released an update to all supported versions of PostgreSQL, including 17.2, 16.6, 15.10, 14.15, and 13.18. Additionally, due to the nature of one of the issues in the previous update release, the PostgreSQL Global Development Group is also releasing a 12.22 release for PostgreSQL 12. PostgreSQL 12 is now EOL and will not receive more fixes.',
         image: 'image'   
        },
        {
         title: 'PGConf.dev 2025 - Call for Speakers and Sponsors',
         date: new Date('2024-11-20'),
         text: 'PGConf.dev 2025 (May 13-16, 2025, Montreal, CA), aka PostgreSQL Development Conference 2025, is an event where users, developers, and community organizers come together to focus on PostgreSQL development and community growth. Meet PostgreSQL contributors, learn about upcoming features, and discuss development problems with PostgreSQL enthusiasts!',
         image: 'image'    
        },
        {
         title: 'Call for Proposals is open for POSETTE: An Event for Postgres 2025!',
         date: new Date('2024-11-20'),
         text: 'The 4th annual event called POSETTE: An Event for Postgres will happen Jun 10-12, 2025 and the Call for Speakers is now open—until Feb 9, 2025! POSETTE is a free & virtual developer event organized by the Postgres team at Microsoft. The name POSETTE stands for Postgres Open Source Ecosystem Talks Training & Education. First time & experienced speakers both welcome! Whether you’re a first-time speaker or a regular speaker at conferences, we’d love to consider your talk proposal(s) about Postgres and the rich tooling and extensions (like PostGIS, Citus, & Patroni) in the Postgres ecosystem—both open source and for Postgres in the cloud on Azure.',
         image: 'image' 
        },
        {
         title: 'pgSCV 0.9.4 released.',
         date: new Date('2024-11-20'),
         text: 'pgSCV is a Prometheus-compatible monitoring agent and metrics exporter for PostgreSQL environment. The goal of the project is to provide a single tool (exporter) for collecting metrics from PostgreSQL and related services.',
         image: 'image' 
        }
    ];

    for (const newsdata of newsarray) {
        await prisma.news.upsert({
            where: { title: newsdata.title },
            update: {
                date: newsdata.date,
                text: newsdata.text,
                image: newsdata.image,
            },
            create: {
                title: newsdata.title,
                date: newsdata.date,
                text: newsdata.text,
                image: newsdata.image,
            },
        });
        console.log('Upserted news: ${newsdata.title}');
    }
}

main()
    .then(async ()=> {
        await prisma.$disconnect();
    })
    .catch(async (e) =>{
        console.error(e);
        await prisma.$disconnect();
        process.exit(1);
    });
```
### Используем команду для засеивания БД:
npx prisma db seed 
### Засеянную базу данных можно увидеть, прописав в терминале следующую команду и перейдя по ссылке:
npx prisma studio;  http://localhost:5555
### На рисунке видим, как должна выглядеть наша база данных:
![image](https://github.com/user-attachments/assets/35a5c879-5236-4633-b344-6dd3afddb628)
## Теперь мы имеем заполненную базу данных, с которой мы можем работать. Далее мы поговорим о создании страниц сайта.
________





