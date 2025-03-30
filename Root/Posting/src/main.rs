use matrix::Post;

fn main() {
    let mut post = Post::new();

    // Add text to post (State = Draft)
    post.add_text("I ate a salad for lunch today");
    assert_eq!("", post.content());

    // Request review (State -> PendingReview)
    post.request_review();
    assert_eq!("", post.content());

    // Reject post (State -> Draft)
    post.reject();
    assert_eq!("", post.content());

    // Request review again (State -> PendingReview)
    post.request_review();
    assert_eq!("", post.content());

    post.add_text("He does not ate a salad"); 

    // Aprove post (State = Pending Review)
    post.approve();
    // Aprove post again (State -> Published)
    post.approve();

    assert_eq!("I ate a salad for lunch today", post.content());
}
