#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Extractor():
    def __init__(self, coref = None, sentences = None):
        self.coref = coref
        self.sentences = sentences
        self.dependencies = self.sentences['dependencies']

    def concat_noun(self, noun, dependencies):
        if noun is None:
            return None
        ret = noun

        nn = []
        poss = prep = None
        for dependency,gov,dep in dependencies:
            if gov == noun:
                if dependency == 'nn':
                    nn.append(dep)
                elif dependency == 'poss':
                    poss = dep
                # collapsed 対応
                elif 'prep' in dependency:
                    if prep is not None:
                        prep += dependency.lstrip('prep') + ' ' + dep
                    else:
                        prep = dependency.lstrip('prep') + ' ' + dep

        if nn != []:
            ret = ' '.join(nn) + ' ' + ret

        if poss is not None:
            ret = poss + '\'s ' + ret

        if prep is not None:
            ret = ret + ' ' + prep

        return ret

    #collapledではないdependency抽出の場合
    def concat_prep(self, prep, dependencies):
        for dependency,gov,dep in dependencies:
            # May be it is neccesary to focus on specific cc as either 'or' or 'to'
            if gov == prep:
                if dependency == 'pobj':
                    return prep + ' ' + self.concat_noun(dep,dependencies)
                elif dependency == 'pcomp':
                    return prep + ' ' + self.extract_sentence(dep,dependencies)

    #return (verb,object)
    def extract_predicate(self, verb, dependencies):
        for dependency,gov,dep in dependencies:
            if gov == verb:
                if dependency == 'dobj':
                    return (gov,self.concat_noun(dep, dependencies))
                elif dependency == 'ccomp':
                    return (gov,self.extract_sentence(dep,dependencies))
                elif dependency == 'acomp':
                    return (gov,self.concat_noun(dep,dependencies))
        else:
            return None

    #return string
    def extract_sentence(self, verb, dependencies):
        #
        subject = ''
        for dependency,gov,dep in dependencies:
            if dependency in ['nsubj','csubj'] and gov == verb:
                subject = self.concat_noun(dep,dependencies)
                break

        predicate = self.extract_predicate(verb,dependencies)
        if predicate is None:
            if type(subject) is not unicode and type(subject) is not str:
                ret = subject
            else:
                ret = subject
        else:
            ret = ' '.join([subject,predicate[0],predicate[1]])
        return ret

    def extract_svo(self, sentences = None, dependencies = None):
        if sentences is None:
            if self.sentences is None:
                return []
            else:
                sentences = self.sentences
                dependencies = self.dependencies

        #1. extract Named Entity
        NNPs = {word[0] : word[1]['NamedEntityTag'] for word in sentences['words'] if word[1]['PartOfSpeech'] == 'NNP'}

        #2. subject and verb pare
        subjects = [(gov,dep) for dependency,gov,dep in dependencies if dependency in ['nsubj','csubj'] and dep in NNPs]

        #3. objects
        # FIXME : terrible implement
        objects = [self.extract_predicate(gov, dependencies) for dependency,gov,dep in dependencies if dependency in ['dobj','ccomp','acomp']]
        idobjs = [(gov,dep) for dependency,gov,dep in dependencies if dependency == 'idobjs']
        if idobjs != []:
            objects = [(gov,dep + ' ' + idobj) for idobj in idobjs  for dependency,gov,dep in dependencies]

        #4. construct triple
        svos = []
        for sv,subject in subjects:
            for ov,obj in objects:
                if sv == ov:
                    svos.append((subject,sv,obj))
                    break
            else:
                svos.append((subject,sv,None))

        #5.
        svos = [(self.concat_noun(svo[0], dependencies),svo[1],svo[2]) for svo in svos]

        return svos

