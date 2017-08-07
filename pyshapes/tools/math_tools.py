import scipy.linalg
import scipy.sparse

import numpy as np

def sparse_diagonal(data):
    data = np.array(data)
    n = data.size
    return scipy.sparse.diags(np.atleast_2d(data), [0], shape=(n, n))


def __dot2(A, B):
    spA = scipy.sparse.issparse(A)
    spB = scipy.sparse.issparse(B)

    if spA:
        return A.dot(B)

    if spB:
        return B.T.dot(A.T).T

    return A.dot(B)


def dot(*args):
    assert len(args) >= 2

    args = list(args)

    if len(args) > 2:
        # extend middle vectors into sparse_diagonals
        def auto_diag(m):
            if len(m.shape) == 1:
                return sparse_diagonal(m)
            return m

        args = [args[0]] + [auto_diag(m) for m in args[1:-1]] + [args[-1]]

    while len(args) > 1:
        B = args.pop()
        A = args.pop()
        args.append(__dot2(A, B))

    assert len(args) == 1
    return args[0]
