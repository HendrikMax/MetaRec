import torch
from torch import nn
import torch.nn.functional as F

class MF(nn.Module):
    # Iteration counter
    itr = 0

    def __init__(self, n_user, n_item, k=18, c_vector=1.0, c_bias=1.0, writer=None):
        '''
        Function to initialize the MF class
        '''
        super(MF, self).__init__()

        # This will hold the logging
        self.writer = writer

        # These are simple hyperparameters
        self.k = k
        self.n_user = n_user
        self.n_item = n_item
        self.c_bias = c_bias
        self.c_vector = c_vector

        # These are learned and fit by PyTorch
        self.user = nn.Embedding(n_user, k)
        self.item = nn.Embedding(n_item, k)

        # We've added new terms here:
        self.bias_user = nn.Embedding(n_user, 1)
        self.bias_item = nn.Embedding(n_item, 1)
        self.bias = nn.Parameter(torch.ones(1))

    def __call__(self, train_x):
        '''This is the most important function in this script'''
        # These are the user indices, and correspond to "u" variable
        user_id = train_x[:, 0]
        # These are the item indices, correspond to the "i" variable
        item_id = train_x[:, 1]

        # vector user = p_u
        vector_user = self.user(user_id)
        # vector item = q_i
        vector_item = self.item(item_id)

        # Pull out biases
        bias_user = self.bias_user(user_id).squeeze()
        bias_item = self.bias_item(item_id).squeeze()
        biases = (self.bias + bias_user + bias_item)

        # this is a dot product & a user-item interaction: p_u * q_i
        ui_interaction = torch.sum(vector_user * vector_item, dim=1)

        # Add bias prediction to the interaction prediction
        prediction = ui_interaction + biases
        return prediction

    def loss(self, prediction, target):
        '''
        Function to calculate the loss metric
        '''
        # MSE error between target = R_ui and prediction = p_u * q_i
        loss_mse = F.mse_loss(prediction, target.squeeze())

        # Add new regularization to the biases
        prior_bias_user =  l2_regularize(self.bias_user.weight) * self.c_bias
        prior_bias_item = l2_regularize(self.bias_item.weight) * self.c_bias

        # Compute L2 reularization over user (P) and item (Q) matrices
        prior_user =  l2_regularize(self.user.weight) * self.c_vector
        prior_item = l2_regularize(self.item.weight) * self.c_vector

        # Add up the MSE loss + user & item regularization + user & item biases regularization
        total = loss_mse + prior_user + prior_item + prior_bias_user + prior_bias_item

        # This logs all local variables to tensorboard
        for name, var in locals().items():
            if type(var) is torch.Tensor and var.nelement() == 1 and self.writer is not None:
                self.writer.add_scalar(name, var, self.itr)
        return total

def l2_regularize(array):
    '''
    Function to do L2 regularization
    '''
    loss = torch.sum(array ** 2.0)
    return loss
