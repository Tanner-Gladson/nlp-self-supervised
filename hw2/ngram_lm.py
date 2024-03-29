import numpy as np
from matplotlib import pyplot as plt
from tqdm import tqdm
from datasets import load_dataset
from sentence_splitter import SentenceSplitter
from transformers import AutoTokenizer
from collections import Counter, defaultdict # we will using "Counter" data structure for counting word co-occurences


def load_data():
    print(f"{'-' * 10} Load Dataset {'-' * 10}")
    train_dataset = load_dataset(path="wikitext", name="wikitext-103-raw-v1", split="train")
    dev_dataset = load_dataset(path="wikitext", name="wikitext-103-raw-v1", split="validation")

    print(f"{'-' * 10} an example from the train set {'-' * 10}")
    print(train_dataset['text'][10])

    return train_dataset, dev_dataset


def sentence_split_and_tokenize_demo(data, splitter, tokenizer):
    print(f"{'-' * 10} split into sentences {'-' * 10}")
    print(splitter.split(data['text'][10]))
    sentences = splitter.split(data['text'][10])
    for sentence in sentences:
        print(f" -> {sentence}")

    print(f"{'-' * 10} tokenize the first sentence {'-' * 10}")
    tokens = tokenizer.tokenize(sentences[0])
    print(f"Tokens: {tokens}")
    print(f"Tokens to indices: {tokenizer.convert_tokens_to_ids(tokens)}")


def create_ngrams(data, n, splitter, tokenizer):
    ngrams = Counter()
    ngram_context = Counter()
    next_word_candidates = defaultdict(set)

    # Count the occurrences of each n-gram and the context (i.e. the (n-1)-grams) over the dataset
    # It might take a few minutes to run
    for paragraph in tqdm(data['text']):
        # if the paragraph is too short, skip it
        if len(paragraph) < 3:
            continue

        # iterate over sentences given by our sentence splitter
        for sentence in splitter.split(paragraph):

            # drop short sentences
            # TODONE
            tokens = tokenizer.tokenize(sentence)
            if len(tokens) < 7:
                break

            # Iterate over all n-grams to count their occurrences
            for idx, _ in enumerate(tokens):
                if idx + n >= len(tokens):
                    # have already traversed all of the n-grams in this sentence
                    break
                # TODONE
                # - 'ngrams' is a Counter with tuple of n-grams as keys and its occurrence count as values
                # - 'ngram_context' is a Counter with tuple of the context (i.e. the (n-1)-grams) as keys
                #   and its occurrence count as values
                # - 'next_word_candidates' is a dictionary with tuple of the context
                #   (i.e. the (n-1)-grams) as keys and a set of possible next words as values

                if (tuple(tokens[idx:idx + n - 1]) == None) :
                    print("WARNING: we have a context which is None")

                ngrams[tuple(tokens[idx:idx + n])] += 1
                ngram_context[tuple(tokens[idx:idx + n - 1])] += 1
                next_word_candidates[tuple(tokens[idx:idx + n - 1])].add(tokens[idx + n -1])

    # Sort all the next word candidates
    # This is to make the prediction deterministic
    # i.e. when multiple next words have the same probability, we pick the first one alphabetically
    sorted_next_word_candidates = defaultdict(list)
    for context, next_words in next_word_candidates.items():
        sorted_next_word_candidates[context] = sorted(list(next_words))

    # Get the most "probable" next word for each context as the prediction
    # It might take a few minutes to run
    next_word_pred = {}
    next_word_scores = {}
    for context, next_words in sorted_next_word_candidates.items():
        # store the estimated probability of each next word
        scores = []
        for nw in next_words:
            # TODONE: compute the estimated probability of the next word given the context
            # hint: use the counters 'ngrams' and 'ngram_context' you have created above

            ngram_as_list = list(context)
            ngram_as_list.append(nw)
            ngram_as_tuple = tuple(ngram_as_list)
            score = ngrams[ngram_as_tuple] / ngram_context[context]
            scores.append(score)

        # record the most probable next word as the prediction
        next_word_pred[context] = next_words[np.argmax(scores)]

        # record the estimated probability of each next word
        next_word_scores[context] = np.array(scores)

    return next_word_pred, next_word_scores, sorted_next_word_candidates


# Generation function: given a prefix, generate the completion by iteratively taking the (n - 1) grams context and predict the next word
def generate_text(word_pred, tokenizer, n, prefix, max_len=100, stop_token="."):
    res = tokenizer.tokenize(prefix)
    pred = ""
    count = 0
    while count < max_len and pred != stop_token:
        pred = word_pred[tuple(res[-n+1:])]
        res.append(pred)
        count += 1
    return tokenizer.convert_tokens_to_string(res)


def largest_indices(arr, num_indices):
    return np.argsort(arr)[len(arr) - num_indices:]


# Plot ngram probabilities for the given context
def plot_next_word_prob(word_scores, word_candidates, context, top=10, save_path=None):
    # TODONE: plot the top 10 next word probabilities after the given context
    # Hint: follow the hints in the pdf description for how to use matplotlib to plot the bar chart
    # - word_scores is a dictionary with tuple of the context as keys and an array of probabilities as values (the next_word_scores in create_ngrams function)
    # - word_candidates is a dictionary with tuple of the context as keys and a list of possible next words as values (the sorted_next_word_candidates in create_ngrams function)
    # - for a given context, elements in word_scores[context] and word_candidates[context] have one-to-one correspondence
    # - context is a tuple of words
    
    scores = word_scores[context]
    candidates = word_candidates[context]

    indices_of_largest = largest_indices(scores, top)
    top_scores = scores[indices_of_largest]
    top_candidates = [candidates[i] for i in indices_of_largest]

    # Plot the top candidates and their scores using For bomatplotlib
    plt.figure(figsize=(16, 8))  # We need big figure
    plt.bar(top_candidates, top_scores)
    plt.xlabel('Next Word')
    plt.ylabel('Probability')
    plt.title('Top 10 Next Word Probabilities')

    # If the save_path is not None, save the plot as a pdf
    if save_path is not None:
        plt.savefig(save_path)

def run_ngram():
    train_data, dev_data = load_data()
    splitter = SentenceSplitter(language='en')
    tokenizer = AutoTokenizer.from_pretrained("bert-base-cased")
    sentence_split_and_tokenize_demo(train_data, splitter, tokenizer)
    word_pred, next_word_scores, next_word_candidates = create_ngrams(train_data[:100000], 3, splitter, tokenizer)

    # TODONE: paste the generated plots to the pdf (done in the plot function)
    context1 = ("move", "to")
    context2 = ("the", "news")
    print(f"{'-' * 10} plot the top 10 next word probabilities after {context1} {'-' * 10}")
    plot_next_word_prob(next_word_scores, next_word_candidates, context1, top=10, save_path="ngram_context1.png")
    print(f"{'-' * 10} plot the top 10 next word probabilities after {context2} {'-' * 10}")
    plot_next_word_prob(next_word_scores, next_word_candidates, context2, top=10, save_path="ngram_context2.png")

    # TODONE: paste the generated completion of these two prefixes to the pdf
    prefix1 = "According to the report"
    prefix2 = "The president of the association"
    completion1 = generate_text(word_pred, tokenizer, 3, prefix1, max_len=30)
    completion2 = generate_text(word_pred, tokenizer, 3, prefix2, max_len=30)
    print(f"{'-' * 10} generated text 1 {'-' * 10}")
    print(completion1)
    print(f"{'-' * 10} generated text 2 {'-' * 10}")
    print(completion2)

    # We want to save the completions to a PDF file, not just plain text
    with open("ngram_completions1.txt", "w") as f:
        f.write(completion1)
    
    with open("ngram_completions2.txt", "w") as f:
        f.write(completion2)

