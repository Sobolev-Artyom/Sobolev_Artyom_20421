use rayon::ThreadPoolBuilder;

/// ThreadPool представляет пул потоков, который может выполнять работы параллельно.
pub struct ThreadPool {
    pool: rayon::ThreadPool,
}

impl ThreadPool {
    /// Создает новый пул потоков с указанным количеством потоков.
    /// 
    /// # Аргументы
    /// 
    /// * size - Количество потоков в пуле. Должно быть больше 0.
    pub fn new(size: usize) -> ThreadPool {
        let pool = ThreadPoolBuilder::new()
            .num_threads(size)
            .build()
            .expect("Failed to create thread pool");

        ThreadPool { pool }
    }

    /// Выполняет заданную функцию в одном из потоков пула.
    /// 
    /// # Аргументы
    /// 
    /// * f - Функция, которую необходимо выполнить. Должна быть типа FnOnce.
    pub fn execute<F>(&self, f: F)
    where
        F: FnOnce() + Send + 'static,
    {
        self.pool.spawn(f);
    }
}
