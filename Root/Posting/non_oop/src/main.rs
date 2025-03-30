use matrix::Post;

fn main() {
    // Add text to post (State = Draft)
    let mut post = Post::new();

    post.add_text("I ate a salad for lunch today");

    // Request review (State -> PendingReview)
    let post = post.request_review();

    // Reject post (State -> Draft)
    let post = post.reject();
    
    // Request review again (State -> PendingReview)
    let post = post.request_review();

    // Aprove post (State = Pending Review)
    let post = post.approve();

    // Aprove post again (State -> Published)
    let post = post.approve();

    assert_eq!("I ate a salad for lunch today", post.content());
}
