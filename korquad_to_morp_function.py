# 기존의 KorQuAD 데이터를 KorBERT 입력에 맞추기 위해 변환

from __future__ import absolute_import

import argparse
import json
from pprint import pprint
from sentence_splitter import SentenceSplitter, split_text_into_sentences
from komoran3py_master.komoran3py import KomoranPy

class KorquadToMorpFunction():

    def __init__(self, input_file):
        self.input_file = input_file

    def find_substring(self, sub, orig):
        pos_list = []
        sub_len = len(sub)
        for i in range(len(orig) - sub_len + 1):
            if orig[i:i+sub_len] == sub:
                pos_list.append(i)
        return pos_list

    def convert(self):
        
        read_file_dir = self.input_file
        
        file_directory = read_file_dir
        read_data=open(file_directory, encoding='utf-8').read()
        json_data = json.loads(read_data)
        
        komoran = KomoranPy()
        splitter = SentenceSplitter(language='en')

        splits = 0
        
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

                    sent_pos_orig = komoran.pos(context, position=True)
                    tokens_dict_tmp = [{'token_text':word, 'token':str(word+'/'+pos), 'pos':(start, end), 'orig':context[start: end]} \
                                   for (word, pos, start, end) in sent_pos_orig]

                    tokens_dict = []

                    for token in tokens_dict_tmp:
                        token_text = token['token_text'].strip()
                        token_text_list = token_text.split()
                        if len(token_text_list) == 1:
                            tokens_dict.append(token)
                            continue
                        else:
                            tag = token['token'].split('/')[-1]
                            for t in token_text_list:
                                tokens_dict.append({'token_text':t, 'token':str(t+'/'+tag), 'orig':t})
                    
                    # #JW) Check whether tokens are split                    
                    # if len(tokens_dict_tmp) != len(tokens_dict):
                    #     splits += 1
                    #     print(splits, "SPLIT!", len(tokens_dict) - len(tokens_dict_tmp))

                    p_morp_list = [elem['token'] for elem in tokens_dict]


                    orig_list = [token['orig'] for token in tokens_dict]
                    pos_list = []
                    pos = 0
                    context_encoded = context.encode()

                    for token_orig in orig_list:
                        token_encoded = token_orig.encode()
                        idxs = self.find_substring(token_encoded, context_encoded)
                        for idx in idxs:
                            if idx >= pos:
                                pos = idx
                                pos_list.append(pos)
                                break

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


                    data_dict = dict()
                    data_dict['id'] = uid
                    data_dict['passage'] = passage
                    data_dict['question'] = question
                    data_list.append(data_dict)
        

        return data_list            

        
