import numpy as np
import sympy as sp
import control as ct
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt

'''
F = 10 + (X-1)**2 + (Y-2)**2
G = X - Y

###############################################################################
#            Minimum optimization using Lagrange multiplier lambda
###############################################################################
lam = sp.symbols('lam') 
x = sp.MatrixSymbol('x',2,1)
J=sp.Matrix([(10 + (x[0]-1)**2+(x[1]-2)**2) + lam*(x[0] - x[1])])
grad_J = J.jacobian(x).transpose()
eqn1, eqn2 = grad_J[0,0], grad_J[1,0]
var1, var2 = x[0,0], x[1,0]
solution = sp.solve([eqn1, eqn2], var1,var2, dict=True)
sol1, sol2 = solution[0][var1], solution[0][var2]
# From G=0 , x-y=0 , This will solve for lambda
solution = sp.solve((sol1-sol2), lam)  
sol1, sol2 = sol1.subs(lam,solution[0]), sol2.subs(lam,solution[0])
print([sol1, sol2])
# gradFunc=lambdify(x,grad_J)
# xValue=np.array([[10],[10]])
# gradientNumericalValue=gradFunc(xValue)
'''
'''
###############################################################################
#            Minimum optimization using Scipy Directly instead
###############################################################################
def objective(x):
    return 10 + (x[0]-1)**2 + (x[1]-2)**2
def constraint1(x):
    return x[0] - x[1]
n = 2
x0 = np.zeros(n)
x0[0] = 2.0
x0[1] = 5.0
print('Initial Objective: ' + str(objective(x0)))
b = (0.0,5.0)
bnds = (b, b)
cons1 = {'type': 'eq', 'fun': constraint1}
from scipy.optimize import minimize
solution = minimize(objective,x0,method='SLSQP',\
                    bounds=bnds,constraints=[cons1])
x = solution.x
print('Final Objective: ' + str(objective(x)))
print('Solution')
print('x1 = ' + str(x[0]))
print('x2 = ' + str(x[1]))
'''
###############################################################################
#            Finding Lyapunov function using Direct Method
###############################################################################
# Lyapunov Equation => A.T * P + P * A = - Q
# Sylvester Criteria = A symmetric matrix Q is positive definite if all principal minors 
# are positive. If it is satisfied then linear system is globally asymptotically stable
# and required Lyapunov function is => V = x.T * P * x
x1, x2 = sp.symbols('x1 x2')
X = sp.Matrix([x1, x2])
A = sp.Matrix([[0,4],[-8,-12]])
Q = sp.Matrix([[1,0],[0,1]])
print('Is Q Positive definite: ', Q.is_positive_definite)
P = sp.MatrixSymbol('P', 2, 2).as_explicit()
res = sp.solve((A.T*P+P*A+Q), P)
P = P.subs(res)
# P = ct.lyap(A,Q)
V = (X.T * P * X)    
print('Lyapunov function: ',V[0,0]) 
###############################################################################
#            Finding Lyapunov function using Krasovskii's Method
###############################################################################
# For a system => x_dot = A*x , Let J is Jacobian matrix of system.
# If matrix G = (J + J.T) is negative definite in neighbourhood of equilibrium, then locally stable
# If neighbourhood spans entire space then system is globally asymptotically stable. 
# And its Lyapunov function candidate is => V = A.T * A
'''
A = sp.Matrix([[-x1],[x1-x2-x2**3]])
J = A.jacobian(X)
G = J.T + J
Pminors = []   # principal minors
for i in range(G.rows):
    submatrix = G[0:i+1,0:i+1]
    Pminors.append(submatrix.det())
print('Principal minors of G: ',Pminors)
V = A.T * A
print('Lyapunov function: ',V[0,0])
'''
###############################################################################
#            Plot Lyapunov function
###############################################################################

# from sympy.plotting import plot3d
# p = plot3d(V[0, 0], (x1, -1, 1), (x2, -1, 1))

'''
array2mat = [{'ImmutableDenseMatrix': np.array}, 'numpy']
from sympy.utilities.lambdify import lambdify
lam_f_mat = lambdify((a,b), V, modules=array2mat)
Z =  lam_f_mat(X,Y)
Z = Z.reshape(len(x),len(y))
 
step = 0.5
x = np.arange(-5,5,step)
y = np.arange(-5,5,step)
X,Y = np.meshgrid(x,y)
Z = X - X

fig = plt.figure(figsize=(8,6))
from mpl_toolkits.mplot3d import axes3d
ax1 = fig.add_subplot(111,projection='3d')
mycmap = plt.get_cmap('gist_earth')
ax1.plot_wireframe(X, Y, Z, rstride=2, cstride=2)
ax1.plot_surface(X, Y, F, cmap=mycmap)
ax1.plot_surface(X, Y, G, cmap=mycmap)
plt.show()
'''
