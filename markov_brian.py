import pprint
import re
import random
import time
import json
from pprint import pprint


class MarkovProcessor:

  def debugPrint(self, s):
    if self.debug: print(s)

  def debugPPrint(self, title, obj):
    if self.debug:
      pprint(obj)

  def __init__(self):
    self.debug = False
    self.separators = {
      '.': '\\.',
      ',': '\\,',
      '?': '\\?',
      '!': '\\!'
    }
    self.tokensWithoutSpacesBefore = ['.', ',', '?', '!', '\n']
    self._newSection()

    # self.chainsByLength
    self.chainsByLength = {}
    self.MAX_LENGTH = 5
    for i in range(1, self.MAX_LENGTH+1):
      self.chainsByLength[i] = {}
    pass

  def _newSection(self):
    self.lastTokens = []
    self.lastToken = ''

  def processToken(self, token):
    self._incrChains(token)
    self._storeTokenInLastTokens(token)

  def _storeTokenInLastTokens(self, token):
    self.lastTokens.insert(0, token)
    self.lastTokens = self.lastTokens[0:self.MAX_LENGTH]

  def _incrChains(self, token):
    # token = "love"
    # MAX_LENGTH = 4
    # self.chainsByLength = {
    # 1: {'How': 1, 'do': 1, 'I': 1}
    # 2: {'How': {'do': 1}, 'do': {'I': 1}}
    # 3: {'How': {'do': {'I': 1}
    # 4: 
    # } 
    # self.lastTokens = ['I', 'do', 'How']

    path = []

    for length, chain_root in self.chainsByLength.items():
      if length == 1:
        self._incrToken(chain_root, token)
      else:
        path = []
        # length = 2
        # path = ['I']

        # length = 3
        # path = ['do', 'I']
        if len(self.lastTokens) + 1 < length: 
          continue

        path = self.lastTokens[0:length - 1]
        path.reverse()

        node = chain_root
        for p in path:
          self._ensureExists(node, p, {})
          node = node[p]
        self._incrToken(node, token)

  def _incrToken(self, d, k):
    self._ensureExists(d, k, 0)
    d[k] = d[k] + 1
     
  def _ensureExists(self, d, k, default):
    if k not in d:
      d[k] = default

  def processFile(self, fn):
    print('Processing file')
    TTL = 5000000
    with open(fn, 'r') as f:
      for line in f:
        line = line.strip()
        if re.match('\\d+', line):
          self._newSection()
          continue
        for c, r in self.separators.items():
          line = re.sub(r, ' %s ' % (c), line)
        line = line.strip()
        words = re.split('\\s+', line)
        for word in words:
          self.processToken(word)
          #self.printModel()
          #input('')
          TTL -= 1
          if TTL < 0: return
        self.processToken("\n")

  def saveModel(self, fn):
    print('SAVING: %s' % fn)
    f = open(fn, 'w', encoding="utf-8")
    json.dump(self.chainsByLength, f)
    f.close()

  def loadModel(self, fn):
    print('LOADING: %s' % fn)
    f = open(fn, 'r', encoding="utf-8")
    self.chainsByLength = json.load(f)
    for k in list(self.chainsByLength.keys()):
      s = str(k)
      i = int(k)
      if s in self.chainsByLength:
        self.chainsByLength[i] = self.chainsByLength[s]
        del self.chainsByLength[s]
    f.close()

  def _indent(self, n):
    for i in range(0, n):
      print('... ', end="")
    

  def printModel(self):
    for length, chain_root in self.chainsByLength.items():
      print('%d: ' % (length))
      pprint(chain_root)

  def printTopCandidates(self, frequency_dict):
    pprint(frequency_dict)
    input('')

  def randomWord(self, frequency_dict = None):
    if not frequency_dict:
      frequency_dict = self.chainsByLength[1]
    candidates = []
    weights = []
    for token, frequency in frequency_dict.items():
      candidates.append(token) 
      weights.append(frequency)
    self.printTopCandidates(frequency_dict)
    choices = random.choices(candidates, weights = weights, k = 1)
    token = choices[0]
    return token

  def generateNextWord(self, previous_tokens):
    self.debugPPrint('previous_tokens', previous_tokens)
    # if the last two charactesr are whitespaces:
    if len(previous_tokens) > 3 and \
      re.match('\\W\\W\\W', ''.join(previous_tokens[-3:])):
      self.debugPrint('double whitespace!')
      return self.randomWord()

    # previous_tokens: ['How', 'do', 'I']

    # we have to figure out the right chain to use (ie, the length of the chain we need)
    # the length should be the length of the previous tokens.

    length = len(previous_tokens)
    chain_length = length + 1
    chain_length = min(chain_length, self.MAX_LENGTH)
    if chain_length <= len(previous_tokens):
      previous_tokens = previous_tokens[(-1*chain_length + 1):]
   
    self.debugPPrint('previous_tokens', previous_tokens)
    while chain_length > 0:
      self.debugPrint('Looking for chains of length %d' % (chain_length))
      if chain_length not in self.chainsByLength: 
        self.debugPrint('do NOT have chains of length %d' % (chain_length))
        chain_length = chain_length - 1
        previous_tokens.pop(0)
        continue
      word = self.randomWordFromChainWithLengthAndStartingWith(chain_length, previous_tokens)
      if word == None:

        self.debugPPrint(
          'Could not find match in chains of length %d for:' % (chain_length),
          previous_tokens)

        chain_length = chain_length - 1
        previous_tokens = previous_tokens.copy()
        previous_tokens.pop(0)
        self.debugPPrint(
          'Changing previous_tokens. Now previous tokens is:',
          previous_tokens)
        continue
      return word
    self.debugPrint('could not find match')
    return self.randomWord()

  def randomWordFromChainWithLengthAndStartingWith(self, chain_length, previous_tokens):
    chain_root = self.chainsByLength[chain_length]
    node = chain_root
    
    for token in previous_tokens:
      if token not in node:
        return None
      node = node[token]

    if type(node) == type({}):
      length = len(node.keys())
      self.debugPrint('frequency_dict: (length: %d)' % (length))
      if length < 10:
        self.debugPPrint('node', node)
      else:
        self.debugPrint('node too big to print')
      return self.randomWord(node)
    return None

  def printTokens(self, tokens):
    i = 0
    for token in tokens:
      last_token = None
      if i > 0: last_token = tokens[i-1]
      next_token = None
      if i < len(tokens) - 1: next_token = tokens[i+1]
      if token not in self.tokensWithoutSpacesBefore:
        print(' ', end='')
      print(token, end="")
      i = i + 1
    print('')
  

processor = MarkovProcessor()
fn = 't8.shakespeare2.txt'
fn = 'akjv.filtered.txt'
processor.processFile(fn)
#processor.saveModel('./t8.shakespeare.model.txt')
processor.saveModel('./akjv.json')


exit();
processor.loadModel('./t8.shakespeare.model.txt')
s = ''
previous_words = ['How']
while s.strip() != 'q':
  processor.debugPPrint('Generating next word from:',
    previous_words)
  word = processor.generateNextWord(previous_words)
  previous_words.append(word)
  processor.printTokens(previous_words)
  s = input('')
exit()



