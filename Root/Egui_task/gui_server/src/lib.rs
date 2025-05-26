// Импорт необходимых библиотек
use eframe::{egui, App};  // Фреймворк для создания GUI
use std::sync::{mpsc::Receiver, Arc, Mutex};  // Для потокобезопасных структур
use serde::Deserialize;  // Для десериализации данных
use egui::Image;  // Виджет для отображения изображений

// Основная структура приложения
pub struct VideoApp {
    latest_image: Option<egui::ColorImage>,  // Текущее изображение для отображения
    receiver: Receiver<egui::ColorImage>,  // Канал для получения новых изображений
    params: Arc<Mutex<Option<Params>>>,  // Параметры робота (потокобезопасные)
}

// Структура параметров робота
#[derive(Debug, Deserialize, Clone)]
pub struct Params {
    id: i32,  // Идентификатор робота
    pos: [i32; 2],  // Позиция [x, y]
    radiation: i32,  // Уровень радиации
    velocity: i32,  // Скорость движения
}

impl VideoApp {
    // Конструктор приложения
    pub fn new(receiver: Receiver<egui::ColorImage>, params: Arc<Mutex<Option<Params>>>) -> Self {
        Self {
            latest_image: None,  // Изначально изображения нет
            receiver,  // Канал для получения изображений
            params,  // Общие параметры робота
        }
    }
}

// Реализация интерфейса App для основного цикла обновления GUI
impl App for VideoApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // Пытаемся получить все доступные новые изображения из канала
        while let Ok(img) = self.receiver.try_recv() {
            self.latest_image = Some(img);  // Сохраняем последнее полученное изображение
        }

        // Блокируем мьютекс для чтения параметров робота
        let param_data = self.params.lock().unwrap().clone();

        // Создаем центральную панель интерфейса
        egui::CentralPanel::default().show(ctx, |ui| {
            // Раздел отображения видео
            if let Some(img) = &self.latest_image {
                // Создаем текстуру из изображения
                let texture = ui.ctx().load_texture(
                    "video_frame",  // Идентификатор текстуры
                    img.clone(),  // Данные изображения
                    egui::TextureOptions::default(),  // Параметры текстуры
                );
                let size = egui::vec2(1100.0, 720.0);  // Фиксированный размер для отображения

                // Добавляем изображение с указанным размером
                ui.add(Image::new(&texture).fit_to_exact_size(size));
                
            } else {
                // Если изображения еще нет, показываем сообщение
                ui.label("Ожидание первого кадра...");
            }

            // Раздел отображения параметров
            ui.separator();  // Визуальный разделитель
            ui.label("Параметры робота:");
            
            if let Some(data) = &param_data {
                // Если параметры доступны, отображаем их
                ui.label(format!("ID: {}", data.id));
                ui.label(format!("Позиция: {}, {}", data.pos[0], data.pos[1]));
                ui.label(format!("Скорость: {}", data.velocity));
                ui.label(format!("Радиация: {}", data.radiation));
            } else {
                // Если параметры недоступны
                ui.label("Нет данных");
            }
        });

        // Запрашиваем перерисовку для плавного обновления
        ctx.request_repaint();
    }
}
