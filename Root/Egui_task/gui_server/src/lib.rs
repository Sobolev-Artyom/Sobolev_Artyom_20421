use eframe::{egui, App};
use std::sync::{mpsc::Receiver, Arc, Mutex};
use serde::Deserialize;
use egui::Image;

pub struct VideoApp {
    latest_image: Option<egui::ColorImage>,
    receiver: Receiver<egui::ColorImage>,
    params: Arc<Mutex<Option<Params>>>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct Params {
    id: i32,
    pos: [i32; 2],
    radiation: i32,
    velocity: i32, 
}

impl VideoApp {
    pub fn new(receiver: Receiver<egui::ColorImage>, params: Arc<Mutex<Option<Params>>>) -> Self {
        Self {
            latest_image: None,
            receiver,
            params,
        }
    }
}

impl App for VideoApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // Пытаемся получить новое изображение, если оно пришло
        while let Ok(img) = self.receiver.try_recv() {
            self.latest_image = Some(img);
        }

        // Получаем параметры робота
        let param_data = self.params.lock().unwrap().clone();

        egui::CentralPanel::default().show(ctx, |ui| {
            // Видео
            if let Some(img) = &self.latest_image {
                let texture = ui.ctx().load_texture(
                    "video_frame",
                    img.clone(),
                    egui::TextureOptions::default(),
                );
                let size = egui::vec2(1100.0, 720.0);

                ui.add(Image::new(&texture).fit_to_exact_size(size));
                
            } else {
                ui.label("Ожидание первого кадра...");
            }

            // Параметры
            ui.separator();
            ui.label("Параметры робота:");
            if let Some(data) = &param_data {
                ui.label(format!("ID: {}", data.id));
                ui.label(format!("Позиция: {}, {}", data.pos[0], data.pos[1]));
                ui.label(format!("Скорость: {}", data.velocity));
                ui.label(format!("Радиация: {}", data.radiation));
            } else {
                ui.label("Нет данных");
            }
        });

        ctx.request_repaint();
    }
}