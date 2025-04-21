use std::{
    sync::{mpsc, Arc, Mutex},
    thread,
};

/// ThreadPool представляет пул потоков, который может выполнять работы параллельно.
pub struct ThreadPool {
    workers: Vec<Worker>,
    sender: Option<mpsc::Sender<Job>>,
}

/// Типы работы, которую будет выполнять пул потоков.
type Job = Box<dyn FnOnce() + Send + 'static>;

impl ThreadPool {
    /// Создает новый пул потоков с указанным количеством потоков.
    /// 
    /// # Аргументы
    /// 
    /// * size - Количество потоков в пуле. Должно быть больше 0.
    pub fn new(size: usize) -> ThreadPool {
        assert!(size > 0);

        let (sender, receiver) = mpsc::channel();
        let receiver = Arc::new(Mutex::new(receiver));

        let mut workers = Vec::with_capacity(size);

        for id in 0..size {
            workers.push(Worker::new(id, Arc::clone(&receiver)));
        }

        ThreadPool {
            workers,
            sender: Some(sender),
        }
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
        let job = Box::new(f);

        if let Some(sender) = self.sender.as_ref() {
            if let Err(e) = sender.send(job) {
                eprintln!("Failed to send job to thread pool: {}", e);
            }
        } else {
            eprintln!("ThreadPool has been shut down.");
        }
    }
}

/// Worker представляет отдельный поток в пуле.
struct Worker {
    id: usize,
    thread: thread::JoinHandle<()>,
}

impl Worker {
    /// Создает нового рабочего потока с указанным идентификатором.
    /// 
    /// # Аргументы
    /// 
    /// * id - Идентификатор рабочего потока.
    /// * receiver - Канал, из которого рабочий поток будет получать задачи.
    fn new(id: usize, receiver: Arc<Mutex<mpsc::Receiver<Job>>>) -> Worker {
        let thread = thread::spawn(move || loop {
            let message = receiver.lock().expect("Failed to lock receiver");

            match message.recv() {
                Ok(job) => {
                    println!("Worker {id} got a job; executing.");
                    job();
                }
                Err(_) => {
                    println!("Worker {id} disconnected; shutting down.");
                    break;
                }
            }
        });

        Worker { id, thread }
    }
}

/// Логика для освобождения ресурсов при удалении пула потоков.
impl Drop for ThreadPool {
    fn drop(&mut self) {
        drop(self.sender.take());

        for worker in self.workers.drain(..) {
            println!("Shutting down worker {}", worker.id);
            if let Err(e) = worker.thread.join() {
                eprintln!("Failed to join worker thread: {:?}", e);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_thread_pool_size() {
        let pool = ThreadPool::new(4);
        assert_eq!(pool.workers.len(), 4);
    }

    #[test]
    fn test_execute_job() {
        let pool = ThreadPool::new(2);
        let (sender, receiver) = mpsc::channel();

        pool.execute(move || {
            sender.send(42).unwrap();
        });

        let result = receiver.recv().unwrap();
        assert_eq!(result, 42);
    }
}