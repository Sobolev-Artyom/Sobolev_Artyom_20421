use std::io::Read;
use std::net::{TcpListener, TcpStream};
use prost::Message; // Для работы с Protocol Buffers

mod device {
    include!(concat!(env!("OUT_DIR"), "/device.rs"));
}

fn handle_client(mut stream: TcpStream) {
    let mut buffer = Vec::new();
    stream.read_to_end(&mut buffer).expect("Failed to read from stream");

    let data = DeviceData::decode(&*buffer).expect("Failed to decode data");
    println!("Received data: {:?}", data);
}

fn main() {
    let listener = TcpListener::bind("127.0.0.1:50051").expect("Could not bind");

    for stream in listener.incoming() {
        match stream {
            Ok(stream) => handle_client(stream),
            Err(e) => eprintln!("Connection failed: {:?}", e),
        }
    }
}