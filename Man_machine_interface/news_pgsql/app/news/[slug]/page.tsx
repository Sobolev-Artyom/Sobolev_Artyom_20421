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