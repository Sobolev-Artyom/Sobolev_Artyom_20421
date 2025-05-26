// Импорт необходимых библиотек
use eframe::{egui};
use std::sync::{Arc, Mutex};
use std::sync::mpsc::channel;
use std::thread;
use std::net::TcpStream;
use std::io::Read;
use image::ImageFormat;
use gui_server::{VideoApp, Params}; // Путь к модулю lib

// Главная функция приложения
fn main() -> Result<(), eframe::Error> {
    // Создаем канал для передачи изображений между потоками
    let (tx, rx) = channel::<egui::ColorImage>();
    
    // Создаем разделяемую изменяемую структуру параметров
    let params = Arc::new(Mutex::new(None));
    let params_clone = params.clone();
    
    // Создаем отдельный поток для работы с сетью
    thread::spawn(move || {
        // Пытаемся подключиться к TCP-серверу
        if let Ok(mut stream) = TcpStream::connect("127.0.0.1:7878") {
            loop {
                // Читаем длину JSON-сообщения (4 байта)
                let mut json_len_buf = [0u8; 4];
                if stream.read_exact(&mut json_len_buf).is_err() {
                    println!("Отключено от сервера");
                    break;
                }
                
                // Преобразуем байты в число (длину JSON)
                let json_len = u32::from_be_bytes(json_len_buf) as usize;

                // Читаем само JSON-сообщение
                let mut json_buf = vec![0u8; json_len];
                stream.read_exact(&mut json_buf).unwrap();
                
                // Преобразуем байты в строку и парсим JSON
                if let Ok(json_str) = String::from_utf8(json_buf) {
                    println!("Получено сообщение: {:?}", json_str);
                    if let Ok(data) = serde_json::from_str::<Params>(&json_str) {
                        // Обновляем параметры в разделяемой структуре
                        let mut par = params_clone.lock().unwrap();
                        *par = Some(data);
                    }
                }
                
                // Обрабатываем поток изображений
                if let Err(e) = handle_image_stream(&mut stream, &tx) {
                    eprintln!("{}", e);
                    break;
                }
            }
        }
    });

    // Настройки графического интерфейса
    let options = eframe::NativeOptions {
        ..Default::default()
    };

    // Запускаем графическое приложение
    eframe::run_native(
        "Video Stream", 
        options, 
        Box::new(|cc| {
            Box::<VideoApp>::new(VideoApp::new(rx, params))
        })
    ) 
}

// Функция для обработки потока изображений
fn handle_image_stream(
    stream: &mut TcpStream, 
    tx: &std::sync::mpsc::Sender<egui::ColorImage>
) -> Result<(), Box<dyn std::error::Error>> {
    // Читаем размер изображения (4 байта)
    let mut size_buf = [0u8; 4];
    stream.read_exact(&mut size_buf)?;

    // Преобразуем байты в число (размер изображения)
    let size = u32::from_be_bytes(size_buf) as usize;
    let mut buffer = vec![0u8; size];
    
    // Читаем само изображение
    stream.read_exact(&mut buffer)?;
    
    // Загружаем изображение из памяти (формат JPEG)
    let img = image::load_from_memory_with_format(&buffer, ImageFormat::Jpeg)?;
    // Конвертируем в RGBA8 формат
    let rgba = img.to_rgba8();
    // Получаем размеры изображения
    let size = [rgba.width() as usize, rgba.height() as usize];
    // Получаем пиксели изображения
    let pixels = rgba.into_vec();
    // Создаем ColorImage для egui
    let color_image = egui::ColorImage::from_rgba_unmultiplied(size, &pixels);

    // Отправляем изображение в канал
    tx.send(color_image).map_err(|e| Box::new(e))?;
    Ok(())
}
