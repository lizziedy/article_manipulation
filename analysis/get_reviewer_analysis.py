from __future__ import print_function
import os
import re
import json
import csv
import sys
import copy

import masters_project_helper as mph

import pdb

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

EMO_SOME = 'Some Emotions'
EMO_ALL = 'All Emotions'
NEI_PERS_MAN = 'Neither or (Persuasive or Manipulative)'
PERS_NEI_MAN = '(Neither or Persuasive) or Manipulative'
NEI_SUBJ_OBJ = '(Neither or Subjective) or (Neither or Objective)'
NEU_SENT = '(Neutral or Negative) or (Neutral or Positive)'


KEYS = [ID, NA, EMO_1, EMO_2, SENT, OPINION, GEN_ATTR, QUOTE, NON_NEUT, SUBJ_OBJ, PERS_MAN]
CSV_KEYS = [ID, EMO_1, EMO_2, SENT, OPINION, GEN_ATTR, QUOTE, NON_NEUT, SUBJ_OBJ, PERS_MAN, NEI_PERS_MAN, PERS_NEI_MAN]

################################################################################
## GET REVIEWS
################################################################################

def get_article_review(article_info, reviewer):
    article_name = mph.get_article_name(article_info)
    topic = mph.get_article_topic(article_info)
    
    reviewer_name = reviewer['name'].replace(" ", "_")
    survey_name = reviewer_name + "_" + article_name
    survey_name = survey_name.replace("'", "\\'")
    print(survey_name)

    topic_folder = gah.get_drive_object(topic, SURVEY_DIRECTORY_ID, gah.DRIVE_FOLDER_TYPE)
    folder =gah.get_drive_object(article_name, topic_folder['id'], gah.DRIVE_FOLDER_TYPE)
    survey_file = gah.get_drive_object(survey_name, folder['id'], gah.DRIVE_SPREADSHEET_TYPE)

    results = gah.get_sheets_values(survey_file['id'], 'Questionnaire', 'A2:K', KEYS)

    named_results = {}
    if survey_filled_out(results):
        cleanup_survey_results(results)
        for key,  value in results.items():
            named_results[key] = {reviewer['name']: value}
    else:
        named_results = None

    print(json.dumps(named_results, indent=2, separators=(',', ': ')))
    return named_results

def survey_filled_out(survey_results):
    article_summary = survey_results['Article']
    any_filled = False
    for key, value in article_summary.items():
        if key != ID and key != NA and value:
            any_filled = True
            break
    return any_filled

def cleanup_survey_results(survey_results):
    for results in survey_results.values():
        # make sure all n/a sentences captured. e.g., some people didn't know how to handle improper sentence break downs
        none_filled = True
        if NA not in results or results[NA] != 'True':
            for key, value in results.items():
                if key != ID and key != NA and value:
                    none_filled = False
                    break
            if none_filled:
                results[NA] = 'True'

        # fill in all default values if fields left empty
        if results[NA] != 'True':
            for key, value in results.items():
                if not value:
                    if key == NA or key == OPINION or key == GEN_ATTR or key == QUOTE or key == NON_NEUT:
                        results[key] = 'False'
                    elif key == EMO_1 or key == EMO_2:
                        results[key] = 'None'
                    elif key == SENT:
                        results[key] = 'Neutral'
                    elif key == SUBJ_OBJ or key == PERS_MAN:
                        results[key] =  'Neither'

        # change string to boolean
        for key, value in results.items():
            if value == 'True':
                results[key] = True
            elif value == 'False':
                results[key] = False

def merge_reviews(complete_review_list, new_review):
    for key in complete_review_list.keys():
        new_key = list(new_review[key].keys())[0]
        complete_review_list[key][new_key] = new_review[key][new_key]

def get_article_reviews(test_articles_path='articles/test_articles.json', reviews_output='articles/reviews.json', non_reviewers_output='articles/non_reviewers.json'):
    test_articles_info = mph.read_json(test_articles_path)
    
    non_responders = {}

    article_reviews = {}
    for test_article_info in test_articles_info.values():
        reviews = article_reviews[test_article_info['id']] = {}
        for reviewer in test_article_info['reviewers']:
            survey_results = get_article_review(test_article_info, reviewer)
            if survey_results:
                if len(reviews) > 0:
                    merge_reviews(reviews, survey_results)
                else:
                    reviews.update(survey_results)
            else:
                article_id = test_article_info['id']
                if article_id not in non_responders:
                    non_responders[article_id] = []
                    
                non_responders[article_id].append({'article_name':mph.get_article_name(test_article_info), 'id': test_article_info['id'], 'reviewer':reviewer})

    mph.write_json(article_reviews, reviews_output)
    mph.write_json(non_responders, non_reviewers_output)

    return reviews_output

################################################################################
## ANALYZE REVIEWS
################################################################################

def get_num_sentences(reviews):
    pass

def get_na_agreement(component, review1, review2):
    if review1[NA] or review2[NA]:
        component[NA] = True
    else:
        component[NA] = False

def get_emo_agreement(component, review1, review2):
    # is this too conservative of an approach?
    emo_1_done = False
    emo_2_done = False
    if review1[EMO_1] == review2[EMO_1] or review1[EMO_1] == review2[EMO_2]:
        component[EMO_1] = review1[EMO_1]
        emo_1_done = True
    if review1[EMO_2] == review2[EMO_1] or review1[EMO_2] == review2[EMO_2]:
        if emo_1_done:
            component[EMO_2] = review1[EMO_2]
            emo_2_done = True
        else:
            component[EMO_1] = review1[EMO_2]
            emo_1_done = True

    if not emo_1_done:
        component[EMO_1] = 'None'
    if not emo_2_done:
        component[EMO_2] = 'None'

def get_sent_agreement(component, review1, review2):
    if review1[SENT] == review2[SENT]:
        component[SENT] = review1[SENT]
    else:
        component[SENT] = 'Neutral'

def get_opinion_agreement(component, review1, review2):
    # note: this is stricter than the other similar ones
    if review1[OPINION] and review2[OPINION]:
        component[OPINION] = True
    else:
        component[OPINION] = False         

def get_attribution_agreement(component, review1, review2):
    if review1[GEN_ATTR] or review2[GEN_ATTR]:
        component[GEN_ATTR] = True
    else:
        component[GEN_ATTR] = False

def get_quote_agreement(component, review1, review2):
    if review1[QUOTE] or review2[QUOTE]:
        component[QUOTE] = True
    else:
        component[QUOTE] = False
        
def get_non_neutral_agreement(component, review1, review2):
    if review1[NON_NEUT] or review2[NON_NEUT]:
        component[NON_NEUT] = True
    else:
        component[NON_NEUT] = False

def get_subj_obj_agreement(component, review1, review2):
    if review1[SUBJ_OBJ] == review2[SUBJ_OBJ]:
        component[SUBJ_OBJ] = review1[SUBJ_OBJ]
    else:
        component[SUBJ_OBJ] = 'Neither'

def get_pers_man_agreement(component, review1, review2):
    if review1[PERS_MAN] == review2[PERS_MAN]:
        component[PERS_MAN] = review1[PERS_MAN]
    elif review1[PERS_MAN] in ['Manipulative', 'Persuasive'] and review2[PERS_MAN] in ['Manipulative', 'Persuasive']:
        component[PERS_MAN] = 'Persuasive'
    else:
        component[PERS_MAN] = 'Neither'

def create_master_dict(reviews):
    master_reviews = {}
    for article_id, article_review in reviews.items():
        if not len(article_review):
            continue
        master_reviews[article_id] = {}
        for component_id, component_review in article_review.items():
            component_master = master_reviews[article_id][component_id] = {}
            if len(component_review) == 1: # only one reviewer - just take their review as master
                component_master.update(copy.deepcopy(list(component_review.values())[0]))
            elif len(component_review) == 2: # only know how to deal with 2 reviews right now
                review1 = list(component_review.values())[0]
                review2 = list(component_review.values())[1]

                component_master[ID] = component_id
                get_na_agreement(component_master, review1, review2)
                if component_master[NA]:
                    continue # if n/a, then there is no more data to look at

                get_emo_agreement(component_master, review1, review2)
                get_sent_agreement(component_master, review1, review2)
                get_opinion_agreement(component_master, review1, review2)
                get_attribution_agreement(component_master, review1, review2)
                get_quote_agreement(component_master, review1, review2)
                get_non_neutral_agreement(component_master, review1, review2)
                get_subj_obj_agreement(component_master, review1, review2)
                get_pers_man_agreement(component_master, review1, review2)

            if not component_master[NA]:
                if component_master[PERS_MAN] in ['Manipulative', 'Persuasive']:
                    component_master[NEI_PERS_MAN] = 'Manipulative or Persuasive'
                else:
                    component_master[NEI_PERS_MAN] = 'Neither'

                if component_master[PERS_MAN] in ['Neither', 'Persuasive']:
                    component_master[PERS_NEI_MAN] = 'Neither or Persuasive'
                else:
                    component_master[PERS_NEI_MAN] = 'Manipulative'
                    
    return master_reviews

def json_data_to_csv(json_path, output_path, type_re=SENTENCE_RE):
    data = mph.read_json(json_path)
    data_to_csv(data, type_re, output_path)

def data_to_csv(data, type_re, file_path):
    # type_re is the regex for sentence, article, paragraph
    review_array = []
    for review_id, review in data.items():
        for content_id, content in review.items():
            if not type_re.match(content_id):
                continue
            if NA in content and content[NA]:
                continue
            review = []
            for key in CSV_KEYS:
                if key == ID:
                    review.append(review_id + content[key])
                else:
                    review.append(content[key])
            review_array.append(review)

    with open(file_path, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for review in review_array:
            writer.writerow(review)
                

def add_people_stats(people_stats, name1, name2, does_agree):
    if not people_stats:
        return
    
    if name1 not in people_stats:
        people_stats[name1] = {'agree': 0, 'disagree': 0, 'versus': []}
    if name2 not in people_stats:
        people_stats[name2] = {'agree': 0, 'disagree': 0, 'versus': []}

    if name2 not in people_stats[name1]['versus']:
        people_stats[name1]['versus'].append(name2)
    if name1 not in people_stats[name2]['versus']:
        people_stats[name2]['versus'].append(name1)

    if does_agree:
        people_stats[name1]['agree'] += 1
        people_stats[name2]['agree'] += 1
    else:
        people_stats[name1]['disagree'] += 1
        people_stats[name2]['disagree'] += 1

def add_stats(total_stats):
    for name, stats in total_stats.items():
        if stats['agree'] + stats['disagree'] == 0:
            continue
        else:
            percentage = (stats['agree']/float(stats['agree'] + stats['disagree'])) * 100
            total_stats[name]['agreement_perc']=percentage

def print_stats(total_stats):
    for name, stats in total_stats.items():
        if stats['agree'] + stats['disagree'] == 0:
            print("No data")
        else:
            percentage = (stats['agree']/float(stats['agree'] + stats['disagree'])) * 100
            print(name + ": " + str(percentage) + "% agree")
    
def get_baseline_stats():
    article_stats = {NA :{'agree': 0, 'disagree': 0},
                    EMO_ALL :{'agree': 0, 'disagree': 0},
                    EMO_SOME : {'agree': 0, 'disagree': 0},
                    SENT : {'agree': 0, 'disagree': 0},
                    OPINION : {'agree': 0, 'disagree': 0},
                    GEN_ATTR : {'agree': 0, 'disagree': 0},
                    QUOTE : {'agree': 0, 'disagree': 0},
                    NON_NEUT : {'agree': 0, 'disagree': 0},
                    SUBJ_OBJ : {'agree': 0, 'disagree': 0},
                    PERS_MAN : {'agree': 0, 'disagree': 0},
                    NEI_PERS_MAN : {'agree': 0, 'disagree': 0},
                    PERS_NEI_MAN : {'agree': 0, 'disagree': 0},
                    NEI_SUBJ_OBJ : {'agree': 0, 'disagree': 0},
                    NEU_SENT : {'agree': 0, 'disagree': 0}}
    sentence_stats = copy.deepcopy(article_stats)
    paragraph_stats = copy.deepcopy(article_stats)

    return (article_stats, paragraph_stats, sentence_stats)

def get_agreement(name1, review1, name2, review2, stats, people_stats = None):
    if review1[NA] == True and review2[NA] == True:
        stats[NA]['agree'] += 1
        add_people_stats(people_stats, name1, name2, True)
        return # if NA, no other fields will be filled out
    elif review1[NA] != review2[NA]:
        stats[NA]['disagree'] += 1
        add_people_stats(people_stats, name1, name2, False)
        return # if one person did NA, then we'll get skewed results for mismatches below
    else:
        stats[NA]['agree'] += 1
        add_people_stats(people_stats, name1, name2, True)

    for item in review1.keys():
        if item not in review2:
            continue
        
        if item in [SENT, OPINION, GEN_ATTR, QUOTE, NON_NEUT, SUBJ_OBJ, PERS_MAN]:
            if review1[item] == review2[item]:
                stats[item]['agree'] += 1
                add_people_stats(people_stats, name1, name2, True)
            else:
                stats[item]['disagree'] += 1
                add_people_stats(people_stats, name1, name2, False)

        if item == EMO_1: # ignore EMO_2
            if (review1[EMO_1] == review2[EMO_1] or review1[EMO_1] == review2[EMO_2]) and (review1[EMO_2] == review2[EMO_1] or review1[EMO_2] == review2[EMO_2]):
                stats[EMO_ALL]['agree'] += 1
                add_people_stats(people_stats, name1, name2, True)
            else:
                stats[EMO_ALL]['disagree'] += 1
                add_people_stats(people_stats, name1, name2, False)

            if (review1[EMO_1] == review2[EMO_1] or review1[EMO_1] == review2[EMO_2]) or (review1[EMO_2] == review2[EMO_1] or review1[EMO_2] == review2[EMO_2]):
                stats[EMO_SOME]['agree'] += 1
                add_people_stats(people_stats, name1, name2, True)
            else:
                stats[EMO_SOME]['disagree'] += 1
                add_people_stats(people_stats, name1, name2, False)

        if item == PERS_MAN:
            if review1[PERS_MAN] == 'Neither' and review2[PERS_MAN] == 'Neither':
                stats[NEI_PERS_MAN]['agree'] += 1
                add_people_stats(people_stats, name1, name2, True)
            elif review1[PERS_MAN] != 'Neither' and review2[PERS_MAN] != 'Neither':
                stats[NEI_PERS_MAN]['agree'] += 1
                add_people_stats(people_stats, name1, name2, True)
            else:
                stats[NEI_PERS_MAN]['disagree'] += 1
                add_people_stats(people_stats, name1, name2, False)


            if review1[PERS_MAN] == 'Manipulative' and review2[PERS_MAN] == 'Manipulative':
                stats[PERS_NEI_MAN]['agree'] += 1
                add_people_stats(people_stats, name1, name2, True)
            elif review1[PERS_MAN] != 'Manipulative' and review2[PERS_MAN] != 'Manipulative':
                stats[PERS_NEI_MAN]['agree'] += 1
                add_people_stats(people_stats, name1, name2, True)
            else:
                stats[PERS_NEI_MAN]['disagree'] += 1
                add_people_stats(people_stats, name1, name2, False)

        if item == SUBJ_OBJ:
            if (review1[SUBJ_OBJ] == 'Subjective' and review2[SUBJ_OBJ] == 'Objective') or (review1[SUBJ_OBJ] == 'Objective' and review2[SUBJ_OBJ] == 'Subjective'):
                stats[NEI_SUBJ_OBJ]['disagree'] += 1
            else:
                stats[NEI_SUBJ_OBJ]['agree'] += 1

        if item == SENT:
            if (review1[SENT] == 'Positive' and review2[SENT] == 'Negative') or (review1[SENT] == 'Negative' and review2[SENT] == 'Positive'):
                stats[NEU_SENT]['disagree'] += 1
            else:
                stats[NEU_SENT]['agree'] += 1

            # Analysis of why automated not working great
            ## if review1[SENT] != review2[SENT] and review1[SENT] != 'Neutral' and review2[SENT] != 'Neutral':
            ##     print(review1[ID])
            ##     print(name2)
            ##     print("review1: " + review1[SENT] + '\t   review2: ' + review2[SENT])
            ##     mph.print_json(review1['old']['emotions_counting_negation'])
            ##     mph.print_json(review1['old']['sentiments_counting_negation'])
            ##     if 'sentence' in review1['old']:
            ##         mph.print_json(review1['old']['sentence'])
            ##     print()

def get_agreement_statistics_with_other(reviews, other, output, has_reviewers=True):
    article_stats, paragraph_stats, sentence_stats = get_baseline_stats()

    for article_review_id, article_review in reviews.items():
        if article_review:
            for content_review_id, content_reviews in article_review.items():
                if len(content_reviews) < 2:
                    # there's only one reviewer so we don't care about stats
                    break
                
                if SENTENCE_RE.match(content_review_id):
                    stats = sentence_stats
                elif PARAGRAPH_RE.match(content_review_id):
                    stats = paragraph_stats
                elif ARTICLE_RE.match(content_review_id):
                    stats = article_stats
                else:
                    continue

                if has_reviewers:
                    for name, review in content_reviews.items():
                        if content_review_id in other[article_review_id]:
                            get_agreement('other1', other[article_review_id][content_review_id], name, review, stats)
                else:
                    if content_review_id in other[article_review_id]:
                        get_agreement('other1', other[article_review_id][content_review_id], 'other2', content_reviews, stats)
                    
    print("Article:")
    add_stats(article_stats)
    print_stats(article_stats)
    print()
    print("Paragraph:")
    add_stats(paragraph_stats)
    print_stats(paragraph_stats)
    print()
    print("Sentence:")
    add_stats(sentence_stats)
    print_stats(sentence_stats)

    agreement_stats = {}
    agreement_stats['article'] = article_stats
    agreement_stats['paragraph'] = paragraph_stats
    agreement_stats['sentence'] = sentence_stats

    mph.write_json(agreement_stats, output)

            
def get_agreement_statistics(reviews, output='articles/review_agreement_stats.json'):
    article_stats, paragraph_stats, sentence_stats = get_baseline_stats()
    
    for article_review_id, article_review in reviews.items():
        if article_review:
            for content_review_id, content_reviews in article_review.items():
                if len(content_reviews) != 2:
                    # there's only one reviewer so we don't care about stats
                    # if there's more than one reviewer, we don't really know how to deal with that
                    break
                else:
                    reviewer1 = list(content_reviews.values())[0]
                    reviewer2 = list(content_reviews.values())[1]
                    name1 = list(content_reviews.keys())[0]
                    name2 = list(content_reviews.keys())[1]
                
                if SENTENCE_RE.match(content_review_id):
                    stats = sentence_stats
                elif PARAGRAPH_RE.match(content_review_id):
                    stats = paragraph_stats
                elif ARTICLE_RE.match(content_review_id):
                    stats = article_stats
                else:
                    continue

                get_agreement(name1, reviewer1, name2, reviewer2, stats)

    print("Article:")
    add_stats(article_stats)
    print_stats(article_stats)
    print()
    print("Paragraph:")
    add_stats(paragraph_stats)
    print_stats(paragraph_stats)
    print()
    print("Sentence:")
    add_stats(sentence_stats)
    print_stats(sentence_stats)
    
    agreement_stats = {}
    agreement_stats['article'] = article_stats
    agreement_stats['paragraph'] = paragraph_stats
    agreement_stats['sentence'] = sentence_stats

    mph.write_json(agreement_stats, output)


################################################################################
## OTHER
################################################################################


def see_reviews():
    reviews = mph.read_json('articles/reviews.json')
    non_reviewers = mph.read_json('articles/non_reviewers.json')

    for key1, value1 in reviews.items():
        print(key1)
        if len(value1.values()) > 0:
            for key2, value2 in list(value1.values())[0].items():
                print("\t" + key2)


    print()
    print(json.dumps(non_reviewers, indent=2, separators=(',', ': ')))

def get_reviewer_agreement_statistics(review_path='articles/reviews.json', output='articles/review_agreement_stats.json'):
    reviews = mph.read_json(review_path)
    get_agreement_statistics(reviews, output)

def get_other_agreement_statistics(other_file_path, output, review_path='articles/reviews.json', has_reviewers=True):
    reviews = mph.read_json(review_path)
    other = mph.read_json(other_file_path)
    
    get_agreement_statistics_with_other(reviews, other, output, has_reviewers)

def create_master(review_path='articles/reviews.json', output_json='articles/master_reviews.json', output_csv='articles/master_reviews.csv'):
    reviews = mph.read_json(review_path)
    master_dict = create_master_dict(reviews)
    mph.write_json(master_dict, output_json)
    data_to_csv(master_dict, SENTENCE_RE, output_csv)
    
def main():
    get_article_reviews('articles/test_articles.json', 'articles/reviews.json', 'articles/non_reviewers.json')
    
    ## test_articles_info = {'asdf':{"file_path":"articles/immigration/judge-immigration-agents-suing-obama-can-move-forward.txt",
    ##                               "id":'asdf',
    ##                               "reviewers":[{"name":"Dawn Stapleton"}, {"name":"Clare Hurley"}]}}
    ## get_article_reviews(test_articles_info, 'articles/reviews2.json', 'articles/non_reviewers2.json')
    
    ## article_info = {"file_path":"articles/immigration/judge-immigration-agents-suing-obama-can-move-forward.txt"}
    ## reviewer_info = {"name":"Dawn Stapleton"}
    ## print(get_article_review(article_info, reviewer_info))

    ## article_info = {"file_path":"articles/stock/delaware-quarterback-joe-flacco-stock-rising-in-nfl-draft.txt"}
    ## reviewer_info = {"name":"Mandi Swanson"}
    ## print(get_article_review(article_info, reviewer_info))
    
if __name__ == '__main__':
    #main()
    #get_reviewer_agreement_statistics()
    #create_master()
    #see_reviews()
    #get_other_agreement_statistics('articles/master_reviews.json')
    get_other_agreement_statistics('baseline_match/test_articles.json')

