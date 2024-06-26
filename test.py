import streamlit as st
from transformers import AutoTokenizer, GPT2LMHeadModel
import torch
import nltk
from nltk.util import ngrams
from nltk.lm.preprocessing import pad_sequence
from nltk.probability import FreqDist
import plotly.express as px
from collections import Counter
from nltk.corpus import stopwords
import string
from googletrans import Translator

nltk.download('punkt')
nltk.download('stopwords')

# Load GPT-2 tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained('gpt2')

# Initialize the translator
translator = Translator()

def translate_text(text, src_lang='auto', dest_lang='en'):
    try:
        translation = translator.translate(text, src=src_lang, dest=dest_lang)
        return translation.text
    except Exception as e:
        st.error(f"Translation error: {e}")
        return text

def calculate_perplexity(text):
    encoded_input = tokenizer.encode(text, add_special_tokens=False, return_tensors='pt')
    
    if encoded_input.numel() == 0:
        return float('inf')  # Return a high value to indicate the error

    input_ids = encoded_input

    with torch.no_grad():
        outputs = model(input_ids)
        logits = outputs.logits

    # Shift logits and input_ids for cross entropy calculation
    shift_logits = logits[:, :-1, :].contiguous()
    shift_labels = input_ids[:, 1:].contiguous()

    loss = torch.nn.functional.cross_entropy(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
    perplexity = torch.exp(loss)
    return perplexity.item()

def calculate_burstiness(text):
    tokens = nltk.word_tokenize(text.lower())
    word_freq = FreqDist(tokens)
    repeated_count = sum(count > 1 for count in word_freq.values())
    burstiness_score = repeated_count / len(word_freq)
    return burstiness_score

def plot_top_repeated_words(text):
    # Tokenize the text and remove stopwords and special characters
    tokens = text.split()
    stop_words = set(stopwords.words('english'))
    tokens = [token.lower() for token in tokens if token.lower() not in stop_words and token.lower() not in string.punctuation]

    # Count the occurrence of each word
    word_counts = Counter(tokens)

    # Get the top 10 most repeated words
    top_words = word_counts.most_common(10)

    # Extract the words and their counts for plotting
    words = [word for word, count in top_words]
    counts = [count for word, count in top_words]

    # Plot the bar chart using Plotly
    fig = px.bar(x=words, y=counts, labels={'x': 'Words', 'y': 'Counts'}, title='Top 10 Most Repeated Words')
    st.plotly_chart(fig, use_container_width=True)

st.set_page_config(layout="wide")

st.title("GPT Shield: AI Plagiarism Detector")
text_area = st.text_area("Enter text", "")
language = st.selectbox("Select text language", options=['auto', 'en', 'es', 'fr', 'de', 'zh-cn', 'ja'])

if text_area:
    if st.button("Analyze"):
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.info("Your Input Text")
            st.success(text_area)
        
        with col2:
            st.info("Detection Score")
            translated_text = translate_text(text_area, src_lang=language, dest_lang='en')
            perplexity = calculate_perplexity(translated_text)
            burstiness_score = calculate_burstiness(translated_text)

            st.write("Perplexity:", perplexity)
            st.write("Burstiness Score:", burstiness_score)

            if perplexity < 1000 and burstiness_score > 0.5:
                st.error("Text Analysis Result: AI generated content")
            else:
                st.success("Text Analysis Result: Likely not generated by AI")

            
            st.warning("Disclaimer: AI plagiarism detector apps can assist in identifying potential instances of plagiarism; however, it is important to note that their results may not be entirely flawless or completely reliable. These tools employ advanced algorithms, but they can still produce false positives or false negatives. Therefore, it is recommended to use AI plagiarism detectors as a supplementary tool alongside human judgment and manual verification for accurate and comprehensive plagiarism detection.")
        
        with col3:
            st.info("Basic Details")
            plot_top_repeated_words(translated_text)
