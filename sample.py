# -*- encoding:utf-8 -*-
import time
import math
import sys
import argparse
import cPickle as pickle
import codecs

import numpy as np
from chainer import cuda, Variable, FunctionSet
import chainer.functions as F
from CharRNN import CharRNN, make_initial_state

sys.stdout = codecs.getwriter('utf_8')(sys.stdout)

def convertDegreeRepresentation(chord):
    if chord.find("10") != -1 or chord.find("11") != -1:
        degree = chord[:2]
        chordType = chord[2:]
    else:
        degree = chord[0]
        chordType = chord[1:]

    degree = degree.replace("0","Ⅰ")
    degree = degree.replace("1","Ⅰ #/Ⅱ ♭")
    degree = degree.replace("2","Ⅱ")
    degree = degree.replace("3","Ⅱ #/Ⅲ ♭")
    degree = degree.replace("4","Ⅲ")
    degree = degree.replace("5","Ⅳ")
    degree = degree.replace("6","Ⅳ #/Ⅴ ♭")
    degree = degree.replace("7","Ⅴ")
    degree = degree.replace("8","Ⅴ #/Ⅵ ♭")
    degree = degree.replace("9","Ⅵ")
    degree = degree.replace("10","Ⅵ #/Ⅶ ♭")
    degree = degree.replace("11","Ⅶ")

    res = degree.decode("utf-8") + " ".decode("utf-8") + chordType.decode("utf-8")
    return res






#%% arguments
parser = argparse.ArgumentParser()

parser.add_argument('--model',      type=str,   required=True)
parser.add_argument('--vocabulary', type=str,   required=True)

parser.add_argument('--seed',       type=int,   default=123)
parser.add_argument('--sample',     type=int,   default=1)
parser.add_argument('--primetext',  type=str,   default='')
parser.add_argument('--length',     type=int,   default=2000)
parser.add_argument('--gpu',        type=int,   default=-1)

args = parser.parse_args()

np.random.seed(args.seed)

# load vocabulary
vocab = pickle.load(open(args.vocabulary, 'rb'))
ivocab = {}
for c, i in vocab.items():
    ivocab[i] = c

# load model
model = pickle.load(open(args.model, 'rb'))
n_units = model.embed.W.data.shape[1]

if args.gpu >= 0:
    cuda.get_device(args.gpu).use()
    model.to_gpu()

# initialize generator
state = make_initial_state(n_units, batchsize=1, train=False)
if args.gpu >= 0:
    for key, value in state.items():
        value.data = cuda.to_gpu(value.data)


if args.gpu >= 0:
    prev_char = cuda.to_gpu(prev_char)

if len(args.primetext) > 0:
    #for i in unicode(args.primetext, 'utf-8'):
    words = args.primetext.split(" ")
    for word in words:
        word = word.replace("\n","")
        sys.stdout.write("input word : " + convertDegreeRepresentation(word) + "\n")
        prev_char = np.ones((1,), dtype=np.int32) * vocab[word]
        if args.gpu >= 0:
            prev_char = cuda.to_gpu(prev_char)

        state, prob = model.forward_one_step(prev_char, prev_char, state, train=False)

sys.stdout.write("----- sampling result -----\n")

for i in xrange(args.length):
    state, prob = model.forward_one_step(prev_char, prev_char, state, train=False)

    if args.sample > 0:
        probability = cuda.to_cpu(prob.data)[0].astype(np.float64)
        probability /= np.sum(probability)
        index = np.random.choice(range(len(probability)), p=probability)
    else:
        index = np.argmax(cuda.to_cpu(prob.data))
    #sys.stdout.write(convertDegreeRepresentation(ivocab[index]) + "\n")
    print convertDegreeRepresentation(ivocab[index]) + "\n"

    prev_char = np.array([index], dtype=np.int32)
    if args.gpu >= 0:
        prev_char = cuda.to_gpu(prev_char)

print
