use unicode_segmentation::UnicodeSegmentation;

fn main() {
    let input = "First apple from box";
    let output = pig_latinize_sentence(input);
    println!("{}", output);
}

fn to_pig_latin(word: &str) -> String {
    let graphemes: Vec<&str> = word.graphemes(true).collect();

    if graphemes.is_empty() {
        return String::from("");
    }

    let first_grapheme = graphemes.first().unwrap();
    let rest_of_word = graphemes.get(1..).unwrap_or_default().join("");

    if ["a", "e", "i", "o", "u"].contains(&first_grapheme) {
        format!("{}-hay", word)
    } else {
        format!("{}-{}ay", rest_of_word, first_grapheme)
    }
}

fn pig_latinize_sentence(sentence: &str) -> String {
    sentence.split_whitespace()
        .map(to_pig_latin)
        .collect::<Vec<String>>()
        .join(" ")
}