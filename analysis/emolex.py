"""
Lizzie Charbonneau (c) 2017
lizziedy@gmail.com

Uses:
NRC Word-Emotion Association Lexicon
(NRC Emotion Lexicon)
Version 0.92
10 July 2011
Copyright (C) 2011 National Research Council Canada (NRC)
Contact: Saif Mohammad (saif.mohammad@nrc-cnrc.gc.ca)
"""

import nltk
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet
import re
from copy import deepcopy
import pdb

#### START - from nltk/sentiment/util
## http://www.nltk.org/_modules/nltk/sentiment/util.html
## adding to punctuation regex

#////////////////////////////////////////////////////////////
#{ Regular expressions
#////////////////////////////////////////////////////////////

# Regular expression for negation by Christopher Potts
NEGATION = r"""
    (?:
        ^(?:never|no|nothing|nowhere|noone|none|not|
            havent|hasnt|hadnt|cant|couldnt|shouldnt|
            wont|wouldnt|dont|doesnt|didnt|isnt|arent|aint
        )$
    )
    |
    n't"""

NEGATION_RE = re.compile(NEGATION, re.VERBOSE)

CLAUSE_PUNCT = r'^[.:;!?"]|\'\'|``$' # LDC: added quotation marks
CLAUSE_PUNCT_RE = re.compile(CLAUSE_PUNCT)

#### END - from nltk/sentiment/util

class EmoSentFinder:
    EMOTIONS = ['anger', 'disgust', 'fear', 'joy', 'sadness', 'surprise']
    SENTIMENTS = ['positive', 'negative']

    EMO_SENT_MAP = {'anger':['negative'], 'disgust':['negative'], 'fear':['negative'],
                    'joy':['positive'], 'sadness':['negative'],
                    'surprise':['positive', 'negative']}
    SENT_EMO_MAP = {'negative':['anger', 'disgust', 'fear', 'sadness', 'surprise'],
                    'positive':['joy', 'surprise']}
        

    def __init__(self, emolex_file = "analysis/NRC-emotion-lexicon-wordlevel-alphabetized-v0.92.txt"):
        emolex_regex = re.compile('(.+)\t(.+)\t(\d)')
        self._emolex_dict = {}
        self._lemmatizer = WordNetLemmatizer()
        
        with open(emolex_file) as f:
            for line in f:
                match = emolex_regex.match(line)
                if match:
                    word = match.group(1)
                    emo_sent = match.group(2)
                    is_emo_sent = 1 if match.group(3) == '1' else 0

                    if word not in self._emolex_dict:
                        self._emolex_dict[word] = {}
                    self._emolex_dict[word][emo_sent] = is_emo_sent

    def get_sentence_neutral_words(self, sentence):
        tokens = nltk.word_tokenize(sentence)
        words_pos = nltk.pos_tag(tokens)
        for index, word_pos in enumerate(words_pos):
            if word_pos:
                self._get_neutral_word(word_pos)
                
                    
    def get_sentence_statistics(self, sentence):
        tokens = nltk.word_tokenize(sentence)
        words_pos = nltk.pos_tag(tokens)

        negated_tokens = self._mark_negation(tokens)

        sent_sentiments = {'positive':0, 'negative':0}
        sent_sentiments_counting_negation = {'positive':0, 'negative':0}
        sent_emotions = {'anger':0, 'disgust':0, 'fear':0, 'joy':0, 'sadness':0, 'surprise':0}
        sent_emotions_counting_negation = {'anger':0, 'disgust':0, 'fear':0, 'joy':0, 'sadness':0, 'surprise':0}
        sent_sentiment_word_count = 0
        non_stopword_count = len(self.remove_stop_words(tokens))
        word_count = len(tokens)
        has_negation = False
                    
        for index, word_pos in enumerate(words_pos):
            if word_pos:
                emotions = self._get_emotions(word_pos)
                sentiments = self._get_sentiments(word_pos)
                
                has_sentiment = False

                if emotions:
                    self.add_to_dict(emotions, sent_emotions)
                if sentiments:
                    has_sentiment = sum(sentiments.values()) > 0
                    
                    self.add_to_dict(sentiments, sent_sentiments)
                    if has_sentiment:
                        sent_sentiment_word_count += 1
                        
                if negated_tokens[index].endswith('_NEG'):
                    neg_emotions = None
                    neg_sentiments = None
                    has_negation = True
                    
                    neg_word_pos = self._get_antonym(word_pos)
                    if neg_word_pos:
                        neg_emotions = self._get_emotions(neg_word_pos)
                        neg_sentiments = self._get_sentiments(neg_word_pos)
                        if neg_emotions:
                            self.add_to_dict(neg_emotions, sent_emotions_counting_negation)
                        if neg_sentiments and sum(neg_sentiments.values()) > 0:
                            self.add_to_dict(neg_sentiments, sent_sentiments_counting_negation)
                        elif has_sentiment:
                            neg_sentiments = {'positive':sentiments['negative'], 'negative':sentiments['positive']}
                            self.add_to_dict(neg_sentiments, sent_sentiments_counting_negation)
                            

                    ## print(sentence)
                    ## neg_word = "(NONE)"
                    ## if neg_word_pos:
                    ##     neg_word = neg_word_pos[0]
                    ## print(word_pos[0] + " -> " + neg_word)
                    ## if neg_emotions:
                    ##     print(neg_emotions)
                    ## else:
                    ##     print("NO EMOTIONS")
                    ## if neg_sentiments:
                    ##     print(neg_sentiments)
                    ## else:
                    ##     print("NO SENTIMENTS")
                    ## print("\n\n")
                    
                    
                else:
                    if emotions:
                        self.add_to_dict(emotions, sent_emotions_counting_negation)
                    if sentiments:
                        self.add_to_dict(sentiments, sent_sentiments_counting_negation)

        return_hash = {'sentiments':sent_sentiments,
                       'emotions':sent_emotions,
                       'sentiment_word_count':sent_sentiment_word_count,
                       'emotions_counting_negation':sent_emotions_counting_negation,
                       'sentiments_counting_negation':sent_sentiments_counting_negation,
                       'non_stopword_count':non_stopword_count,
                       'word_count':word_count,
                       'has_negation':has_negation}

        return return_hash

    def add_to_dict(self, new_dict, accumulator_dict):
        for key, value in new_dict.items():
            if key in accumulator_dict:
                accumulator_dict[key] += value
            else:
                accumulator_dict[key] = value

    def remove_stop_words(self, word_tokens):
        stopwords = nltk.corpus.stopwords.words('english')
        no_stopword_tokens = [word for word in word_tokens if word.lower() not in stopwords]
        return no_stopword_tokens

    def _get_emotions(self, word_tuple):
        return self._get_emolex_info(word_tuple, EmoSentFinder.EMOTIONS)
    
    def _get_sentiments(self, word_tuple):
        # doing sentiments based off of emotion words which seems like it may improve things
        emotions = self._get_emotions(word_tuple)
        if not emotions:
            return None
        sent_counts = {'negative':0, 'positive':0}
        for emotion, value in emotions.items():
            for sent in self.EMO_SENT_MAP[emotion]:
                sent_counts[sent] += value
            
        #return self._get_emolex_info(word_tuple, EmoSentFinder.SENTIMENTS)
        return sent_counts

    def _get_emolex_info(self, word_tuple, emosent_list):
        orig_word = word_tuple[0]
        ## if orig_word == 'collapsed':
        ##     pdb.set_trace()
            
        if orig_word in self._emolex_dict:
             word_dict = { emosent_key: self._emolex_dict[orig_word][emosent_key] for emosent_key in emosent_list }
             return word_dict

        # get root word if original word not included
        word = self._get_root_word(word_tuple)
        if word and word in self._emolex_dict:
            word_dict = { emosent_key: self._emolex_dict[word][emosent_key] for emosent_key in emosent_list }
            return word_dict
        
        else:
            return None
        
    def _get_root_word(self, word_tuple):
        word = word_tuple[0]
        pos = self._get_wordnet_pos(word_tuple[1])
        if pos == '':
            return None
        else:
            word = self._lemmatizer.lemmatize(word, pos)
            return word
        
    def _get_wordnet_pos(self, nltk_pos):
        if nltk_pos.startswith('J'):
            return wordnet.ADJ
        elif nltk_pos.startswith('V'):
            return wordnet.VERB
        elif nltk_pos.startswith('N'):
            return wordnet.NOUN
        elif nltk_pos.startswith('R'):
            return wordnet.ADV
        else:
            return ''
       
    def _get_nltk_pos(self, wordnet_pos):
        if wordnet_pos == wordnet.ADJ:
            return 'JJ'
        elif wordnet_pos == wordnet.VERB:
            return 'VB'
        elif wordnet_pos == wordnet.NOUN:
            return 'NN'
        elif wordnet_pos == wordnet.ADV:
            return 'RB'
        else:
            return ''

    def _get_antonym(self, word_tuple):
        word = word_tuple[0]
        pos = self._get_wordnet_pos(word_tuple[1])
        if pos == '':
            return None
        lemmatized_word = self._lemmatizer.lemmatize(word, pos)
        
        synsets = wordnet.synsets(word, pos)

        for synset in synsets:
            for lemma in synset.lemmas():
                if lemma.name() == word or lemma.name() == lemmatized_word:
                    if len(lemma.antonyms()) > 0:
                        neg_word = lemma.antonyms()[0].name()
                        pos = self._get_nltk_pos(lemma.synset().pos())
                        return (neg_word, pos)
        return None

    def _get_neutral_word(self, word_tuple):
        word = word_tuple[0]
        pos = self._get_wordnet_pos(word_tuple[1])
        if pos == '':
            return None
        lemmatized_word = self._lemmatizer.lemmatize(word, pos)

        original_sentiments = self._get_sentiments(word_tuple)
        original_emotions = self._get_emotions(word_tuple)
        if not original_sentiments:
            original_sentiments = self._get_sentiments((lemmatized_word, word_tuple[1]))
            original_emotions = self._get_emotions((lemmatized_word, word_tuple[1]))

        sum_emos = 0
        if original_emotions:
            for counts in original_emotions.values():
                sum_emos += counts
        if original_sentiments and (original_sentiments['positive'] > 0 or original_sentiments['negative'] > 0) and sum_emos > 0:
        
            synsets = wordnet.synsets(word, pos)

            for synset in synsets:
                nltk_pos = self._get_nltk_pos(synset.pos())
                for lemma in synset.lemmas():
                    sentiments = self._get_sentiments((lemma.name(), nltk_pos))
                    if not sentiments:
                        lemmatized_word = self._lemmatizer.lemmatize(lemma.name(), synset.pos())
                        sentiments = self._get_sentiments((lemmatized_word, nltk_pos))
                    if sentiments and sentiments['positive'] == 0 and sentiments['negative'] == 0:
                        print("ORIGINAL")
                        print(word)
                        print(original_sentiments)
                        print(original_emotions)
                        print(synsets)
                        print("NEW")
                        print(lemma)
                        print(sentiments)
                        print(synset.definition())
                        print()
                        return (lemma.name(), nltk_pos)

        return None
    
    #### START - from nltk/sentiment/util
    ## http://www.nltk.org/_modules/nltk/sentiment/util.html
    def _mark_negation(self, document, double_neg_flip=False, shallow=False):
        """
        Append _NEG suffix to words that appear in the scope between a negation
        and a punctuation mark.

        :param document: a list of words/tokens, or a tuple (words, label).
        :param shallow: if True, the method will modify the original document in place.
        :param double_neg_flip: if True, double negation is considered affirmation
            (we activate/deactivate negation scope everytime we find a negation).
        :return: if `shallow == True` the method will modify the original document
            and return it. If `shallow == False` the method will return a modified
            document, leaving the original unmodified.

        >>> sent = "I didn't like this movie . It was bad .".split()
        >>> mark_negation(sent)
        ['I', "didn't", 'like_NEG', 'this_NEG', 'movie_NEG', '.', 'It', 'was', 'bad', '.']
        """
        if not shallow:
            document = deepcopy(document)
        # check if the document is labeled. If so, do not consider the label.
        labeled = document and isinstance(document[0], (tuple, list))
        if labeled:
            doc = document[0]
        else:
            doc = document
        neg_scope = False
        for i, word in enumerate(doc):
            if NEGATION_RE.search(word):
                if not neg_scope or (neg_scope and double_neg_flip):
                    neg_scope = not neg_scope
                    continue
                else:
                    doc[i] += '_NEG'
            elif neg_scope and CLAUSE_PUNCT_RE.search(word):
                neg_scope = not neg_scope
            elif neg_scope and not CLAUSE_PUNCT_RE.search(word):
                doc[i] += '_NEG'

        return document
    
    #### END - from nltk/sentiment/util
        
if __name__ == '__main__':
    el = EmoLex()
    print(el._emolex_dict)
