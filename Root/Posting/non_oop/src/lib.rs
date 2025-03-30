pub struct Post {
    content: String,
}

pub struct Draft {
    content: String,
}

impl Post {
    pub fn new() -> Draft {
        Draft {
            content: String::new(),
        }
    }

    pub fn content(&self) -> &str {
        &self.content
    }
}

impl Draft {
    pub fn add_text(&mut self, text: &str) {
        self.content.push_str(text);
    }

    pub fn request_review(self) -> PendingReview_1 {
        PendingReview_1 {
            content: self.content,
        }
    }
}

pub struct PendingReview_1 {
    content: String,
}

impl PendingReview_1 {
    pub fn approve(self) -> PendingReview_2 {
        PendingReview_2 {
            content: self.content,
        }
    }

    pub fn reject(self) -> Draft {
        Draft {
            content: self.content,
        }
    }
}

pub struct PendingReview_2 {
    content: String,
}

impl PendingReview_2 {
    pub fn approve(self) -> Post {
        Post {
            content: self.content,
        }
    }

    pub fn reject(self) -> Draft {
        Draft {
            content: self.content,
        }
    }
}
