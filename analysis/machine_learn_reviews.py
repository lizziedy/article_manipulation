from __future__ import print_function
import os
import re
import json
import sys
import copy

import pandas
from pandas.tools.plotting import scatter_matrix
import matplotlib.pyplot as plt
from sklearn import model_selection
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC

import masters_project_helper as mph

import pdb

'''
Installed scipy using instructions here: https://www.scipy.org/install.html
'''


PARAGRAPH_RE = re.compile("^P\d+$")
SENTENCE_RE = re.compile("^P\d+S\d+$")
ARTICLE_RE = re.compile("^Article$")

ID = 'Identifier'
NA = 'Not Applicable'
EMO_1 = 'Primary Emotion'
EMO_2 = 'Secondary Emotion'
SENT = 'Sentiment'
OPINION = 'Opinion Stated as Fact'
GEN_ATTR =  'Generalized Attribution'
QUOTE = 'Quote Used or Referenced'
NON_NEUT = 'Non-Neutral Word Used'
SUBJ_OBJ = 'Subjective, Objective, or Neither'
PERS_MAN = 'Persuasive, Manipulative, or Neither'

NEI_PERS_MAN = 'Neither or (Persuasive or Manipulative)'
PERS_NEI_MAN = '(Neither or Persuasive) or Manipulative'

KEYS = [ID, NA, EMO_1, EMO_2, SENT, OPINION, GEN_ATTR, QUOTE, NON_NEUT, SUBJ_OBJ, PERS_MAN, NEI_PERS_MAN, PERS_NEI_MAN]
CSV_KEYS = [ID, EMO_1, EMO_2, SENT, OPINION, GEN_ATTR, QUOTE, NON_NEUT, SUBJ_OBJ, PERS_MAN, NEI_PERS_MAN, PERS_NEI_MAN]
#CSV_KEYS = [EMO_1, EMO_2, SENT, OPINION, GEN_ATTR, QUOTE, NON_NEUT, SUBJ_OBJ, PERS_MAN]
TRANSFORM_KEYS = [EMO_1, EMO_2, SENT, OPINION, GEN_ATTR, QUOTE, NON_NEUT, SUBJ_OBJ]

EMO_SOME = 'Some Emotions'
EMO_ALL = 'All Emotions'
#NEI_PERS_MAN = 'Niether or (Persuasive or Manipulative)'
NEI_SUBJ_OBJ = '(Neither or Subjective) or (Neither or Objective)'
NEU_SENT = '(Neutral or Negative) or (Neutral or Positive)'

def sample():
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
    names = ['sepal-length', 'sepal-width', 'petal-length', 'petal-width', 'class']
    dataset = pandas.read_csv(url, names=names)

    # shape
    print(dataset.shape)

    # head
    print(dataset.head(20))
    
    dataset.plot(kind='box', subplots=True, layout=(2,2), sharex=False, sharey=False)
    plt.show()

def create_train_test_sets(data_path='articles/master_reviews.csv', train_path='articles/master_reviews_train.csv', test_path='articles/master_reviews_test.csv', data_keys=CSV_KEYS):
    dataset = pandas.read_csv(data_path, names=data_keys)
    train_set, test_set = model_selection.train_test_split(dataset, test_size=.2, random_state=7)
    train_set.to_csv(train_path, header=False)
    test_set.to_csv(test_path, header=False)


    
def learn(train_path, data_path, data_keys):
    pass

def train_feature_data(csv_file='features/features.csv'):
    dataset = pandas.read_csv(csv_file)
    
    del_keys = [ID, NEI_PERS_MAN, PERS_MAN]
    for del_key in del_keys:
        if del_key in dataset:
            del dataset[del_key]
    #['stop_word_perc', 'direct_speech', 'special_punctuation', 'upper_case', 'num_words', 'pos_total', 'verb_count', 'has_negation', 'emo', 'sent']
    del_keys_start = []
    for del_key_start in del_keys_start:
        for key in dataset.keys():
            if key.startswith(del_key_start):
                del dataset[key]
                print('removed ' + key)


    # Split-out validation dataset
    array = dataset.values
    X = array[:,0:dataset.shape[1]-1]
    Y = array[:,dataset.shape[1]-1:dataset.shape[1]]
    validation_size = 0.20
    seed = 7
    X_train, X_validation, Y_train, Y_validation = model_selection.train_test_split(X, Y, test_size=validation_size, random_state=5667489)

    Y_train = Y_train.ravel()
    Y_validation = Y_validation.ravel()
    
    seed = 7
    scoring = 'accuracy'

    # Spot Check Algorithms
    models = []
    models.append(('LR', LogisticRegression()))
    #models.append(('LDA', LinearDiscriminantAnalysis())) # too much collinearity
    models.append(('KNN', KNeighborsClassifier()))
    models.append(('CART', DecisionTreeClassifier()))
    models.append(('NB', GaussianNB()))
    models.append(('SVM', SVC()))
    # evaluate each model in turn
    results = []
    names = []
    for name, model in models:
        kfold = model_selection.KFold(n_splits=10, random_state=seed)
        cv_results = model_selection.cross_val_score(model, X_train, Y_train, cv=kfold, scoring=scoring)
        results.append(cv_results)
        names.append(name)
        msg = "%s: %f (%f)" % (name, cv_results.mean(), cv_results.std())
        print(msg)

    # Make predictions on validation dataset
    for name, model in models:
        print(name)
        print()
        knn = model
        knn.fit(X_train, Y_train)
        predictions = knn.predict(X_validation)
        print(accuracy_score(Y_validation, predictions))
        print(confusion_matrix(Y_validation, predictions))
        print(classification_report(Y_validation, predictions))
    
def article_data(csv_file='articles/master_reviews.csv'):
    transform_keys = copy.deepcopy(TRANSFORM_KEYS)
    dataset = pandas.read_csv(csv_file, names=CSV_KEYS)

    # NOTE:
    # GEN_ATTR, NON_NEUT, SUBJ_OBJ do not seem to contribute much to accuracy
    # Opinion stated as fact does
    # Opinion stated as fact is hard to detect.
    del_keys = [ID, PERS_MAN, NEI_PERS_MAN]#, OPINION]#GEN_ATTR, NON_NEUT, SUBJ_OBJ
    #del_keys = [ID, PERS_MAN, NEI_PERS_MAN, OPINION, EMO_1, EMO_2, GEN_ATTR, NON_NEUT]
    print(del_keys)
    for del_key in del_keys:
        if del_key in dataset:
            del dataset[del_key]
        if del_key in transform_keys:
            transform_keys.remove(del_key)
    print(transform_keys)

    dataset_dummies = pandas.get_dummies(dataset, columns=transform_keys)

    # shape
    print(dataset_dummies.shape)

    # Split-out validation dataset
    array = dataset_dummies.values
    X = array[:,1:dataset_dummies.shape[1]]
    Y = array[:,0]
    validation_size = 0.20
    seed = 7
    X_train, X_validation, Y_train, Y_validation = model_selection.train_test_split(X, Y, test_size=validation_size, random_state=seed)

    seed = 7
    scoring = 'accuracy'
    
    # Spot Check Algorithms
    models = []
    models.append(('LR', LogisticRegression()))
    #models.append(('LDA', LinearDiscriminantAnalysis())) # too much collinearity
    models.append(('KNN', KNeighborsClassifier()))
    models.append(('CART', DecisionTreeClassifier()))
    models.append(('NB', GaussianNB()))
    models.append(('SVM', SVC()))
    # evaluate each model in turn
    results = []
    names = []
    for name, model in models:
        kfold = model_selection.KFold(n_splits=10, random_state=seed)
        cv_results = model_selection.cross_val_score(model, X_train, Y_train, cv=kfold, scoring=scoring)
        results.append(cv_results)
        names.append(name)
        msg = "%s: %f (%f)" % (name, cv_results.mean(), cv_results.std())
        print(msg)

    # Make predictions on validation dataset
    for name, model in models:
        model.fit(X_train, Y_train)
        predictions = model.predict(X_validation)
        print()
        print(name)
        print(accuracy_score(Y_validation, predictions))
        print(confusion_matrix(Y_validation, predictions))
        print(classification_report(Y_validation, predictions))

def make_predictions(models, X_train, Y_train, X_validation, Y_validation):
    # Make predictions on validation dataset
    for name, model in models:
        model.fit(X_train, Y_train)
        predictions = model.predict(X_validation)
        print()
        print(name)
        print(accuracy_score(Y_validation, predictions))
        print(confusion_matrix(Y_validation, predictions))
        print(classification_report(Y_validation, predictions))
            
def main():
    article_data()
    #sample()
    

if __name__ == '__main__':
    main()
