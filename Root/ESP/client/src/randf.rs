use rand::prelude::*;

pub struct RANDF {
    rng: ThreadRng,
    prev_humidity: f32,
    prev_temperature: f32
}

impl RANDF {
    pub fn build() -> Self {
        RANDF {
            rng: rand::rng(),
            prev_humidity: rand::random_range(0.0..100.0),
            prev_temperature: rand::random_range(-40.0..80.0)
        }
    }

    pub fn read_humidity(&mut self) -> f32 {
        self.prev_humidity += self.rng.random_range(-20.0..20.0);
        if self.prev_humidity > 100.0 {self.prev_humidity = 100.0}
        if self.prev_humidity < 0.0 {self.prev_humidity = 0.0};
        return self.prev_humidity
    }

    pub fn read_temperature(&mut self) -> f32 {
        self.prev_temperature += self.rng.random_range(-20.0..20.0);
        if self.prev_temperature > 80.0 {self.prev_temperature = 80.0}
        if self.prev_temperature < -40.0 {self.prev_temperature = -40.0};
        return self.prev_temperature
    }
}