from transformers import AutoTokenizer, AutoModel

import numpy as np
import torch
import torch.nn.functional as F

MODEL_PATH = "../all-MiniLM-L6-v2"


def create_embedding(sentence: str):
    assert type(sentence) is str
    
    # See https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
    sentences = [sentence]

    def mean_pooling(model_output, attention_mask):
        token_embeddings = model_output[0] # First element of model_output contains all token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    # Load saved models
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModel.from_pretrained(MODEL_PATH)

    # Tokenize sentences
    encoded_input = tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')

    # Compute token embeddings
    with torch.no_grad():
        model_output = model(**encoded_input)

    # Perform pooling
    sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])

    # Normalize embeddings
    sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

    return sentence_embeddings[0]


def find_most_similar_idx(query_embedding, db_embeddings):
    return np.argmax(db_embeddings.dot(query_embedding))