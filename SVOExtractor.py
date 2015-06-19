#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Extractor():
    def __init__(self, coref = None, sentence = None):
        if sentence is not None:
            self.coref = coref
            self.sentence = sentence
            self.dependencies = self.sentence['dependencies']

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
                elif dependency == 'prep':
                    prep = self.concat_prep(prep, dependencies)
                # collapsed 対応
                elif 'prep' in dependency:
                    if prep is not None:
                        prep += dependency.lstrip('prep_') + ' ' + dep.decode('utf-8')
                    else:
                        prep = dependency.lstrip('prep_') + ' '  + dep.decode('utf-8')

        if nn != []:
            ret = ' '.join(nn) + ' ' + ret

        if poss is not None:
            ret = poss + '\'s ' + ret

        if prep is not None:
            ret = ret.decode('utf-8') + ' ' + prep

        return ret

    #collapsedではないdependency抽出の場合
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
                    if gov == dep:
                        return (gov, self.concat_noun(dep, dependencies))
                    else:
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

    def extract_svo(self, sentence = None, dependencies = None, coref = None):
        if sentence is None:
            if self.sentence is None:
                return []
            else:
                sentence = self.sentence
                dependencies = self.dependencies
        coref = dict() if coref is None else coref

        #1. extract Named Entity
        NNPs = {word[0] : word[1]['NamedEntityTag'] for word in sentence['words'] if word[1]['PartOfSpeech'] == 'NNP'}

        #2. subject and verb pare
        subjects = [(gov,dep) for dependency,gov,dep in dependencies if dependency in ['nsubj','csubj'] and (dep in NNPs or dep in coref)]

        # 3. objects
        # FIXME : terrible implement
        objects = [self.extract_predicate(gov, dependencies) for dependency,gov,dep in dependencies if dependency in ['dobj','ccomp','acomp']]
        idobjs = [(gov,dep) for dependency,gov,dep in dependencies if dependency == 'idobjs']
        if idobjs != []:
            objects = [(gov,dep + ' ' + idobj) for idobj in idobjs  for dependency,gov,dep in dependencies]

        # 4. construct triple
        svos = []
        for sv,subject in subjects:
            # complete noun phrase
            if subject in coref:
                subject = coref[subject]
            else:
                subject = self.concat_noun(subject, dependencies)
            for ov,obj in objects:
                if sv == ov:
                    if obj in coref:
                        obj = coref[obj]
                    svos.append((subject,sv,obj))
                    break
            else:
                svos.append((subject,sv,None))

        # svos = [(self.concat_noun(svo[0], dependencies),svo[1],svo[2]) for svo in svos]

        return svos

