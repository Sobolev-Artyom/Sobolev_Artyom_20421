use std::{
    error::Error,
    net::{TcpListener},
};

mod lib;

fn main() -> Result<(), Box<dyn Error>> {
    let listener = TcpListener::bind("127.0.0.1:7878")?;
    println!("Сервер запущен на 127.0.0.1:7878");

    for stream_result in listener.incoming() {
        match stream_result {
            Ok(stream) => {
                println!("Клиент подключён");
                if let Err(e) = lib::handle_client(stream) {
                    eprintln!("Ошибка обработки клиента: {}", e);
                }
                println!("Клиент отключён");
            }
            Err(e) => eprintln!("Ошибка подключения: {}", e),
        }
    }
    Ok(())
}
