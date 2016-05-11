
from __future__ import division

import time
import copy

import pandas as pd
import numpy

from scipy.sparse import hstack, vstack
from sklearn.preprocessing import LabelEncoder, OneHotEncoder


# class EMEstimate(object):
    
#     def __init__(self, max_iter=100, init=None, random_decisions=False):
        
#         self.init = init # options 'jaro', 'random', dict
#         self.max_iter = max_iter
#         self.random_decisions = random_decisions

#         self._p = None
#         self._m = None
#         self._u = None

#         self._g = None


class ECMEstimate(object):
    """ 

    Algorithm to compute the Expectation/Conditional Maximisation algorithm in
    the context of record linkage. The algorithm is clearly described by
    Herzog, Schueren and Winkler in the book: Data Quality and Record Linkage
    Tehniques. The algorithm assumes that the comparison variables are
    mutually independent given the match status.
 
    :param max_iter: An integer specifying the maximum number of
                    iterations. Default maximum number of iterations is 100.

    :type max_iter: int
        

    """

    def __init__(self, max_iter=100, init='jaro', random_decisions=False):

        self.max_iter = max_iter
        self.random_decisions = random_decisions

    @property
    def weights(self):

        # [feature:{for } for i in np.unique(self.y_features)]
        return numpy.log(self._m/self._u)

    def train(self, vectors, *args, **kwargs):
        """

        Start the estimation of parameters with the iterative EM-algorithm. 

        """

        vectors = numpy.array(vectors)

        y = self.encode_vectors(vectors)

        self._m = 0+0.1+0.8*self.y_classes
        self._u = 1-0.1-0.8*self.y_classes
        self._p = 0.1

        iteration = 0

        # Iterate until converged
        while iteration < self.max_iter:
            
            prev_m, prev_u, prev_p = self._m, self._u, self._p

            # Expectation step
            g = self._expectation(y)

            # Maximisation step
            self._m, self._u, self._p = self._maximization(y, g)

            # Increment counter
            iteration += 1

            # Stop iterating when parameters are close to previous iteration
            if (numpy.allclose(prev_m, self._m, atol=10e-5) and numpy.allclose(prev_u, self._u, atol=10e-5) and numpy.allclose(prev_p, self._p, atol=10e-5)):
                break

        return 

    def _maximization(self, y_enc, g):
        """ 

        Maximisation step of the ECM-algorithm. 

        :param samples: Dataframe with comparison vectors. 
        :param weights: The number of times the comparison vectors samples occur. This frame needs to have the same index as samples. 
        :param prob: The expectation of comparison vector in samples.

        :return: A dict of marginal m-probabilities, a dict of marginal u-probabilities and the match prevalence. 
        :rtype: (dict, dict, float)

        """

        m = g.T*y_enc/numpy.sum(g)
        u = (1-g).T*y_enc/numpy.sum(1-g)
        p = numpy.average(g)
        
        return m, u, p

    def _expectation(self, y_enc):
        """ 

        Compute the expectation of the given comparison vectors. 

        :return: A Series with the expectation.
        :rtype: pandas.Series
        """

        # The following approach has a lot of computational advantages. But if
        # there is a better method, replace it. See Herzog, Scheuren and
        # Winkler for details about the algorithm.
        m = numpy.exp(y_enc.dot(numpy.log(self._m)))
        u = numpy.exp(y_enc.dot(numpy.log(self._u)))
        p = self._p

        return p*m/(p*m+(1-p)*u) 
       
    def encode_vectors(self, vectors):

        n_samples, n_features = vectors.shape

        data_enc = []

        self.y_features = numpy.array([])
        self.y_classes = numpy.array([])

        for i in range(0, n_features):

            le = LabelEncoder()
            enc = OneHotEncoder()

            label_encoded = le.fit_transform(vectors[:,i]).reshape((-1,1))
            data_enc_i = enc.fit_transform(label_encoded)

            self.y_classes = numpy.append(self.y_classes, le.classes_)
            self.y_features = numpy.append(self.y_features, numpy.repeat(i, len(le.classes_)))

            data_enc.append(data_enc_i)

        return hstack(data_enc)

    # def predict_proba(self, samples):

        # Use the trained le encoder to sample data

    #     p_link = self._expectation(samples)
    #     p_nonlink = 1-p_link

    #     return numpy.array([p_link, p_nonlink])

