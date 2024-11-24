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