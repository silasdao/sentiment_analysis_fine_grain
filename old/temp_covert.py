# -*- coding: utf-8 -*-
import json
import random

dict_unique={}

dict_type_ignore_count={'train':0,'valid':0,'test':0}
def transform_data_to_fasttext_format(file_path,target_path,data_type):
    with open(file_path,'r') as file_object:
        with open(target_path,'w') as target_object:
            lines=file_object.readlines()
            print("length of lines:",len(lines))
            random.shuffle(lines)
            for i,line in enumerate(lines):
                json_string=json.loads(line)
                accusation_list=json_string['meta']['accusation']
                fact=json_string['fact'].strip('\n\r').replace("\n","").replace("\r","")
                unique_value=dict_unique.get(fact,None)
                if unique_value is None: # if not exist, put to unique dict, then process
                    dict_unique[fact] = fact
                else: # otherwise, ignore
                    print("going to ignore.",data_type,fact)
                    dict_type_ignore_count[data_type]=dict_type_ignore_count[data_type]+1
                    continue
                length_accusation=len(accusation_list)
                accusation_strings = ''.join(
                    f' __label__{accusation}' for accusation in accusation_list
                )
                target_object.write(fact+accusation_strings+"\n")
    print("dict_type_ignore_count:",dict_type_ignore_count[data_type])

file_path='./data/cail2018/data_valid_checked.json'
target_path='./data/data_valid2.txt'
transform_data_to_fasttext_format(file_path,target_path,'valid')

file_path='./data/cail2018/data_test.json'
target_path='./data/data_test2.txt'
transform_data_to_fasttext_format(file_path,target_path,'test')

file_path='./data/cail2018/cail2018_big_downsmapled.json'
target_path='./data/data_train2.txt'
transform_data_to_fasttext_format(file_path,target_path,'train')

