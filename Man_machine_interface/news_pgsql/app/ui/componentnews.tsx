import Link from "next/link";
import {news} from '@prisma/client';

export default async function ComponentNews({newsdata} : { newsdata: news[],}) {
    return (
        <div className='grid grid-cols-1 gap-3 bg-blue-200'>
            {newsdata.map((elem) => (
                <Link href={'/news/${elem.id}'} key = {elem.id} className={'group'}>
                    <div key = {elem.id} className="bg-blue-200 rounded-lg">
                        <div className="font-bold">
                            Congratulations, {elem.title}
                        </div>
                    </div>
                </Link>
            ))}
        </div>
    );
}