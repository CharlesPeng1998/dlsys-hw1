"""Operator implementations."""

from numbers import Number
from typing import Optional, List
from .autograd import NDArray
from .autograd import Op, Tensor, Value, TensorOp
from .autograd import TensorTuple, TensorTupleOp
import numpy

# NOTE: we will import numpy as the array_api
# as the backend for our computations, this line will change in later homeworks
import numpy as array_api


class EWiseAdd(TensorOp):
    def compute(self, a: NDArray, b: NDArray):
        return a + b

    def gradient(self, out_grad: Tensor, node: Tensor):
        return out_grad, out_grad


def add(a, b):
    return EWiseAdd()(a, b)


class AddScalar(TensorOp):
    def __init__(self, scalar):
        self.scalar = scalar

    def compute(self, a: NDArray):
        return a + self.scalar

    def gradient(self, out_grad: Tensor, node: Tensor):
        return out_grad


def add_scalar(a, scalar):
    return AddScalar(scalar)(a)


class EWiseMul(TensorOp):
    def compute(self, a: NDArray, b: NDArray):
        return a * b

    def gradient(self, out_grad: Tensor, node: Tensor):
        lhs, rhs = node.inputs
        return out_grad * rhs, out_grad * lhs


def multiply(a, b):
    return EWiseMul()(a, b)


class MulScalar(TensorOp):
    def __init__(self, scalar):
        self.scalar = scalar

    def compute(self, a: NDArray):
        return a * self.scalar

    def gradient(self, out_grad: Tensor, node: Tensor):
        return (out_grad * self.scalar,)


def mul_scalar(a, scalar):
    return MulScalar(scalar)(a)


class PowerScalar(TensorOp):
    """Op raise a tensor to an (integer) power."""

    def __init__(self, scalar: int):
        self.scalar = scalar

    def compute(self, a: NDArray) -> NDArray:
        return array_api.power(a, self.scalar)

    def gradient(self, out_grad, node):
        ### BEGIN YOUR SOLUTION
        raise NotImplementedError()
        ### END YOUR SOLUTION


def power_scalar(a, scalar):
    return PowerScalar(scalar)(a)


class EWiseDiv(TensorOp):
    """Op to element-wise divide two nodes."""

    def compute(self, a, b):
        return a / b

    def gradient(self, out_grad: Tensor, node: Tensor):
        lhs, rhs = node.inputs
        return out_grad / rhs, -out_grad * lhs * (rhs ** -2)


def divide(a, b):
    return EWiseDiv()(a, b)


class DivScalar(TensorOp):
    def __init__(self, scalar):
        self.scalar = scalar

    def compute(self, a):
        return a / self.scalar

    def gradient(self, out_grad: Tensor, node: Tensor):
        return out_grad / self.scalar


def divide_scalar(a, scalar):
    return DivScalar(scalar)(a)


class Transpose(TensorOp):
    def __init__(self, axes: Optional[tuple] = None):
        self.axes = axes

    def compute(self, a):
        axes = list(range(len(a.shape)))
        if self.axes is None:
            axes[-1], axes[-2] = axes[-2], axes[-1]
        else:
            axes[self.axes[0]], axes[self.axes[1]] = axes[self.axes[1]], axes[self.axes[0]]
        return array_api.transpose(a, axes)

    def gradient(self, out_grad: Tensor, node: Tensor):
        return transpose(out_grad, self.axes)


def transpose(a, axes=None):
    return Transpose(axes)(a)


class Reshape(TensorOp):
    def __init__(self, shape):
        self.shape = shape

    def compute(self, a):
        return array_api.reshape(a, self.shape)

    def gradient(self, out_grad: Tensor, node: Tensor):
        x, = node.inputs
        return reshape(out_grad, x.shape)


def reshape(a, shape):
    return Reshape(shape)(a)


class BroadcastTo(TensorOp):
    def __init__(self, shape):
        self.shape = shape

    def compute(self, a):
        return array_api.broadcast_to(a, self.shape)

    def gradient(self, out_grad: Tensor, node: Tensor):
        x, = node.inputs
        output_shape = out_grad.shape
        input_shape = x.shape
        reduce_dim = list()
        input_shape_idx = len(input_shape) - 1
        for output_shape_idx in range(len(output_shape) - 1, -1, -1):
            if input_shape_idx < 0:
                reduce_dim.append(output_shape_idx)
            else:
                if output_shape[output_shape_idx] != input_shape[input_shape_idx]:
                    reduce_dim.append(output_shape_idx)
            input_shape_idx -= 1
        return reshape(summation(out_grad, tuple(reduce_dim)), input_shape)


def broadcast_to(a, shape):
    return BroadcastTo(shape)(a)


class Summation(TensorOp):
    def __init__(self, axes: Optional[tuple] = None):
        self.axes = axes
        if isinstance(self.axes, int):
            self.axes = (self.axes,)

    def compute(self, a):
        return array_api.sum(a, self.axes)

    def gradient(self, out_grad: Tensor, node: Tensor):
        x, = node.inputs
        input_shape = x.shape
        sum_shape = list(input_shape)

        if self.axes:
            for dim in self.axes:
                sum_shape[dim] = 1
        else:
            sum_shape = [1 for _ in range(len(input_shape))]

        out_grad = reshape(out_grad, sum_shape)
        return out_grad * array_api.ones(input_shape)


def summation(a, axes=None):
    return Summation(axes)(a)


class MatMul(TensorOp):
    def compute(self, a, b):
        return array_api.matmul(a, b)

    def gradient(self, out_grad: Tensor, node: Tensor):
        x, y = node.inputs
        dx = out_grad @ transpose(y)
        dy = transpose(x) @ out_grad

        if dx.shape != x.shape:
            dx = summation(dx, tuple(range(len(dx.shape) - len(x.shape))))
        if dy.shape != y.shape:
            dy = summation(dy, tuple(range(len(dy.shape) - len(y.shape))))

        return dx, dy


def matmul(a, b):
    return MatMul()(a, b)


class Negate(TensorOp):
    def compute(self, a):
        return array_api.negative(a)

    def gradient(self, out_grad: Tensor, node: Tensor):
        return -out_grad


def negate(a):
    return Negate()(a)


class Log(TensorOp):
    def compute(self, a):
        return array_api.log(a)

    def gradient(self, out_grad: Tensor, node: Tensor):
        x, = node.inputs
        return out_grad / x


def log(a):
    return Log()(a)


class Exp(TensorOp):
    def compute(self, a):
        return array_api.exp(a)

    def gradient(self, out_grad: Tensor, node: Tensor):
        x, = node.inputs
        return out_grad * exp(x)


def exp(a):
    return Exp()(a)


class ReLU(TensorOp):
    def compute(self, a):
        return array_api.maximum(a, 0)

    def gradient(self, out_grad: Tensor, node: Tensor):
        x, = node.inputs
        cached_data = x.cached_data
        return out_grad * Tensor((cached_data > 0).astype(array_api.float32))


def relu(a):
    return ReLU()(a)

