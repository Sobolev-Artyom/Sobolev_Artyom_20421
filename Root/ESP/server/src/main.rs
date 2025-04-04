extern crate postgres;
extern crate chrono;
use std::env; 
use crate::listener::Listener;
use crate::db_client::Database;

mod proto {
    include!(concat!(env!("OUT_DIR"), "/_.rs"));
}

mod utils {
    use chrono::{DateTime, NaiveDateTime, Utc};
    use prost_types::Timestamp;
    use crate::proto::Proto;
    use prost::Message;

    pub fn protobuf_timestamp_to_naive_date_time(timestamp: Timestamp) -> NaiveDateTime {
        let datetime_utc: DateTime<Utc> = DateTime::from_timestamp(timestamp.seconds, timestamp.nanos as u32).unwrap();
        datetime_utc.naive_utc()
    }

    pub fn vec_to_data_proto(mut vec: Vec<u8>) -> Result<Proto, ()> {
        if vec.len() > 4 {
            let mut vec_len: usize = 0 ;
            for i in (0..4).rev() {
                vec_len = vec_len << 8;
                vec_len += vec[i] as usize;
            }
            vec = vec[4..].to_owned();  
            if vec_len <= vec.len() {
                return match Proto::decode(&vec[..vec_len]) {
                    Ok(r) => Ok(r),
                    Err(_) => Err(())
                }
            }
        }
        Err(())
    }
}

pub mod db_client {
    use postgres::{Client, NoTls};
    use crate::proto::Proto;
    use crate::utils::protobuf_timestamp_to_naive_date_time;

    pub struct Database {
        client: Client,
    }

    impl Database {
        pub fn build(postgres_url: String) -> Database {
            loop {
                match Client::connect(&postgres_url, NoTls) {
                    Ok(c) => {return Database {client: c}},
                    Err(_) => {println!("Error");continue;}
                }
            }
        }

        pub fn init_table(&mut self) {
            self.client.batch_execute("
            CREATE TABLE IF NOT EXISTS proto (
            id              SERIAL PRIMARY KEY,
            device_id       OID NOT NULL,
            event_id        OID NOT NULL,
            humidity        real NOT NULL,
            temperature     real NOT NULL,
            read_time       timestamp NOT NULL
            )").unwrap();
        }

        pub fn add_data(&mut self, proto: Proto) {
            let read_time = protobuf_timestamp_to_naive_date_time(proto.read_time.unwrap());
            self.client.execute(
                "INSERT INTO proto 
                (device_id, event_id, humidity, temperature, read_time) 
                VALUES 
                ($1, $2, $3, $4, $5)",
                &[&proto.device_id, &(proto.event_id as u32), &proto.humidity, &proto.temperature, &read_time]
                ).unwrap();

        }
    }
}

pub mod listener {
    use std::{io::{BufReader, Read}, net::TcpListener};

    use crate::{db_client::Database, utils::vec_to_data_proto};
    pub struct Listener {
        listener: TcpListener,
        db: Database
    }

    impl Listener {
        pub fn build(db: Database,ip: String, port: String) -> Listener {
            Listener {
                listener: TcpListener::bind(ip+":"+&port).unwrap(),
                db: db
            }
        }

        pub fn start(&mut self) {
            for stream in self.listener.incoming() {
                let stream = stream.unwrap();
                let mut buf_reader = BufReader::new(&stream);
                let mut vec_proto = Vec::new();
                buf_reader.read_to_end(&mut vec_proto).unwrap();
                let proto =  match vec_to_data_proto(vec_proto) {
                    Ok(d) => d,
                    Err(_) => continue
                };
                self.db.add_data(proto);
            }
        }
    }
}
fn main() {
    // let postgres_url="postgres://postgres:1234@localhost:5268/mydb".to_string();
    // let port="7878".to_string();
    // let ip="0.0.0.0".to_string();
    let postgres_url = env::var("DATABASE_URL").unwrap();
    
    let ip = env::var("IP").unwrap();
    let port = env::var("PORT").unwrap();

    let mut db = Database::build(postgres_url);
    db.init_table();
    let mut listener = Listener::build(db, ip, port);

    listener.start();
}
