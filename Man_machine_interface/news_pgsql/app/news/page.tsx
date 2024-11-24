import Image from "next/image";
import ComponentNews from "@/app/ui/componentnews";
import  {getavaliablenews} from "@/app/lib/data"

export default async function Home() {
  const newsdata = await getavaliablenews();

  
  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-8 row-start-2 items-center sm:items-start">
        <p className = {"font-bold"}> You are on news page!</p>

        <ComponentNews newsdata = {newsdata} />
      </main>
      <footer className="row-start-3 flex gap-6 flex-wrap items-center justify-center">
      </footer>
    </div>
  );
}
