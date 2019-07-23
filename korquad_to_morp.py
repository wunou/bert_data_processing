# 기존의 KorQuAD 데이터를 KorBERT 입력에 맞추기 위해 변환

from __future__ import absolute_import

import argparse
import json
from pprint import pprint
from sentence_splitter import SentenceSplitter, split_text_into_sentences
from komoran3py_master.komoran3py import KomoranPy

def find_substring(sub, orig):
    pos_list = []
    sub_len = len(sub)
    for i in range(len(orig) - sub_len + 1):
        if orig[i:i+sub_len] == sub:
            pos_list.append(i)
    return pos_list

def main():
    parser = argparse.ArgumentParser(description='Argument parser for tokenizing korquad data in morphological way')
    parser.add_argument('input_file', type=str,
            help='Directory and name of the input file.')
    parser.add_argument('output_file', type=str,
            help='Directory and name of the output file.')
    args = parser.parse_args()
    
    read_file_dir = args.input_file
    
    file_directory = read_file_dir
    read_data=open(file_directory, encoding='utf-8').read()
    json_data = json.loads(read_data)
    
    komoran = KomoranPy()
    splitter = SentenceSplitter(language='en')

    MARKER = '✿'
    error = False


    answer_not_found = 0
    wrong_tokenize = 0

    data_list = []
    for data in json_data['data']:
        paragraphs = data['paragraphs']    

        for paragraph in paragraphs:
            context = paragraph['context']

            p_sent_text_list = splitter.split(context)
            p_sent_word_list = []
            sent_start = 0
            for sent in p_sent_text_list:
                words_num = len(sent.split())
                p_sent_word_list.append([sent_start, sent_start + words_num - 1])
                sent_start = words_num

            qas = paragraph['qas']
            for qa in qas:
                uid = qa['id']
                question = qa['question']
                answers = qa['answers']
                answer_text = answers[0]['text']
                answer_start = answers[0]['answer_start']
                answer_end = answer_start + len(answer_text)

                try:
                    q_morp_list = komoran.pos(question)
                except:
                    question = question.replace('\n', '')
                    q_morp_list = komoran.pos(question)
                q_morp_list = ['/'.join(morp) for morp in q_morp_list]

                q_sent_text_list = splitter.split(question)
                q_sent_word_list = []
                words_num = len(question.split())
                q_sent_word_list = [0, words_num]
                q_text = str(question)

                # context에 MARKER 추가
    #             context_marked = context[:answer_start] +\
    #                              MARKER + answer_text + MARKER + \
    #                              context[answer_end:]            
                # MARKER 양 옆에 공백 추가하여 형태소 분석 시 MARKER가 분리되지 않는 상황을 방지

                context_marked = context[:answer_start] +\
                                MARKER + ' ' + answer_text + ' ' + MARKER + \
                                 context[answer_end:]
                context_marked = context_marked.lstrip()

                sent_pos_orig = komoran.pos(context_marked, position=True)
                tokens_dict = [{'token_text':word, 'token':str(word+'/'+pos), 'pos':(start, end), 'orig':context_marked[start: end]} \
                               for (word, pos, start, end) in sent_pos_orig]

                p_morp_list = [elem['token'] for elem in tokens_dict]
                marker_position = [i for i,val in enumerate(p_morp_list) if val == MARKER+'/SW']
                try:
                    begin_morp = marker_position[0]
                    end_morp = marker_position[1] - 2
                except IndexError:
                    answer_not_found += 1
                    print('Answer NOT found!', answer_not_found)
                    continue

                marker_index = [index for index, morp in enumerate(p_morp_list) if morp == MARKER+'/SW']
                if len(marker_index) != 2:
                    print("MARKER tokenized NOT correctly")
                    continue
                else:
                    del p_morp_list[marker_index[1]]
                    del p_morp_list[marker_index[0]]
                    del tokens_dict[marker_index[1]]
                    del tokens_dict[marker_index[0]]

                orig_list = [token['orig'] for token in tokens_dict]
                pos_list = []
                pos = 0
                context_encoded = context.encode()

                for token_orig in orig_list:
                    token_encoded = token_orig.encode()
                    idxs = find_substring(token_encoded, context_encoded)
                    for idx in idxs:
                        if idx >= pos:
                            pos = idx
                            pos_list.append(pos)
                            break

                if len(orig_list) != len(pos_list):
                    print("Wrong morphological tokenized!", wrong_tokenize)
                    wrong_tokenize += 1
                    continue

                passage = dict()
                passage['morp_list'] = p_morp_list
                passage['position_list'] = pos_list
                passage['sent_text_list'] = p_sent_text_list
                passage['sent_word_list'] = p_sent_word_list
                passage['text'] = context

                question = dict()
                question['morp_list'] = q_morp_list
                question['sent_text_list'] = q_sent_text_list
                question['sent_word_list'] = q_sent_word_list
                question['text'] = q_text

                answer = dict()
                answer['text'] = answer_text
                answer['begin_morp'] = begin_morp
                answer['end_morp'] = end_morp

                data_dict = dict()
                data_dict['id'] = uid
                data_dict['passage'] = passage
                data_dict['question'] = question
                data_dict['answer'] = answer
                data_list.append(data_dict)
                
    print("Number of PQA set after tokenizing:", len(data_list))
    with open(args.output_file, "w") as write_file:
        json.dump(json_data, write_file)
        
        
if __name__=="__main__":
    main()
    
    
    
