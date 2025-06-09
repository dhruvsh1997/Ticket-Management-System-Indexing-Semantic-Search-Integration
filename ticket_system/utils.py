import logging
from transformers import pipeline, BertTokenizer, BertForSequenceClassification
from sentence_transformers import SentenceTransformer
import torch

# Configure logger
# logger = logging.getLogger('ticket_system.utils')
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )

# Configure logging
logger = logging.getLogger('ticket_system')

# Initialize ML models
logger.info("Initializing ML models")
try:
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=3)  # Assume 3 categories
    encoder = SentenceTransformer('all-MiniLM-L6-v2')
    sentiment_pipeline = pipeline("sentiment-analysis")
    logger.info("ML models initialized successfully")
except Exception as e:
    logger.error(f"Error initializing ML models: {str(e)}")
    raise

def classify_ticket(ticket_text):
    logger.debug(f"Classifying ticket text: {ticket_text[:50]}...")
    try:
        breakpoint()
        inputs = tokenizer(ticket_text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        category_id = torch.argmax(outputs.logits).item() + 1  # Adjust for 1-based category IDs
        logger.info(f"Ticket classified with category ID: {category_id}")
        return category_id
    except Exception as e:
        logger.error(f"Error classifying ticket: {str(e)}")
        raise

def analyze_sentiment(text):
    logger.debug(f"Analyzing sentiment for text: {text[:50]}...")
    try:
        score = sentiment_pipeline(text[:512])[0]['score']
        logger.info(f"Sentiment score: {score}")
        return score
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        raise

def find_similar_solutions(ticket_text):
    from .models import KnowledgeBase
    logger.debug(f"Finding similar solutions for text: {ticket_text[:50]}...")
    try:
        embedding = encoder.encode(ticket_text).tolist()
        solutions = KnowledgeBase.objects.raw(
            """
            SELECT *, (embedding <-> %s) as similarity
            FROM ticket_system_knowledgebase
            ORDER BY similarity ASC
            LIMIT 3
            """,
            [embedding]
        )
        logger.info(f"Found {len(solutions)} similar solutions")
        return solutions
    except Exception as e:
        logger.error(f"Error finding similar solutions: {str(e)}")
        raise