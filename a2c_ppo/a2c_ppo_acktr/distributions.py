import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from .utils import AddBias, init

"""
Modify standard PyTorch distributions so they are compatible with this code.
"""

#
# Standardize distribution interfaces
#

# Categorical
class FixedCategorical(torch.distributions.Categorical):
    def sample(self):
        return super().sample().unsqueeze(-1)

    def log_probs(self, actions):
        return (
            super()
            .log_prob(actions.squeeze(-1))
            .view(actions.size(0), -1)
            .sum(-1)
            .unsqueeze(-1)
        )

    def mode(self):
        return self.probs.argmax(dim=-1, keepdim=True)


# Normal
class FixedNormal():
    def __init__(self, mean, log_scale):
        self.mean = mean
        self.log_scale = log_scale

    def log_probs(self, actions):
        var = torch.exp(self.log_scale * 2)
        log_prob =  -((actions - self.mean) ** 2) / (2 * var) - self.log_scale - math.log(math.sqrt(2 * math.pi))
        return log_prob.sum(-1, keepdim=True)

    def entropy(self):
        return (0.5 + 0.5 * math.log(2 * math.pi) + self.log_scale).sum(-1)

    def mode(self):
        return self.mean

    def sample(self):
        with torch.no_grad():
            return torch.normal(self.mean, self.log_scale.exp())


# Bernoulli
class FixedBernoulli(torch.distributions.Bernoulli):
    def log_probs(self, actions):
        return super.log_prob(actions).view(actions.size(0), -1).sum(-1).unsqueeze(-1)

    def entropy(self):
        return super().entropy().sum(-1)

    def mode(self):
        return torch.gt(self.probs, 0.5).float()


class Categorical(nn.Module):
    def __init__(self, num_inputs, num_outputs):
        super(Categorical, self).__init__()

        init_ = lambda m: init(
            m,
            nn.init.orthogonal_,
            lambda x: nn.init.constant_(x, 0),
            gain=0.01)

        self.linear = init_(nn.Linear(num_inputs, num_outputs))

    def forward(self, x):
        x = self.linear(x)
        return FixedCategorical(logits=x)


class DiagGaussian(nn.Module):
    def __init__(self, num_inputs, num_outputs):
        super(DiagGaussian, self).__init__()

        init_ = lambda m: m#init(m, nn.init.orthogonal_, lambda x: nn.init.
                           #    constant_(x, 0))

        self.fc_mean = init_(nn.Linear(num_inputs, num_outputs))
        #self.logstd = nn.Linear(num_inputs, num_outputs)
        self.logstd = AddBias(torch.zeros(num_outputs))

    def forward(self, x):
        action_mean = torch.tanh(self.fc_mean(x))

        #  An ugly hack for my KFAC implementation.
        zeros = torch.zeros(action_mean.size())
        if x.is_cuda:
            zeros = zeros.cuda()

        action_logstd = self.logstd(zeros)
        #action_logstd = self.logstd(x)
        return FixedNormal(action_mean, action_logstd)


class Bernoulli(nn.Module):
    def __init__(self, num_inputs, num_outputs):
        super(Bernoulli, self).__init__()

        init_ = lambda m: init(m, nn.init.orthogonal_, lambda x: nn.init.
                               constant_(x, 0))

        self.linear = init_(nn.Linear(num_inputs, num_outputs))

    def forward(self, x):
        x = self.linear(x)
        return FixedBernoulli(logits=x)
