# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 21:57:40 2021

@author: mszx2
"""
import string
import time
from collections import deque
import copy

def to_gen(s):
    for c in s:
        yield c

def charged(fn):
    def wrapper_charged(*args, **kwargs):
        v = fn(*args, **kwargs)
        v.send(None)
        return v
    return wrapper_charged

def coroutined(state_fn):
    def wrapper_coroutined():
        while True:
            token = yield
            if not state_fn(token):
                break
    return wrapper_coroutined

class SchemeMixin:        
    def from_json(json_file):
        import json
        with open(json_file) as f:
            scheme = json.load(f)
            success, log = SchemeMixin.scheme_validation(scheme)
            if success:
                return SchemeMixin.build_from_scheme(scheme)
            else:
                raise BaseException('Validation error, {}'.format(log))
                
    def scheme_validation(scheme):
        return True, 'Success!'
    '''
    def from_image(img_file):
        pass
    
    def scheme_vis():
        pass
    '''
    def build_from_scheme(scheme):
        instance = scheme['instance']
        init = scheme['init']
        def factory():
            def add_state(evaluator, query):
                [from_state, conds, to_states] = query
                @evaluator.state(from_state)
                def state_fn(token):
                    for cond, state in zip(conds, to_states):
                        if token in cond:
                            return evaluator.transition(state, token)
                    return False
            if instance.lower() == 'fsm':
                transitions = scheme['transitions']
                K, s, F = init["K"], init["s"], init["F"]
                evaluator = FSM(K = K,
                                s = s,
                                F = F)
                for transition in transitions:
                    query = list(transition.values())
                    add_state(evaluator, query)
                for f in F:
                    add_state(evaluator, [f, [], [f]])
            evaluator.reset()
            return evaluator
        return factory
            
class Automata(SchemeMixin):
    def __init__(self,
               K = [],
               s = [],
               F = [],
               A = string.printable):
        SchemeMixin.__init__(self)
        self.s = s
        self.K = K
        self.F = F
        self.A = A
        
        self.log = []
        self.all_states = [self.s, *self.K, *self.F]
        self.states = {k: None for k in self.all_states}
        self.state_factories = {k: None for k in self.all_states}
    
    
    def reset(self):
        self.log = []
        self.stopped = False
        self.current_state = None
        if self.states[self.s] is not None:
            self.transition(self.s, '$')
    
    def _register_state(self, label, wrapped, state_fn):
        self.states[label] = wrapped()
        self.state_factories[label] = state_fn
    
    def state(self, state_label):
        if state_label not in self.states.keys():
            raise BaseException('transition alphabet does not contain transition "{}"'.format(state_label))
        def decorator(state_fn):
            @charged
            @coroutined
            def wrapped(*args, **kwargs):
                return state_fn(*args, **kwargs)
            self._register_state(state_label, wrapped, state_fn)
            return wrapped
        return decorator
    
    def send(self, payload):
        try:
            self.current_state.send(payload)
        except StopIteration:
            self.stopped = True
            
    def recognized(self):
        end_states = [self.states[f] for f in self.F]
        if self.stopped:
            return False
        return self.current_state in end_states
    
    def transition(self, state, token, payload = deque()):
        if state not in self.states:
            raise BaseException('undescribed condition "{}"'.format(state))
        elif self.states[state] is None:
            raise BaseException('the transition is not registered "{}"'.format(state))
        else:
            self._logged(token, state, payload = payload)
            self.current_state = self.states[state]
            return True
    
    def evalute(self, istream):
        for token in istream:
            self.send(token)
                
    def create_task(evaluator_factory, log = False):
        def task(istream):
            evaluator = evaluator_factory()
            evaluator.evalute(istream)
            if log:
                print(" -> ".join(evaluator.log))
            return evaluator.recognized()
        return task

class FSM(Automata):
    def __init__(self,
                 K = [],
                 s = None,
                 F = [],
                 A = string.printable):
        Automata.__init__(self,
                          K = K,
                          s = s,
                          F = F,
                          A = A)
        self.reset()

    def reset(self):
        super().reset()
    
    def _logged(self, token, state, payload = None):
         self.log.append('({}, {})'.format(token, state))
        
class IPA(Automata):
    def __init__(self, *args, **kwargs):
        Automata.__init__(self, *args, **kwargs)
        self.reset()
        
    def reset(self):
        super().reset()
        self.S = self.A
        self.e = None
        
        self.instances = []
        self.memory_stack = deque()
        self.stream = []
    
    def copy_instance(self, flow = []):
        instance = IPA(K = self.K,
                         s = self.s,
                         F = self.F,
                         A = self.A)
        

        instance.memory_stack = self.memory_stack.copy()
        instance.state_factories = {k:v for k, v in self.state_factories.items()}
        
        def add_state(key, state_coroutine):
            @instance.state(key)
            def coroutine(pair):
                return state_coroutine(pair)
        
        for key, state_coroutine in instance.state_factories.items():
            add_state(key, state_coroutine)
        
        instance.log = self.log.copy()
        instance.stopped = False
        instance.stream = flow
        return instance
        
    def spawn(self, worker, flow, *args, **kwargs):
        instance = self.copy_instance(flow = flow)
        result = worker(instance, *args, **kwargs)
        self.instances.append(instance)
        return result
    
    def _logged(self, token, state, payload = deque()):
         self.log.append('({}, {}, stack_memory={}, stream = {})'.format(state, token, payload, self.stream))
    
    def recognized(self):
        def get_end_states(instance):
            return [instance.states[f] for f in instance.F]
        
        end_states = get_end_states(self)
        
        end_states_conditions = self.current_state in end_states or \
            any(map(lambda x: x.current_state in get_end_states(x), self.instances))
        empty_stacks_conditions = len(self.memory_stack) == 0 or any(map(lambda x: len(x.memory_stack) == 0, self.instances))
        return end_states_conditions or empty_stacks_conditions
    
    def evalute(self, istream):
        self.stream = list(istream)
        flows = [self.stream]
        instances = [self]
        def log(i, instance):
            print('instance {}'.format(instance))
            print('{}-i instance:'.format(i))
            print("\n".join(instance.log))
            print('is stopped? {}'.format(instance.stopped))
            print('current state {}'.format([k for k, state in instance.states.items() if state == instance.current_state]))
        while True:
            for i, (flow, instance) in enumerate(zip(flows, instances)):
                #log(i, instance)
                instance.send((flow, instance))
            instances = [self, *self.instances]
            flows = list(map(lambda i: i.stream, instances))
            
            if self.stopped and all(map(lambda x: x.stopped, self.instances)):
                break
        
    def create_task(evaluator_factory,
                    log = False):
        def task(istream):
            if log:
                print('test for: "{}"'.format(istream))
            evaluator = evaluator_factory()
            evaluator.evalute(istream)
            if log:
                print("\n".join(evaluator.log))
                for i, instance in enumerate(evaluator.instances):
                    print('{}-i instance:'.format(i + 2))
                    print("\n".join(instance.log))
                print('-' * 20)
            return evaluator.recognized()
        return task