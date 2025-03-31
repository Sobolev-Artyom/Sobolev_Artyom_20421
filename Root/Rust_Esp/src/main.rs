use rand::Rng;
use std::io::Write;
use std::net::{TcpStream};
use std::thread;
use std::time::{Duration, SystemTime};
use prost::Message;
use tokio_postgres::types::Timestamp;
use dotenv::dotenv;
use std::env;
mod device;

fn main() {
    dotenv().ok();
    let db_url = env::var("DATABASE_URL").expect("DATABASE_URL not set");
    let device_id = "ESP123".to_string();
    let mut event_id = 0;

    loop {
        let humidity = rand::thread_rng().gen_range(30.0..50.0);
        let temperature = rand::thread_rng().gen_range(18.0..28.0);
        let read_time = SystemTime::now();

        let mut timestamp = google_dates::Timestamp::default();
        timestamp.seconds = read_time.duration_since(SystemTime::UNIX_EPOCH).unwrap().as_secs() as i64;
        timestamp.nanos = (read_time.duration_since(SystemTime::UNIX_EPOCH).unwrap().subsec_nanos()) as i32;

        let data = device::DeviceData {
            device_id: device_id.clone(),
            event_id,
            humidity,
            temperature,
            read_time: Some(timestamp),
        };

        let encoded_data = data.encode_to_vec();

        match TcpStream::connect("127.0.0.1:50051") {
            Ok(mut stream) => {
                stream.write_all(&encoded_data).expect("Failed to send data");
            }
            Err(e) => {
                eprintln!("Connection error: {:?}", e);
            }
        }

        event_id += 1;
        thread::sleep(Duration::from_secs(1));
    }
}