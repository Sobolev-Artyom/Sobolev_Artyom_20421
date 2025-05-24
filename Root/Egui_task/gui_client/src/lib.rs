use std::{
    error::Error,
    fs::{self, OpenOptions},
    io::{BufWriter, Write},
    net::TcpStream,
    sync::mpsc,
    thread,
    time::{Duration, Instant},
};
use chrono::Local;
use opencv::{
    core::Vector,
    imgcodecs,
    prelude::*,
    videoio::{self, CAP_ANY},
};
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct Config {
    device: Device,
    options: Options,
}

#[derive(Debug, Deserialize)]
struct Device {
    path: String,
}

#[derive(Debug, Deserialize)]
struct Options {
    id: String,
    start_pos: String,
    velocity: String,
    altitude: String,
}

fn parse_position(pos: &str) -> Result<(i32, i32), Box<dyn Error>> {
    let parts: Vec<&str> = pos.split(',').collect();
    if parts.len() != 2 {
        return Err("Некорректный формат позиции".into());
    }
    Ok((parts[0].trim().parse()?, parts[1].trim().parse()?))
}

pub fn handle_client(stream: TcpStream) -> Result<(), Box<dyn Error>> {
    let config: Config = toml::from_str(&fs::read_to_string("Options.toml")?)?;

    let mut pos = parse_position(&config.options.start_pos)?;
    let velocity: i32 = config.options.velocity.parse()?;
    let mut altitude: f32 = config.options.altitude.parse()?;
    let mut cap = open_video_source(&config.device.path)?;

    let (frame_tx, frame_rx) = mpsc::channel();
    let (log_tx, log_rx) = mpsc::channel();

    thread::spawn(move || log_handler(log_rx));
    thread::spawn(move || stream_sender(frame_rx, stream));

    let mut frame = Mat::default();

    if !cap.read(&mut frame)? || frame.empty() {
        return Err("Не удалось прочитать кадры: камера не работает или нет файла.".into());
    }

    while cap.read(&mut frame)? {
        if frame.empty() {
            return Err("Получен пустой кадр — остановка передачи.".into());
        }
        update_position(&mut pos, velocity, &mut altitude);
        
        let message = generate_message(&config.options.id, pos.0, pos.1, velocity, altitude);
        
        let _ = log_tx.send(message.clone());
        let _ = frame_tx.send((frame.clone(), message));

        thread::sleep(Duration::from_millis(1000 / 60));
    }

    Ok(())
}

fn open_video_source(path: &str) -> Result<videoio::VideoCapture, Box<dyn Error>> {
    let mut cap = if path != "cam" {
        videoio::VideoCapture::from_file(path, CAP_ANY)
    } else {
        videoio::VideoCapture::new(0, CAP_ANY)
    }?;
    
    if !cap.is_opened()? {
        return Err("Не удалось открыть источник видео".into());
    }
    
    cap.set(5, 60.0)?;
    Ok(cap)
}

fn log_handler(log_rx: mpsc::Receiver<String>) {
    let log_file = OpenOptions::new()
        .create(true)
        .append(true)
        .open("params.log")
        .unwrap();
    let mut writer = BufWriter::new(log_file);
    let mut last_log_time = Instant::now();

    while let Ok(message) = log_rx.recv() {
        if last_log_time.elapsed() >= Duration::from_secs(5) {
            writeln!(writer, "[{}] {}", Local::now().format("%Y-%m-%d %H:%M:%S"), message).unwrap();
            writer.flush().unwrap();
            last_log_time = Instant::now();
        }
    }
}

fn stream_sender(frame_rx: mpsc::Receiver<(Mat, String)>, mut stream: TcpStream) {
    while let Ok((frame, message)) = frame_rx.recv() {
        let mut buf = Vector::new();
        if imgcodecs::imencode(".jpg", &frame, &mut buf, &Vector::new()).is_ok() {
            let bytes = buf.as_slice();
            let json_bytes = message.as_bytes();
            let json_len = (json_bytes.len() as u32).to_be_bytes();
            let frame_len = (bytes.len() as u32).to_be_bytes();

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
fn update_position(pos: &mut (i32, i32), velocity: i32, altitude: &mut f32) {
    pos.0 += velocity;
    pos.1 += velocity;
    *altitude += 0.1;
}

fn generate_message(id: &str, x: i32, y: i32, velocity: i32, altitude: f32) -> String {
    format!(
        "{{\"id\": {}, \"pos\": [{}, {}], \"velocity\": {}, \"altitude\": {}}}",
        id, x, y, velocity, altitude
    )
}