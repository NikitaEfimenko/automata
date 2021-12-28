# -*- coding: utf-8 -*-
"""
Created on Tue Dec 28 17:41:39 2021

@author: mszx2
"""

from automata import FSM

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
    factory = FSM.from_json('./test_fsm_scheme.json')
    task = FSM.create_task(factory,
                           log = True)
    
    test(task)
    print('OK!')