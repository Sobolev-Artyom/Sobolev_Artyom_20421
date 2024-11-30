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