# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 23:24:53 2021

@author: mszx2
"""

from automata import IPA

def to_gen(s):
    for c in s:
        yield c

def spawn_worker(instance, *args, payload = None):
    res = instance.transition(*args, payload = instance.memory_stack)
    return res

def log_stopped(instance):
    print(instance, 'stopped!')
    print(list(map(lambda i: i.stopped, instance.instances)))

def top(deque):
    return deque[-1]

def automata_factory():    
    evaluator = IPA(
        K = ['s1', 's2', 's3', 's4', 's6'],
        s = 's0',
        F = ['f5']
    )
    
    @evaluator.state('f5')
    def end(pair):
        return False
    
    @evaluator.state('s0')
    def start(pair):
        stream, instance = pair
        instance.memory_stack.append('$')
        return instance.transition('s1', 'E',
                                    payload = instance.memory_stack)
    
    @evaluator.state('s1')
    def q1(pair):
        stream, instance = pair
        evaluator.spawn(spawn_worker, stream, 's2', 'E')

        payload = top(instance.memory_stack)
        try:
            stream_gen = to_gen(stream)
            token = next(stream_gen)
            instance.stream = list(stream_gen)
        except:
            #log_stopped(instance)
            return False
        if token == '0' and payload == '$':
            instance.memory_stack.pop()
            instance.memory_stack.append('$')
            instance.memory_stack.append('-')

        elif token == '1' and payload == '-':
            instance.memory_stack.pop()
            instance.memory_stack.append('+')
        
        elif token == '0' and payload == '+':
            instance.memory_stack.pop()
            instance.memory_stack.append('+')
            instance.memory_stack.append('-')
        
        elif token == '0' and payload == '-':
            instance.memory_stack.pop()
            instance.memory_stack.append('-')
        
        elif token == '1' and payload == '$':
            instance.memory_stack.pop()
            instance.memory_stack.append('$')
        
        elif token == '1' and payload == '+':
            instance.memory_stack.pop()
            instance.memory_stack.append('+')
        else:
            #log_stopped(instance)
            return False
        return instance.transition('s1', token, payload = instance.memory_stack)
    
    @evaluator.state('s2')
    def q2(pair):
        stream, instance = pair
        payload = top(instance.memory_stack)
        try:
            stream_gen = to_gen(stream)
            token = next(stream_gen)
            instance.stream = list(stream_gen)
        except:
            if payload == '+':
                instance.memory_stack.pop()
                instance.memory_stack.append('+')
                return instance.transition('s3', '$',
                                        payload = instance.memory_stack)
            #log_stopped(instance)
            return False
        
        if token == '1' and payload == '-':
            instance.memory_stack.pop()
            instance.memory_stack.append('-')
        elif token == '1' and payload == '$':
            instance.memory_stack.pop()
            instance.memory_stack.append('$')
        elif token == '1' and payload == '+':
            instance.memory_stack.pop()
            instance.memory_stack.append('+')
        else:
            #log_stopped(instance)
            return False
        return instance.transition('s3', token,
                                    payload = instance.memory_stack)
    
    @evaluator.state('s3')
    def q3(pair):
        stream, instance = pair
        payload = top(instance.memory_stack)
        
        if payload == '$':
            instance.memory_stack.pop()
            instance.memory_stack.append('$')
        elif payload == '+':
            instance.memory_stack.pop()
        elif payload == '-':
            instance.memory_stack.pop()
            instance.memory_stack.append('-')
        else:
            return False
        return instance.transition('s4', 'E',
                                        payload = instance.memory_stack)
    
    @evaluator.state('s4')
    def q4(pair):
        stream, instance = pair
        payload = top(instance.memory_stack)
        try:
            stream_gen = to_gen(stream)
            token = next(stream_gen)
            instance.stream = list(stream_gen)
        except:
            if payload == '$':
                instance.memory_stack.pop()
                return instance.transition('f5', '$',
                                        payload = instance.memory_stack)
            elif payload == '+':
                instance.memory_stack.pop()
                return instance.transition('s4', '$',
                                        payload = instance.memory_stack)
            else:
                return False
        
        if token == '0' and (payload == '+' or payload == '-'):
            instance.memory_stack.pop()
            
        elif token == '0' and payload == '$':
            instance.memory_stack.pop()
            instance.memory_stack.append('$')
        
        elif token == '1' and payload == '$':
            instance.memory_stack.pop()
            instance.memory_stack.append('$')
            
        elif token == '1' and payload == '-':
            instance.memory_stack.pop()
        elif token == '1' and payload == '+':
            instance.memory_stack.pop()
            return instance.transition('s4', token,
                                        payload = instance.memory_stack)              
        else:
            return False
        
        return instance.transition('s6', token,
                                        payload = instance.memory_stack)
    
    @evaluator.state('s6')
    def q6(pair):
        stream, instance = pair
        payload = top(instance.memory_stack)
        try:
            stream_gen = to_gen(stream)
            token = next(stream_gen)
            instance.stream = list(stream_gen)
        except:
            return False
        
        if token == '0' and payload == '$':
            instance.memory_stack.pop()
            instance.memory_stack.append('$')
        elif token == '1' and payload == '$':
            instance.memory_stack.pop()
            instance.memory_stack.append('$')
        elif token == '0' and payload == '+':
            instance.memory_stack.pop()
        elif token == '1' and payload == '+':
            instance.memory_stack.pop()
        else:
            return False
        return instance.transition('s6', token,
                                        payload = instance.memory_stack)
    
    evaluator.reset()
    return evaluator

def test(task): 
    assert task('01') == True
    assert task('01011') == True
    assert task('01010111') == True
    assert task('01010101111') == True
    assert task('01010101011111') == True
    assert task('01010101010111111') == True
    assert task('01010100000000000111') == True
    assert task('111101') == True    
    assert task('00001') == True

    assert task('') == False
    assert task('0000') == False

    assert task('0') == False
    assert task('010110') == False
    ### ---
    '''
    assert task('010111') == False

    assert task('0101010101111') == False
    assert task('010101010111') == False
    
    assert task('1') == False
    assert task('1111') == False
    '''
    
if __name__ == '__main__':
    task = IPA.create_task(automata_factory,
                                        log = True)
    test(task)
    print('OK!')
    