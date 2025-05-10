from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import re
import traceback
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID


stemmer = PorterStemmer()

# whoosh schema 
schema = Schema(
    url=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    description=TEXT(stored=True),
    keywords=TEXT(stored=True),
    s3_key=ID(stored=True),
    s3_bucket=ID(stored=True)
)



def index_in_whoosh(data,ix):
    try:
        processed_title = clean_text(data.get("title", ""))
        processed_description = stem_text(clean_text(" ".join(analyze_keywords(data.get("description", "")))))
        processed_keywords = clean_text(" ".join(analyze_keywords(data.get("keywords", ""))))

        print(f"Processed fields for URL {data['url']}:")
        print(f"Title: {processed_title}")
        print(f"Description: {processed_description}")
        print(f"Keywords: {processed_keywords}")
        
        writer = ix.writer()
        writer.update_document(
            url=data["url"],
            title=processed_title,
            description=processed_description,
            keywords=processed_keywords
        )
        writer.commit()
        print(f"Indexed data for URL: {data['url']} in Whoosh.")
        
        
    except Exception as e:
        print(f"Failed to index data in Whoosh: {e}")
        traceback.print_exc()
        raise
    


def clean_text(text):
    """Clean and normalize text for indexing."""
    if not text:
        return ""
    try:
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)
        # Convert to lowercase
        text = text.lower()
        # Strip extra whitespace
        text = text.strip()
        return text
    except Exception as e:
        print(f"Error in clean_text: {e}")
        traceback.print_exc()
        return ""

def analyze_keywords(text):
    """Perform basic keyword analysis."""
    if not text:
        return []

    try:
        words = word_tokenize(text)
        # Remove stop words
        stop_words = set(stopwords.words('english'))
        filtered_words = [word for word in words if word.lower() not in stop_words]
        # Count word frequencies
        word_counts = Counter(filtered_words)
        # Return the most common keywords
        return [word for word, count in word_counts.most_common(10)]
    except Exception as e:
        print(f"Error in analyze_keywords: {e}")
        traceback.print_exc()
        return []
    
def stem_text(text):
    """Stem words in the text."""
    if not text:
        return ""
    try:
        words = word_tokenize(text)
        stemmed_words = [stemmer.stem(word) for word in words]
        return " ".join(stemmed_words)
    except Exception as e:
        print(f"Error in stem_text: {e}")
        traceback.print_exc()
        return ""
