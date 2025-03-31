use std::io::Read;
use std::net::{TcpListener, TcpStream};
use prost::Message; // Для работы с Protocol Buffers
use tokio_postgres::{NoTls, Client};

async fn save_to_db(client: &Client, data: &DeviceData) -> Result<(), Box<dyn std::error::Error>> {
    let query = "INSERT INTO device_data (device_id, event_id, humidity, temperature, read_time) VALUES ($1, $2, $3, $4, $5)";
    client.execute(query, &[
        &data.device_id,
        &data.event_id,
        &data.humidity,
        &data.temperature,
        &data.read_time.as_ref().unwrap().seconds
    ]).await?;
    Ok(())
}

// Добавьте обработку подключения к базе данных в main
async fn connect_db() -> Result<Client, tokio_postgres::Error> {
    let (client, connection) = tokio_postgres::connect("host=localhost user=postgres dbname=mydb", NoTls).await?;
    tokio::spawn(async move {
        if let Err(e) = connection.await {
Rust


            eprintln!("Connection error: {}", e);
        }
    });
    Ok(client)
}
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