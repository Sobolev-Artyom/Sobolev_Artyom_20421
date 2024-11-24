import prisma from "@/app/lib/db";
import { Prisma } from '@prisma/client';
import { unstable_noStore as nostore } from "next/cache";

export async function addnews(newsdata: Prisma.newsCreateInput){}


export async function getavaliablenews() {
    nostore();
    try {
        console.log('getavaliablenews');
        const data = await prisma.news.findMany();
        return data;

    } catch (error) {
        console.error("Database Error:", error);
        throw new Error("Failed to fetch employee data.");
    }

}
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