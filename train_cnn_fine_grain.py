# -*- coding: utf-8 -*-
#process--->1.load data(X:list of lint,y:int). 2.create session. 3.feed data. 4.training (5.validation) ,(6.prediction)
"""
 BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
 main idea:  based on multiple layer self-attention model(encoder of Transformer), pretrain two tasks( masked language model and next sentence prediction task)
             on large scale of corpus, then fine-tuning by add a single classification layer.

train the model(transformer) with data enhanced by pre-training of two tasks.
default hyperparameter is d_model=512,h=8,d_k=d_v=64(big). if you have a small data set or want to train a
small model, use d_model=128,h=8,d_k=d_v=16(small), or d_model=64,h=8,d_k=d_v=8(tiny).
"""

import tensorflow as tf
#import numpy as np
#from model.bert_model import BertModel # TODO TODO TODO test whether pretrain can boost perofrmance with other model
from model.bert_cnn_fine_grain_model import BertCNNFineGrainModel as BertModel

from data_util_hdf5 import assign_pretrained_word_embedding,set_config,create_or_load_vocabulary
import os
import pickle
from evaluation_matrix import *
#from model.config_transformer import Config
#configuration
FLAGS=tf.app.flags.FLAGS

tf.app.flags.DEFINE_string("data_path","./data/","path of traning data.")
tf.app.flags.DEFINE_string("training_data_file","./data/bert_train2.txt","path of traning data.") #./data/cail2018_bi.json
tf.app.flags.DEFINE_string("valid_data_file","./data/bert_valid2.txt","path of validation data.")
tf.app.flags.DEFINE_string("test_data_file","./data/bert_test2.txt","path of validation data.")
tf.app.flags.DEFINE_string("ckpt_dir","./checkpoint_lm/","checkpoint location for the model for restore from pre-train") #save to here, so make it easy to upload for test
tf.app.flags.DEFINE_string("ckpt_dir_save","./checkpoint_lm_save/","checkpoint location for the model for save fine-tuning") #save to here, so make it easy to upload for test

tf.app.flags.DEFINE_string("tokenize_style","word","checkpoint location for the model")
tf.app.flags.DEFINE_string("model_name","","text cnn model. pre-train and fine-tuning.") # BertCNNFineGrainModel

tf.app.flags.DEFINE_integer("vocab_size",70000,"maximum vocab size.")
tf.app.flags.DEFINE_float("learning_rate",0.001,"learning rate") #0.001
tf.app.flags.DEFINE_integer("batch_size", 64, "Batch size for training/evaluating.") # 32-->128
tf.app.flags.DEFINE_integer("decay_steps", 10000, "how many steps before decay learning rate.") # 32-->128
tf.app.flags.DEFINE_float("decay_rate", 0.8, "Rate of decay for learning rate.") #0.65
tf.app.flags.DEFINE_float("dropout_keep_prob", 0.9, "percentage to keep when using dropout.") #0.65
tf.app.flags.DEFINE_integer("sequence_length",400,"max sentence length")#400
tf.app.flags.DEFINE_integer("sequence_length_lm",10,"max sentence length for masked language model")

tf.app.flags.DEFINE_boolean("is_training",True,"is training.true:tranining,false:testing/inference")
tf.app.flags.DEFINE_boolean("is_fine_tuning",True,"is_finetuning.ture:this is fine-tuning stage")

tf.app.flags.DEFINE_integer("num_epochs",35,"number of epochs to run.")
tf.app.flags.DEFINE_integer("process_num",35,"number of cpu used")

tf.app.flags.DEFINE_integer("validate_every", 1, "Validate every validate_every epochs.") #
tf.app.flags.DEFINE_boolean("use_pretrained_embedding",False,"whether to use embedding or not.")#
tf.app.flags.DEFINE_string("word2vec_model_path","./data/Tencent_AILab_ChineseEmbedding_100w.txt","word2vec's vocabulary and vectors") # data/sgns.target.word-word.dynwin5.thr10.neg5.dim300.iter5--->data/news_12g_baidubaike_20g_novel_90g_embedding_64.bin--->sgns.merge.char
tf.app.flags.DEFINE_boolean("test_mode",False,"whether it is test mode. if it is test mode, only small percentage of data will be used. test mode for test purpose.")

tf.app.flags.DEFINE_integer("d_model", 128, "dimension of model") # 128-->200
tf.app.flags.DEFINE_integer("num_layer", 6, "number of layer")
tf.app.flags.DEFINE_integer("num_header", 8, "number of header")
tf.app.flags.DEFINE_integer("d_k", 16, "dimension of k") # 64-->16
tf.app.flags.DEFINE_integer("d_v", 16, "dimension of v") # 64-->16

tf.app.flags.DEFINE_string("cache_file","./preprocess_word/train_valid_test_vocab_cache.pik","cache file that contains train/valid/test data and vocab of words and label2index")

def main(_):
    # 1.load vocabulary of token from cache file save from pre-trained stage; load label dict from training file; print some message.
    vocab_word2index, _= create_or_load_vocabulary(FLAGS.data_path,FLAGS.training_data_file,FLAGS.vocab_size,test_mode=FLAGS.test_mode,tokenize_style=FLAGS.tokenize_style,model_name=FLAGS.model_name)
    #label2index=get_lable2index(FLAGS.data_path,FLAGS.training_data_file, tokenize_style=FLAGS.tokenize_style)
    #vocab_size = len(vocab_word2index);print("cnn_model.vocab_size:",vocab_size);num_classes=len(label2index);print("num_classes:",num_classes)
    #  load training data.
    #train,valid, test= load_data_multilabel(FLAGS.data_path,FLAGS.training_data_file,FLAGS.valid_data_file,FLAGS.test_data_file,vocab_word2index,label2index,FLAGS.sequence_length,
    #                                        process_num=FLAGS.process_num,test_mode=FLAGS.test_mode,tokenize_style=FLAGS.tokenize_style)
    #train_X, train_Y= train
    #valid_X, valid_Y= valid
    #test_X,test_Y = test
    if not os.path.exists(FLAGS.cache_file):
        print("cache file is missing. please generate it though step by step with preprocess_word.ipynb")
        return
    train_X, train_Y, valid_X, valid_Y, test_X, label2index=None,None,None,None,None,None

    with open(FLAGS.cache_file, 'rb') as data_f:
        train_X, train_Y, valid_X, valid_Y, test_X,_, label2index=pickle.load(data_f)
    valid=(valid_X, valid_Y)
    data_f.close()
    num_classes=len(label2index)
    vocab_size=len(vocab_word2index)
    FLAGS.sequence_length=train_X.shape[1] #
    print("test_model:",FLAGS.test_mode,";length of training data:",train_X.shape,";valid data:",valid_X.shape,";test data:",test_X.shape,";train_Y:",train_Y.shape)
    # 2.create session.
    gpu_config=tf.ConfigProto()
    gpu_config.gpu_options.allow_growth=True
    with tf.Session(config=gpu_config) as sess:
        #Instantiate Model
        config=set_config(FLAGS,num_classes,vocab_size)
        model=BertModel(config)
        #Initialize Save
        saver=tf.train.Saver()
        if os.path.exists(f"{FLAGS.ckpt_dir}checkpoint"):
            print("Restoring Variables from Checkpoint.")
            sess.run(tf.global_variables_initializer())
            for i in range(6): #decay learning rate if necessary.
                print(
                    i,
                    f"Going to decay learning rate by a factor of {str(FLAGS.decay_rate)}",
                )
                sess.run(model.learning_rate_decay_half_op)
            # restore those variables that names and shapes exists in your model from checkpoint. for detail check: https://gist.github.com/iganichev/d2d8a0b1abc6b15d4a07de83171163d4
            optimistic_restore(sess, tf.train.latest_checkpoint(FLAGS.ckpt_dir)) #saver.restore(sess,tf.train.latest_checkpoint(FLAGS.ckpt_dir))
        else:
            print('Initializing Variables as model instance is not exist.')
            sess.run(tf.global_variables_initializer())
            if FLAGS.use_pretrained_embedding:
                vocabulary_index2word={index:word for word,index in vocab_word2index.items()}
                assign_pretrained_word_embedding(sess, vocabulary_index2word, vocab_size,FLAGS.word2vec_model_path,model.embedding,config.d_model) # assign pretrained word embeddings
        curr_epoch=sess.run(model.epoch_step)
        # 3.feed data & training
        number_of_training_data=len(train_X)
        batch_size=FLAGS.batch_size
        iteration=0
        score_best=-100
        f1_score=0
        epoch=0
        for epoch in range(curr_epoch,FLAGS.num_epochs):
            loss_total, counter =  0.0, 0
            for start, end in zip(range(0, number_of_training_data, batch_size),range(batch_size, number_of_training_data, batch_size)):
                iteration=iteration+1
                if epoch==0 and counter==0:
                    print("trainX[start:end]:",train_X[start:end],"train_X.shape:",train_X.shape)
                feed_dict = {model.input_x: train_X[start:end],model.input_y:train_Y[start:end],model.dropout_keep_prob: FLAGS.dropout_keep_prob}
                current_loss,lr,l2_loss,_=sess.run([model.loss_val,model.learning_rate,model.l2_loss,model.train_op],feed_dict)
                loss_total,counter=loss_total+current_loss,counter+1
                if counter %30==0:
                    print("Learning rate:%.7f\tLoss:%.3f\tCurrent_loss:%.3f\tL2_loss%.3f\t"%(lr,float(loss_total)/float(counter),current_loss,l2_loss))
                if start!=0 and start%(4000*FLAGS.batch_size)==0:
                    loss_valid, f1_macro_valid, f1_micro_valid= do_eval(sess, model, valid,num_classes,label2index)
                    f1_score_valid=((f1_macro_valid+f1_micro_valid)/2.0) #*100.0
                    print("Valid.Epoch %d ValidLoss:%.3f\tF1_score_valid:%.3f\tMacro_f1:%.3f\tMicro_f1:%.3f\t" % (epoch, loss_valid, f1_score_valid, f1_macro_valid, f1_micro_valid))

                    # save model to checkpoint
                    if f1_score_valid>score_best:
                        save_path = f"{FLAGS.ckpt_dir_save}model.ckpt"
                        print("going to save check point.")
                        saver.save(sess, save_path, global_step=epoch)
                        score_best=f1_score_valid
            #epoch increment
            print("going to increment epoch counter....")
            sess.run(model.epoch_increment)

            # 4.validation
            print(epoch,FLAGS.validate_every,(epoch % FLAGS.validate_every==0))
            if epoch % FLAGS.validate_every==0:
                loss_valid,f1_macro_valid2,f1_micro_valid2=do_eval(sess,model,valid,num_classes,label2index)
                f1_score_valid2 = ((f1_macro_valid2 + f1_micro_valid2) / 2.0) #* 100.0
                print("Valid.Epoch %d ValidLoss:%.3f\tF1 score:%.3f\tMacro_f1:%.3f\tMicro_f1:%.3f\t"% (epoch,loss_valid,f1_score_valid2,f1_macro_valid2,f1_micro_valid2))
                #save model to checkpoint
                if f1_score_valid2 > score_best:
                    save_path = f"{FLAGS.ckpt_dir_save}model.ckpt"
                    print("going to save check point.")
                    saver.save(sess,save_path,global_step=epoch)
                    score_best = f1_score_valid2
            if epoch in [2, 4, 6, 9, 13]:
                for i in range(1):
                    print(i, "Going to decay learning rate by half.")
                    sess.run(model.learning_rate_decay_half_op)

        # 5.report on test set
        #loss_test, f1_macro_test, f1_micro_test=do_eval(sess, model, test,num_classes, label2index)
        #f1_score_test=((f1_macro_test + f1_micro_test) / 2.0) * 100.0
        #print("Test.Epoch %d TestLoss:%.3f\tF1_score:%.3f\tMacro_f1:%.3f\tMicro_f1:%.3f\t" % (epoch, loss_test, f1_score_test,f1_macro_test, f1_micro_test))
        print("training completed...")

          #sess,model,valid,iteration,num_classes,label2index
num_fine_grain_type=20 # 20 fine grain sentiment analysis
num_fine_grain_value=4 # 4 kinds of value: [1,0,-1,-2]
def do_eval(sess,model,valid,num_classes,label2index):
    """
    do evaluation using validation set, and report loss, and f1 score.
    :param sess:
    :param model:
    :param valid:
    :param num_classes:
    :param label2index:
    :return:
    """
    valid = valid[:64*80]
    number_examples=valid[0].shape[0]
    valid_x,valid_y=valid
    print("number_examples for valid:",number_examples)
    eval_loss,eval_counter=0.0,0
    batch_size=FLAGS.batch_size
    label_dict=init_label_dict(num_classes)
    eval_macro_f1, eval_micro_f1 = 0.0,0.0
    for start,end in zip(range(0,number_examples,batch_size),range(batch_size,number_examples,batch_size)):
        feed_dict = {model.input_x: valid_x[start:end],model.input_y:valid_y[start:end],model.dropout_keep_prob: 1.0}
        curr_eval_loss, logits= sess.run([model.loss_val,model.logits],feed_dict) # logits：[batch_size,label_size]
        #compute confuse matrix
        label_dict=compute_confuse_matrix_batch(valid_y[start:end],logits,label_dict,name='bright')
        #for aspect_index in range(num_fine_grain_type):
        #    start_sub=aspect_index*num_fine_grain_value
        #    start_end=start_sub+num_fine_grain_value
        #    valid_y_sub=valid_y[start:end][:,start_sub:start_end]
        #    logits_sub=logits[start:end][:,start_sub:start_end]
        #    label_dict=compute_confuse_matrix_batch(valid_y_sub[start:end],logits_sub,label_dict,name='bright')
        #    if start%3000==0:
        #        print("valid_y_sub:",valid_y_sub)
        #        print("logits_sub:",logits_sub)
        eval_loss=eval_loss+curr_eval_loss
        eval_counter=eval_counter+1
    #compute f1_micro & f1_macro
    f1_micro,f1_macro=compute_micro_macro(label_dict) #label_dict is a dict, key is: an label,value is: (TP,FP,FN). where TP is number of True Positive
    compute_f1_score_write_for_debug(label_dict,label2index)
    return eval_loss/float(eval_counter+small_value),f1_macro,f1_micro

def optimistic_restore(session, save_file):
  """
  restore only those variable that exists in the model
  :param session:
  :param save_file:
  :return:
  """
  reader = tf.train.NewCheckpointReader(save_file)
  saved_shapes = reader.get_variable_to_shape_map()
  var_names = sorted([(var.name, var.name.split(':')[0]) for
                      var in tf.global_variables()
                      if var.name.split(':')[0] in saved_shapes])
  restore_vars = []
  name2var = dict(zip(map(lambda x: x.name.split(':')[0],tf.global_variables()),tf.global_variables()))
  with tf.variable_scope('', reuse=True):
    for var_name, saved_var_name in var_names:
      curr_var = name2var[saved_var_name]
      var_shape = curr_var.get_shape().as_list()
      if var_shape == saved_shapes[saved_var_name]:
          #print("going to restore.var_name:",var_name,";saved_var_name:",saved_var_name)
          restore_vars.append(curr_var)
      else:
          print("variable not trained.var_name:",var_name)
  saver = tf.train.Saver(restore_vars)
  saver.restore(session, save_file)

if __name__ == "__main__":
    tf.app.run()