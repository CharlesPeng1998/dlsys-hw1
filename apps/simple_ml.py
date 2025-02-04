import struct
import gzip
import numpy as np

import sys
sys.path.append('python/')
import needle as ndl


def parse_mnist(image_filename, label_filename):
    """ Read an images and labels file in MNIST format.  See this page:
    http://yann.lecun.com/exdb/mnist/ for a description of the file format.

    Args:
        image_filename (str): name of gzipped images file in MNIST format
        label_filename (str): name of gzipped labels file in MNIST format

    Returns:
        Tuple (X,y):
            X (numpy.ndarray[np.float32]): 2D numpy array containing the loaded
                data.  The dimensionality of the data should be
                (num_examples x input_dim) where 'input_dim' is the full
                dimension of the data, e.g., since MNIST images are 28x28, it
                will be 784.  Values should be of type np.float32, and the data
                should be normalized to have a minimum value of 0.0 and a
                maximum value of 1.0.

            y (numpy.ndarray[dypte=np.int8]): 1D numpy array containing the
                labels of the examples.  Values should be of type np.int8 and
                for MNIST will contain the values 0-9.
    """
    with gzip.open(image_filename, 'rb') as image_file:
        image_file_content = image_file.read()
        num_images, = struct.unpack_from(">i", image_file_content, 4)
        x = np.frombuffer(image_file_content, dtype=np.uint8, offset=16)
        x_norm = x.reshape(num_images, -1).astype(np.float32) / 255

    with gzip.open(label_filename, 'rb') as label_file:
        label_file_content = label_file.read()
        y = np.frombuffer(label_file_content, dtype=np.uint8, offset=8)

    return x_norm, y


def softmax_loss(z, y_one_hot):
    """ Return softmax loss.  Note that for the purposes of this assignment,
    you don't need to worry about "nicely" scaling the numerical properties
    of the log-sum-exp computation, but can just compute this directly.

    Args:
        z (ndl.Tensor[np.float32]): 2D Tensor of shape
            (batch_size, num_classes), containing the logit predictions for
            each class.
        y_one_hot (ndl.Tensor[np.int8]): 2D Tensor of shape (batch_size, num_classes)
            containing a 1 at the index of the true label of each example and
            zeros elsewhere.

    Returns:
        Average softmax loss over the sample. (ndl.Tensor[np.float32])
    """
    batch_size = z.shape[0]
    z0 = ndl.exp(z).sum(1)
    z1 = ndl.log(z0).sum()
    z_y = ndl.summation(z * y_one_hot)
    loss = (z1 - z_y) / batch_size
    return loss


def nn_epoch(x, y, w1, w2, lr = 0.1, batch=100):
    """ Run a single epoch of SGD for a two-layer neural network defined by the
    weights W1 and W2 (with no bias terms):
        logits = ReLU(X * W1) * W2
    The function should use the step size lr, and the specified batch size (and
    again, without randomizing the order of X).

    Args:
        X (np.ndarray[np.float32]): 2D input array of size
            (num_examples x input_dim).
        y (np.ndarray[np.uint8]): 1D class label array of size (num_examples,)
        w1 (ndl.Tensor[np.float32]): 2D array of first layer weights, of shape
            (input_dim, hidden_dim)
        w2 (ndl.Tensor[np.float32]): 2D array of second layer weights, of shape
            (hidden_dim, num_classes)
        lr (float): step size (learning rate) for SGD
        batch (int): size of SGD mini-batch

    Returns:
        Tuple: (W1, W2)
            W1: ndl.Tensor[np.float32]
            W2: ndl.Tensor[np.float32]
    """
    num_examples = x.shape[0]
    num_classes = w2.shape[1]

    for i in range(0, num_examples, batch):
        x_batch = x[i: i + batch]
        y_batch = y[i: i + batch]

        x_tensor = ndl.Tensor(x_batch)
        z = ndl.relu(x_tensor @ w1) @ w2
        y_one_hot = ndl.Tensor(np.eye(num_classes)[y_batch])
        loss = softmax_loss(z, y_one_hot)

        loss.backward()

        w1 = ndl.Tensor(w1.numpy() - lr * w1.grad.numpy())
        w2 = ndl.Tensor(w2.numpy() - lr * w2.grad.numpy())

    return w1, w2

### CODE BELOW IS FOR ILLUSTRATION, YOU DO NOT NEED TO EDIT

def loss_err(h,y):
    """ Helper function to compute both loss and error"""
    y_one_hot = np.zeros((y.shape[0], h.shape[-1]))
    y_one_hot[np.arange(y.size), y] = 1
    y_ = ndl.Tensor(y_one_hot)
    return softmax_loss(h,y_).numpy(), np.mean(h.numpy().argmax(axis=1) != y)
