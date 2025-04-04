use prost_types::Timestamp;
use prost::Message;
mod randf;

use std::{io::Write, net::TcpStream, time, time::Duration, thread};


mod proto {
    include!(concat!(env!("OUT_DIR"), "/_.rs"));
}


pub struct Config {
    device_id: u32,
    timer_sec: u64,
    address: String,
    port: String
}

impl Config {
    pub fn build(device_id: u32, timer_sec: u64, address: String, port: String) -> Self {
        Config { device_id: device_id, timer_sec: timer_sec, address: address, port: port }
    }
    pub fn device_id(&self) -> u32 {
        self.device_id
    }
    pub fn timer_sec(&self) -> u64 {
        self.timer_sec
    }
    pub fn address(&self) -> &String {
        &self.address
    }
    pub fn port(&self) -> &String {
        &self.port
    }
}

pub struct ESP {
    config: Config,
    event_id: u64,
    randf: randf::RANDF,
}

impl ESP {
    pub fn build(config: Config) -> Self {
        ESP { config: config, event_id: 0, randf: randf::RANDF::build()}
    }

    pub fn start(&mut self) {
        loop {
            thread::sleep(Duration::from_secs(self.config.timer_sec));
            let mut proto = proto::Proto::default();

            proto.device_id = self.config.device_id();
            proto.event_id = self.event_id;
            self.event_id += 1;

            proto.humidity = self.randf.read_humidity();
            proto.temperature = self.randf.read_temperature();
        
            let mut read_ts = Timestamp::default();
            let duration = time::SystemTime::now().duration_since(time::UNIX_EPOCH).unwrap();
            read_ts.seconds = duration.as_secs() as i64;
            read_ts.nanos = duration.subsec_nanos() as i32;

            proto.read_time = Some(read_ts);

            let mut stream = match TcpStream::connect(self.config.address().to_owned() + ":" + self.config.port()) {
                Ok(stream) => {println!("Success"); stream},
                Err(_) => {println!("Error"); continue;},
            };

            let mut vec_proto_proto = proto.encode_to_vec();
            let mut vec_data: Vec<u8>= Vec::new(); 
            let mut vec_len = vec_proto_proto.len() as u32;
            for _ in 0..4 {
                vec_data.push(vec_len as u8);
                vec_len = vec_len >> 8;
            }
            vec_data.append(&mut vec_proto_proto);
            stream.write_all(&vec_data).unwrap();
            stream.flush().unwrap();

        }
    }
}

fn main() {
    let config = Config::build(u32::MAX, 1, "127.0.0.1".to_string(), "7878".to_string());

    let mut esp = ESP::build(config);
    esp.start();
}
