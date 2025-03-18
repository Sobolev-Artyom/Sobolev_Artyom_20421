pub struct Post {
    state: Option<Box<dyn State>>,
    content: String,
}

impl Post {
    pub fn new() -> Post {
        Post {
            state: Some(Box::new(Draft {})),
            content: String::new(),
        }
    }
    //3
    pub fn add_text(&mut self, text: &str) {
        if let Some(state) = self.state.as_ref() {
            state.add_text(self, text);
        }
    }
    
    pub fn content(&self) -> &str {
        self.state.as_ref().unwrap().content(self)
    }
    
    pub fn request_review(&mut self) {
        if let Some(s) = self.state.take() {
            self.state = Some(s.request_review());
        }
    }
    
    pub fn approve(&mut self) {
        if let Some(s) = self.state.take() {
            self.state = Some(s.approve());
        }
    }
    //1
    pub fn reject(&mut self) {
        if let Some(s) = self.state.take() {
            self.state = Some(s.reject());
        }
    }
}

trait State {
    fn request_review(self: Box<Self>) -> Box<dyn State>;
    fn approve(self: Box<Self>) -> Box<dyn State>;
    //1
    fn reject(self: Box<Self>) -> Box<dyn State>;
    fn content<'a>(&self, post: &'a Post) -> &'a str;
    fn add_text(&self, post: &mut Post, text: &str) {
        // No default implementation
    }
}

struct Draft {}

impl State for Draft {
    fn request_review(self: Box<Self>) -> Box<dyn State> {
        Box::new(PendingReview::new())
    }
    
    fn approve(self: Box<Self>) -> Box<dyn State> {
        self
    }
    //1
    fn reject(self: Box<Self>) -> Box<dyn State> {
        self
    }

    fn add_text(&self, post: &mut Post, text: &str) {
        post.content.push_str(text);
    }
}

struct PendingReview {
    //2
    approval_count: usize,
}

impl PendingReview {
    fn new() -> Self {
        PendingReview {
            //2
            approval_count: 0,
        }
    }
}

impl State for PendingReview {
    fn request_review(self: Box<Self>) -> Box<dyn State> {
        self
    }
    //2
    fn approve(self: Box<Self>) -> Box<dyn State> {
        let mut state = *self; // Dereference to get access to the fields
        state.approval_count += 1;

        if state.approval_count >= 2 {
            Box::new(Published {})
        } else {
            Box::new(state) // Stay in PendingReview until approved twice
        }
    }
    //1
    fn reject(self: Box<Self>) -> Box<dyn State> {
        Box::new(Draft {})
    }
}

struct Published {}

impl State for Published {
    fn request_review(self: Box<Self>) -> Box<dyn State> {
        self
    }

    fn approve(self: Box<Self>) -> Box<dyn State> {
        self
    }
    //1
    fn reject(self: Box<Self>) -> Box<dyn State> {
        self // Published posts cannot be rejected
    }
    
    fn content<'a>(&self, post: &'a Post) -> &'a str {
        &post.content
    }
}
