'''
@author: Adrian Hoffmann
'''

import numpy as np
from elina_abstract0 import *
from elina_manager import *
from deeppoly_nodes import *
from deepzono_nodes import *
from functools import reduce
import ctypes

class layers:
    def __init__(self):
        self.layertypes = []
        self.weights = []
        self.biases = []
        self.filters = []
        self.numfilters = []
        self.filter_size = [] 
        self.input_shape = []
        self.strides = []
        self.padding = []
        self.out_shapes = []
        self.pool_size = []
        self.numlayer = 0
        self.ffn_counter = 0
        self.conv_counter = 0
        self.residual_counter = 0
        self.maxpool_counter = 0
        self.specLB = []
        self.specUB = []
        self.original = []
        self.zonotope = []
        self.predecessors = []
        self.lastlayer = None

    def calc_layerno(self):
        return self.ffn_counter + self.conv_counter + self.residual_counter + self.maxpool_counter

class Analyzer:
    def __init__(self, ir_list, nn, domain, timeout_lp, timeout_milp, specnumber, use_area_heuristic, testing = False):
        """
        Arguments
        ---------
        ir_list: list
            list of Node-Objects (e.g. from DeepzonoNodes), first one must create an abstract element
        domain: str
            either 'deepzono', 'refinezono' or 'deeppoly'
        """
        self.ir_list = ir_list
        self.is_greater = is_greater_zono
        self.refine = False
        if domain == 'deeppoly' or domain == 'refinepoly':
            self.man = fppoly_manager_alloc()
            self.is_greater = is_greater
        elif domain == 'deepzono' or domain == 'refinezono':
            self.man = zonoml_manager_alloc()
            self.is_greater = is_greater_zono
        if domain == 'refinezono' or domain == 'refinepoly':
            self.refine = True
        self.domain = domain
        self.nn = nn
        self.timeout_lp = timeout_lp
        self.timeout_milp = timeout_milp
        self.specnumber = specnumber
        self.use_area_heuristic = use_area_heuristic
        self.testing = testing

    
    def __del__(self):
        elina_manager_free(self.man)
        
    
    def get_abstract0(self):
        """
        processes self.ir_list and returns the resulting abstract element
        """
        element = self.ir_list[0].transformer(self.man)
        nlb = []
        nub = []
        testing_nlb = []
        testing_nub = []
        for i in range(1, len(self.ir_list)):
            print(self.ir_list[i])
            if self.testing:
                if self.domain == 'deepzono' or self.domain == 'refinezono':
                    element, test_lb, test_ub = self.ir_list[i].transformer(self.nn, self.man, element, nlb,nub, self.domain=='refinezono', self.timeout_lp, self.timeout_milp, self.testing)
                else:
                    element, test_lb, test_ub = self.ir_list[i].transformer(self.nn, self.man, element, nlb, nub, self.domain=='refinepoly', self.timeout_lp, self.timeout_milp, self.use_area_heuristic, self.testing)
                testing_nlb.append(test_lb)
                testing_nub.append(test_ub)
            else:
                if self.domain == 'deepzono' or self.domain == 'refinezono':
                    element = self.ir_list[i].transformer(self.nn, self.man, element, nlb,nub, self.domain=='refinezono', self.timeout_lp, self.timeout_milp, self.testing)
                else:
                    element = self.ir_list[i].transformer(self.nn, self.man, element, nlb, nub, self.domain=='refinepoly', self.timeout_lp, self.timeout_milp, self.use_area_heuristic, self.testing)
        if self.testing:
            return element, testing_nlb, testing_nub
        return element, nlb, nub
    
    
    def analyze(self):
        """
        analyses the network with the given input
        
        Returns
        -------
        output: int
            index of the dominant class. If no class dominates then returns -1
        """
        element, nlb, nub = self.get_abstract0()
        output_size = 0
        if self.domain == 'deepzono' or self.domain == 'refinezono':
            output_size = self.ir_list[-1].output_length
        else:
            output_size = reduce(lambda x,y: x*y, self.ir_list[-1].bias.shape, 1)
    
        dominant_class = -1
        if self.specnumber==0:
            for i in range(output_size):
                flag = True
                for j in range(output_size):
                    if self.domain == 'deepzono' or self.domain == 'refinezono':
                        if i!=j and not self.is_greater(self.man, element, i, j):
                            flag = False
                            break
                    else:
                        if i!=j and not self.is_greater(self.man, element, i, j, self.use_area_heuristic):
                            flag = False
                            break
                if flag:
                    dominant_class = i
                    break
        elif self.specnumber==9:
            flag = True
            for i in range(output_size):
                if self.domain == 'deepzono' or self.domain == 'refinezono':
                    if i!=3 and not self.is_greater(self.man, element, i, 3):
                        flag = False
                        break
                else:
                    if i!=3 and not self.is_greater(self.man, element, i, 3, self.use_area_heuristic):
                        flag = False
                        break
            if flag:
                dominant_class = 3

        elina_abstract0_free(self.man, element)
        return dominant_class, nlb, nub
    
    
    
    
