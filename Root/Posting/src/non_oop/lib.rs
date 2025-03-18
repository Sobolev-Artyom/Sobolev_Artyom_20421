pub struct Post {
    content: String,
}

pub struct DraftPost {
    content: String,
}

impl Post {
    pub fn new() -> DraftPost {
        DraftPost {
            content: String::new(),
        }
    }

    pub fn content(&self) -> &str {
        &self.content
    }
}

impl DraftPost {
    pub fn add_text(&mut self, text: &str) {
        self.content.push_str(text);
    }
    
    pub fn request_review(self) -> PendingReviewPost {
        PendingReviewPost {
            content: self.content,
            approval_count: 0,
        }
    }
}

pub struct PendingReviewPost {
    content: String,
    approval_count: u32,
}

impl PendingReviewPost {
    pub fn approve(self) -> (PendingReviewPost, Option<Post>) {
        let new_count = self.approval_count + 1;
        
        if new_count == 2 {
            (PendingReviewPost {
                content: self.content,
                approval_count: new_count,
            }, Some(Post {
                content: self.content,
            }))
        } else {
            (PendingReviewPost {
                content: self.content,
                approval_count: new_count,
            }, None)
        }
    }

    pub fn reject(self) -> DraftPost {
        DraftPost {
            content: self.content,
        }
    }
}
