// Импорт необходимых модулей из стандартной библиотеки
use std::{
    error::Error,  // Для работы с ошибками
    fs::{self, OpenOptions},  // Для работы с файловой системой
    io::{BufWriter, Write},  // Для буферизированной записи
    net::TcpStream,  // Для сетевого взаимодействия
    sync::mpsc,  // Для межпоточной коммуникации
    thread,  // Для работы с потоками
    time::{Duration, Instant},  // Для работы со временем
};

// Внешние зависимости
use chrono::Local;  // Для форматирования времени
use opencv::{  // Библиотека компьютерного зрения
    core::Vector,
    imgcodecs,  // Для кодирования/декодирования изображений
    prelude::*,
    videoio::{self, CAP_ANY},  // Для работы с видео
};
use serde::Deserialize;  // Для десериализации конфигурации

// Структура конфигурации (читается из TOML файла)
#[derive(Debug, Deserialize)]
struct Config {
    device: Device,  // Настройки устройства ввода
    options: Options,  // Параметры работы системы
}

// Настройки устройства (камера или видеофайл)
#[derive(Debug, Deserialize)]
struct Device {
    path: String,  // Путь к устройству или файлу ("cam" для камеры)
}

// Параметры работы системы
#[derive(Debug, Deserialize)]
struct Options {
    id: String,  // Идентификатор устройства
    start_pos: String,  // Начальная позиция в формате "x,y"
    velocity: String,  // Скорость движения
    altitude: String,  // Высота
}

// Функция парсинга позиции из строки
fn parse_position(pos: &str) -> Result<(i32, i32), Box<dyn Error>> {
    let parts: Vec<&str> = pos.split(',').collect();
    if parts.len() != 2 {
        return Err("Некорректный формат позиции".into());
    }
    Ok((parts[0].trim().parse()?, parts[1].trim().parse()?))
}

// Основная функция обработки клиентского подключения
pub fn handle_client(stream: TcpStream) -> Result<(), Box<dyn Error>> {
    // Чтение конфигурации из файла Options.toml
    let config: Config = toml::from_str(&fs::read_to_string("Options.toml")?)?;

    // Парсинг начальных параметров
    let mut pos = parse_position(&config.options.start_pos)?;
    let velocity: i32 = config.options.velocity.parse()?;
    let mut altitude: f32 = config.options.altitude.parse()?;
    
    // Открытие видео источника (камера или файл)
    let mut cap = open_video_source(&config.device.path)?;

    // Создание каналов для межпоточной коммуникации:
    // - frame_tx/frame_rx для передачи кадров
    // - log_tx/log_rx для передачи логов
    let (frame_tx, frame_rx) = mpsc::channel();
    let (log_tx, log_rx) = mpsc::channel();

    // Запуск потока для логирования
    thread::spawn(move || log_handler(log_rx));
    // Запуск потока для отправки данных по сети
    thread::spawn(move || stream_sender(frame_rx, stream));

    let mut frame = Mat::default();  // Буфер для кадра

    // Проверка возможности чтения первого кадра
    if !cap.read(&mut frame)? || frame.empty() {
        return Err("Не удалось прочитать кадры: камера не работает или нет файла.".into());
    }

    // Основной цикл обработки видео
    while cap.read(&mut frame)? {
        if frame.empty() {
            return Err("Получен пустой кадр — остановка передачи.".into());
        }
        
        // Обновление позиции и высоты
        update_position(&mut pos, velocity, &mut altitude);
        
        // Генерация JSON сообщения с текущими параметрами
        let message = generate_message(&config.options.id, pos.0, pos.1, velocity, altitude);
        
        // Отправка данных в потоки-обработчики
        let _ = log_tx.send(message.clone());
        let _ = frame_tx.send((frame.clone(), message));

        // Поддержание частоты ~60 FPS
        thread::sleep(Duration::from_millis(1000 / 60));
    }

    Ok(())
}

// Функция открытия видео источника
fn open_video_source(path: &str) -> Result<videoio::VideoCapture, Box<dyn Error>> {
    // Открываем либо файл, либо камеру (если path == "cam")
    let mut cap = if path != "cam" {
        videoio::VideoCapture::from_file(path, CAP_ANY)
    } else {
        videoio::VideoCapture::new(0, CAP_ANY)
    }?;
    
    // Проверка успешности открытия
    if !cap.is_opened()? {
        return Err("Не удалось открыть источник видео".into());
    }
    
    // Установка FPS (5 - это PROP_FPS в OpenCV)
    cap.set(5, 60.0)?;
    Ok(cap)
}

// Обработчик логов (работает в отдельном потоке)
fn log_handler(log_rx: mpsc::Receiver<String>) {
    // Открытие файла логов (создание при необходимости)
    let log_file = OpenOptions::new()
        .create(true)
        .append(true)
        .open("params.log")
        .unwrap();
    let mut writer = BufWriter::new(log_file);
    let mut last_log_time = Instant::now();

    // Основной цикл обработки сообщений
    while let Ok(message) = log_rx.recv() {
        // Логируем не чаще чем раз в 5 секунд
        if last_log_time.elapsed() >= Duration::from_secs(5) {
            // Формат: [дата время] сообщение
            writeln!(writer, "[{}] {}", Local::now().format("%Y-%m-%d %H:%M:%S"), message).unwrap();
            writer.flush().unwrap();
            last_log_time = Instant::now();
        }
    }
}

// Отправитель данных по сети (работает в отдельном потоке)
fn stream_sender(frame_rx: mpsc::Receiver<(Mat, String)>, mut stream: TcpStream) {
    while let Ok((frame, message)) = frame_rx.recv() {
        let mut buf = Vector::new();
        // Кодируем кадр в JPEG
        if imgcodecs::imencode(".jpg", &frame, &mut buf, &Vector::new()).is_ok() {
            let bytes = buf.as_slice();  // JPEG данные
            let json_bytes = message.as_bytes();  // JSON данные
            let json_len = (json_bytes.len() as u32).to_be_bytes();  // Длина JSON
            let frame_len = (bytes.len() as u32).to_be_bytes();  // Длина кадра

            // Отправка данных в формате:
            // [4 байта - длина JSON][JSON данные][4 байта - длина кадра][JPEG данные]
            if stream.write_all(&json_len).is_err() || 
               stream.write_all(json_bytes).is_err() || 
               stream.write_all(&frame_len).is_err() || 
               stream.write_all(bytes).is_err() {
                eprintln!("Ошибка при отправке данных");
                break;
            }
        }
    }
}

// Обновление позиции и высоты
fn update_position(pos: &mut (i32, i32), velocity: i32, altitude: &mut f32) {
    pos.0 += velocity;  // Увеличиваем X
    pos.1 += velocity;  // Увеличиваем Y
    *altitude += 0.1;   // Медленно увеличиваем высоту
}

// Генерация JSON сообщения с параметрами
fn generate_message(id: &str, x: i32, y: i32, velocity: i32, altitude: f32) -> String {
    format!(
        "{{\"id\": {}, \"pos\": [{}, {}], \"velocity\": {}, \"altitude\": {}}}",
        id, x, y, velocity, altitude
    )
}
