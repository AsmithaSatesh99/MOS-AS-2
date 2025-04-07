import json
import re
import math
import numpy as np
from collections import defaultdict
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.corpus import stopwords
# from sentence_transformers import SentenceTransformer, util
from config import IMAGE_FOLDER, METADATA_FILE

class ImageSearchEngine:
    def __init__(self):
        # Initialize text processing tools
        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Load models
        # self.model = SentenceTransformer('paraphrase-mpnet-base-v2')
        
        # Load and process image surrogates
        self.image_metadata = []
        self.processed_texts = []
        self._load_surrogates()
        
        # Build indexes
        self.inverted_index, self.doc_frequency = self._build_inverted_index()
        self.total_images = len(self.processed_texts)
        self.doc_lengths = self._compute_document_lengths()
        
        # Precompute embeddings
        # self.embeddings = self._compute_embeddings()

    def _load_surrogates(self):
        """Load and process image surrogates from JSON file."""
        with open(METADATA_FILE, 'r') as f:
            surrogates = json.load(f)
        
        for filename, data in surrogates.items():
            # Store complete metadata
            self.image_metadata.append({
                'filename': filename,
                'source_url': data['source_url'],
                'alt_text': data['alt_text'],
                'caption': data['analysis']['caption']
            })
            
            # Combine alt text and BLIP caption for search
            combined_text = f"{data['alt_text']} {data['analysis']['caption']}"
            self.processed_texts.append(self._prepare_text(combined_text))

    def _prepare_text(self, text):
        """Clean and process text for indexing."""
        cleaned = re.sub(r'[^\w\s]', '', text.lower())
        tokens = cleaned.split()
        
        processed = []
        for token in tokens:
            if token not in self.stop_words:
                lemma = self.lemmatizer.lemmatize(token)
                stemmed = self.stemmer.stem(lemma)
                processed.append(stemmed)
        return processed

    def _build_inverted_index(self):
        """Build inverted index from processed documents."""
        inverted_index = defaultdict(list)
        doc_frequency = defaultdict(int)

        for doc_id, doc in enumerate(self.processed_texts):
            term_freq = defaultdict(int)
            for term in doc:
                term_freq[term] += 1

            for term, freq in term_freq.items():
                inverted_index[term].append((doc_id, freq))
                doc_frequency[term] += 1

        return inverted_index, doc_frequency

    def _compute_document_lengths(self):
        """Precompute document lengths for cosine similarity."""
        lengths = [0.0] * self.total_images
        for term, postings in self.inverted_index.items():
            for doc_id, term_freq in postings:
                lengths[doc_id] += (term_freq ** 2)
        return [math.sqrt(length) for length in lengths]

    # def _compute_embeddings(self):
    #     """Precompute embeddings for all images."""
    #     doc_texts = [' '.join(doc) for doc in self.processed_texts]
    #     return self.model.encode(doc_texts, show_progress_bar=True)

    def search_vsm(self, query):
        """Vector Space Model search with proper cosine similarity normalization."""
        processed_query = self._prepare_text(query)
        
        # Calculate query vector (tf-idf weights)
        query_terms = set(processed_query)  # Get unique terms
        query_vector = {}
        query_length = 0.0
        
        for term in query_terms:
            if term in self.inverted_index:
                # Calculate tf-idf for query terms
                tf = processed_query.count(term) / len(processed_query)
                df = self.doc_frequency[term]
                idf = math.log(self.total_images / (df + 1))
                query_vector[term] = tf * idf
                query_length += (query_vector[term] ** 2)
        
        query_length = math.sqrt(query_length)
        
        # Normalize query vector
        if query_length > 0:
            for term in query_vector:
                query_vector[term] /= query_length
        
        # Calculate document scores
        scores = [0.0] * self.total_images
        
        for term in query_vector:
            if term in self.inverted_index:
                for doc_id, term_freq in self.inverted_index[term]:
                    # Calculate tf-idf for document term
                    tf = term_freq / len(self.processed_texts[doc_id])
                    df = self.doc_frequency[term]
                    idf = math.log(self.total_images / (df + 1))
                    doc_weight = tf * idf
                    
                    # Normalize by document length (already precomputed in self.doc_lengths)
                    if self.doc_lengths[doc_id] > 0:
                        doc_weight /= self.doc_lengths[doc_id]
                    
                    scores[doc_id] += query_vector[term] * doc_weight
        
        ranked_indices = np.argsort(scores)[::-1]
        return [(self.image_metadata[idx], scores[idx]) for idx in ranked_indices if scores[idx] > 0]

    def search_bm25(self, query, k1=1.5, b=0.75):
        """BM25 search."""
        processed_query = self._prepare_text(query)
        avg_doc_len = np.mean([len(doc) for doc in self.processed_texts])
        scores = [0.0] * self.total_images

        for term in processed_query:
            if term in self.inverted_index:
                df = self.doc_frequency[term]
                idf = math.log((self.total_images - df + 0.5) / (df + 0.5))

                for doc_id, term_freq in self.inverted_index[term]:
                    doc_len = len(self.processed_texts[doc_id])
                    numerator = term_freq * (k1 + 1)
                    denominator = term_freq + k1 * (1 - b + b * (doc_len / avg_doc_len))
                    scores[doc_id] += idf * (numerator / denominator)
        
        ranked_indices = np.argsort(scores)[::-1]
        return [(self.image_metadata[idx], scores[idx]) for idx in ranked_indices if scores[idx] > 0]

    # def search_semantic(self, query):
    #     """Semantic search."""
    #     query_embedding = self.model.encode([query])[0]
    #     scores = util.cos_sim(query_embedding, self.embeddings).squeeze().tolist()
        
    #     ranked_indices = np.argsort(scores)[::-1]
    #     return [(self.image_metadata[idx], scores[idx]) for idx in ranked_indices if scores[idx] > 0]

    def get_all_images(self):
        """Get all images with their metadata."""
        return self.image_metadata