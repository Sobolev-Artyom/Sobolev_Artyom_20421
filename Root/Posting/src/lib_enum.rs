pub struct Post {
    state: State,
    content: String,
}

impl Post {
    pub fn new() -> Post {
        Post {
            state: State::Draft,
            content: String::new(),
        }
    }
    
    pub fn add_text(&mut self, text: &str) {
        self.content.push_str(text);
    }
    
    pub fn content(&self) -> &str {
        match self.state {
            State::Draft => "",
            State::PendingReview => "",
            State::Published => &self.content,
        }
    }
    
    pub fn request_review(&mut self) {
        self.state = match self.state {
            State::Draft => State::PendingReview,
            State::PendingReview => State::PendingReview,
            State::Published => State::Published,
        };
    }
    
    pub fn approve(&mut self) {
        self.state = match self.state {
            State::Draft => State::Draft,
            State::PendingReview => State::Published,
            State::Published => State::Published,
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub enum State {
    Draft,
    PendingReview,
    Published,
}
