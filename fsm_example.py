# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 21:57:38 2021

@author: mszx2
"""

from automata import FSM

def automata_factory():    
    evaluator = FSM(
        K = ['q1', 'q2'],
        s = 'start',
        F = ['q3'])
    
    @evaluator.state('start')
    def start(token):
        if token == 'a':
            return evaluator.transition('q1', token)
    
    @evaluator.state('q3')
    def q3(token):
        return False
    
    @evaluator.state('q1')
    def q1(token):
        if token == 'b':
            return evaluator.transition('q2', token)
        if token == 'c':
            return evaluator.transition('q3', token)
        
    @evaluator.state('q2')
    def q2(token):
        if token == 'c':
            return evaluator.transition('q3', token)
        if token == 'b':
            return evaluator.transition('q2', token)
    
    evaluator.reset()
    return evaluator

def test(task):
    assert task('') == False
    assert task('a') == False
    assert task('ab') == False
    assert task('ac') == True
    assert task('abc') == True
    assert task('abbbbbbbc') == True
    assert task('abcc') == False
    assert task('bcbc') == False

if __name__ == '__main__':
    task = FSM.create_task(automata_factory, log = True)
    test(task)
    print('OK!')
    