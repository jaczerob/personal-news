# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 17:45:40 2017

@author: NishitP
"""

import pickle

#doc_new = ['obama is running for president in 2016']


#function to run for prediction
def detecting_fake_news(var):    
#retrieving the best model for prediction call
    load_model = pickle.load(open('./fakenews/final_model.sav', 'rb'))
    # _ = load_model.predict([var])
    prob = load_model.predict_proba([var])

    return prob[0][1]


if __name__ == '__main__':
    var = input("Please enter the news text you want to verify: ")
    print("You entered: " + str(var))
    detecting_fake_news(var)
