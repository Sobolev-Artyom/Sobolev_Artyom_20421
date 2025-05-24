use eframe::{egui};
use std::sync::{Arc, Mutex};
use std::sync::mpsc::channel;
use std::thread;
use std::net::TcpStream;
use std::io::Read;
use image::ImageFormat;
use gui_server::{VideoApp, Params}; // Путь к модулю lib
fn main() -> Result<(), eframe::Error> {
    let (tx, rx) = channel::<egui::ColorImage>();
    let params = Arc::new(Mutex::new(None));
    let params_clone = params.clone();
    
    thread::spawn(move || {
        if let Ok(mut stream) = TcpStream::connect("127.0.0.1:7878") {
            loop {
                let mut json_len_buf = [0u8; 4];
                if stream.read_exact(&mut json_len_buf).is_err() {
                    println!("Отключено от сервера");
                    break;
                }
                let json_len = u32::from_be_bytes(json_len_buf) as usize;

                let mut json_buf = vec![0u8; json_len];
                stream.read_exact(&mut json_buf).unwrap();
                
                if let Ok(json_str) = String::from_utf8(json_buf) {
                    println!("Получено сообщение: {:?}", json_str);
                    if let Ok(data) = serde_json::from_str::<Params>(&json_str) {
                        let mut par = params_clone.lock().unwrap();
                        *par = Some(data);
                    }
                }
                
                if let Err(e) = handle_image_stream(&mut stream, &tx) {
                    eprintln!("{}", e);
                    break;
                }
            }
        }
    });

    let options = eframe::NativeOptions {
        ..Default::default()
    };

    eframe::run_native("Video Stream", options, Box::new(|cc| {Box::<VideoApp>::new(VideoApp::new(rx, params))})) 
}

fn handle_image_stream(stream: &mut TcpStream, tx: &std::sync::mpsc::Sender<egui::ColorImage>) -> Result<(), Box<dyn std::error::Error>> {
    let mut size_buf = [0u8; 4];
    stream.read_exact(&mut size_buf)?;

    let size = u32::from_be_bytes(size_buf) as usize;
    let mut buffer = vec![0u8; size];
    
    stream.read_exact(&mut buffer)?;
    
    let img = image::load_from_memory_with_format(&buffer, ImageFormat::Jpeg)?;
    let rgba = img.to_rgba8();
    let size = [rgba.width() as usize, rgba.height() as usize];
    let pixels = rgba.into_vec();
    let color_image = egui::ColorImage::from_rgba_unmultiplied(size, &pixels);

    tx.send(color_image).map_err(|e| Box::new(e))?;
    Ok(())
}
