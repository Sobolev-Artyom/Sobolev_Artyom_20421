import Image from "next/image";
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
