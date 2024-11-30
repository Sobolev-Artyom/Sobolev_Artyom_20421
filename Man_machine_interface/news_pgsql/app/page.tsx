import Image from "next/image";
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
