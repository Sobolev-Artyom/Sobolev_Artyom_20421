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
# Создание страниц сайта
## Первая(Главная) страница сайта:
![image](https://github.com/user-attachments/assets/52d177f3-5ff8-4779-89f4-062d38dce9fe)
### Код для ее создания.
```rust
import Link from "next/link";

export default function Home() {
  return (
    <div className="grid grid-rows-[20px_1fr_20px]  items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-8 row-start-2  items-center sm:items-start">
      <p className = {"items-center font-bold text-3xl italic text-white"}> PostgreSQL.News</p>
        <Link href="/news" className = {"ml-8 font-bold italic text-white"}>Click to go on news page.</Link>

        <div className="flex gap-4 items-center flex-col sm:flex-row">
        </div>
      </main>
      <footer className="row-start-3 flex gap-6 flex-wrap items-center justify-center">
        <a
            className="flex border-1 rounded-lg bg-blue-400 items-center text-white gap-2 hover:underline hover:underline-offset-4"
            href="https://nextjs.org/docs?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
            target="_blank"
            rel="noopener noreferrer"
          >
            Click to "Read our docs"
          </a>
        <a
          className="flex border-1 rounded-lg bg-blue-400 items-center gap-2 text-white hover:underline hover:underline-offset-4"
          href="https://nextjs.org/learn?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          Click to "Learn more"
        </a>
        <a
          className="flex border-1 rounded-lg bg-blue-400 items-center gap-2 text-white hover:underline hover:underline-offset-4"
          href="https://vercel.com/templates?framework=next.js&utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          Click to "See examples"
        </a>
        <a
          className="flex border-1 rounded-lg bg-blue-400 items-center gap-2 text-white hover:underline hover:underline-offset-4"
          href="https://nextjs.org?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          Click to "Go to nextjs.org"
        </a>
      </footer>
    </div>
  );
}
```

## Cтраница с новостями:
![image](https://github.com/user-attachments/assets/b4ace90d-ccaf-4cd6-8a2c-ff30571935a0)
### Код для ее создания.
```rust
import ComponentNews from "@/app/ui/componentnews";
import  {getavaliablenews} from "@/app/lib/data"

export default async function Home() {
  const newsdata = await getavaliablenews();

  
  return (
    <div className="grid grid-rows-[20px_1fr_20px] min-h-screen p-8 pb-20 gap-1 sm:p-20 ">
      <main className="flex flex-col gap-8 row-start-2 items-center sm:items-start text-base/6" >
        <p className = {"object-left-top font-bold text-2xl italic border-1 rounded-lg bg-blue-50"}> You are on news page!</p>

        <ComponentNews newsdata = {newsdata} isnew = {false}/>
      </main>
      <footer className="row-start-3 flex gap-6 flex-wrap items-center justify-center">
        <a
            className="flex border-1 rounded-lg bg-blue-50 items-center gap-2 hover:underline hover:underline-offset-4"
            href="https://nextjs.org/docs?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
            target="_blank"
            rel="noopener noreferrer"
          >
            Click to "Read our docs"
          </a>
        <a
          className="flex items-center gap-2 border-1 rounded-lg bg-blue-50 hover:underline hover:underline-offset-4"
          href="https://nextjs.org/learn?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          Click to "Learn more"
        </a>
        <a
          className="flex items-center gap-2 hover:underline border-1 rounded-lg bg-blue-50 hover:underline-offset-4"
          href="https://vercel.com/templates?framework=next.js&utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          Click to "See examples"
        </a>
        <a
          className="flex items-center gap-2 hover:underline border-1 rounded-lg bg-blue-50 hover:underline-offset-4"
          href="https://nextjs.org?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          Click to "Go to nextjs.org"
        </a>
      </footer>
    </div>
  );
}

```
## Страница с новостью :
![image](https://github.com/user-attachments/assets/728f9f79-7916-4422-962e-68e6e45698e7)
### Код для ее создания.
```rust
import Link from "next/link";
import {news} from '@prisma/client';

export default async function ComponentNews({newsdata, isnew} : { newsdata: news[], isnew: boolean}) {
    return (
        <div className='grid grid-cols-1 gap-3 p-8 bg-blue-50 rounded-lg '>
            {newsdata.map((elem) => (
                <Link href={`/news/${elem.id}`} key = {elem.id} className={'group '}>
                    <div key = {elem.id} className={"bg-blue  rounded-lg"}>
                        <div className="flex-col font-bold ml-10 w-80 italic underline rounded-lg">
                            Now, {elem.title}
                        </div>
                        {isnew  && (
                            <div className="ml-4 italic leading-loose" >
                                <div className="my-4">
                                    Date:{elem.date.toDateString()}
                                </div>
                                <div className="w-80" >    
                                    Read it:{elem.text}
                                </div>
                                <div className="my-4">
                                    See it: {elem.image}
                                </div>
                            </div>
                        )}  
                    </div>
                </Link>
            ))}
        </div>
    );
}
```
## И также: 
```rust
import ComponentNews from "@/app/ui/componentnews";
import prisma from "@/app/lib/db";
import { unstable_noStore as nostore } from "next/cache";

export async function getNewsByid(id:number) {
    nostore();
    try {
        console.log('getNewsByid');
        const data = await prisma.news.findUnique({where:{id}});
        return data; 

        

    } catch (error){
        console.error('Database error', error);
        throw new Error("Failed to fetch news data");
    }
    
 }

export default async function Page({params}: { params: {slug: string} }) {
    console.log(params);
    const { slug } = await params
    const newsdata = await getNewsByid(Number(slug));

    const newsarray = newsdata ? [newsdata] : [];

    return (
        <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
            <main className="flex flex-col gap-8 row-start-2 items-center sm:items-start">
                <ComponentNews newsdata = {newsarray} isnew = {true}/>
            </main>
        </div>
    )
}
```
________
## Dockerfile:
```rust
# Первая стадия: сборка приложения
FROM node:20-alpine

# Рабочая директория
WORKDIR /app

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
```
## docker-compose.yml:
```rust
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgres://postgres:1234@db:5432/mydb
    depends_on:
      - db
    command: >
      sh -c "
             npx prisma migrate dev --name init &&
             npx prisma generate &&
             npm install -D typescript ts-node @types/node &&
             npx prisma db seed &&
             npm run dev"
    volumes:
      - .:/app
      - /app/node_modules
    networks:
      - my_network
  db:
    image: postgres:14
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: 1234
      POSTGRES_DB: mydb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - my_network
networks:
  my_network:
    external: false
volumes:
  postgres_data:
```
## nginx.conf:
```rust
events {}

http {
    server {
        listen 80;

        location / {
            proxy_pass http://app:3000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```






