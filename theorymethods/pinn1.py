import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt

# Set random seed for reproducibility
torch.manual_seed(42)

# Physics informed Neural network model
class PINN(nn.Module):
    def __init__(self):
        super(PINN, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(1, 32),  # Input: t
            nn.Tanh(),
            nn.Linear(32, 32),
            nn.Tanh(),
            nn.Linear(32, 1)   # Output: x(t)
        )
    
    def forward(self, t):
        return self.net(t)

# Function to compute derivatives
def get_derivatives(model, t):
    t = t.requires_grad_(True)
    x = model(t)
    dx_dt = torch.autograd.grad(x, t, grad_outputs=torch.ones_like(x), create_graph=True)[0]
    d2x_dt2 = torch.autograd.grad(dx_dt, t, grad_outputs=torch.ones_like(dx_dt), create_graph=True)[0]
    return x, dx_dt, d2x_dt2

# Loss function
def loss_fn(model, t):
    x, dx_dt, d2x_dt2 = get_derivatives(model, t)
    
    # Physics residual: d^2x/dt^2 + x = 0
    physics_loss = torch.mean((d2x_dt2 + x) ** 2)
    
    # Initial conditions: x(0) = 1, dx/dt(0) = 0
    t0 = torch.zeros((1, 1), dtype=torch.float32)
    x0, dx_dt0, _ = get_derivatives(model, t0)
    ic_loss = (x0 - 1.0) ** 2 + dx_dt0 ** 2
    
    return physics_loss + ic_loss

# Training setup
model = PINN()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
t_train = torch.linspace(0, 10, 100).reshape(-1, 1).float()

# Training loop
for epoch in range(1000):
    optimizer.zero_grad()
    loss = loss_fn(model, t_train)
    loss.backward()
    optimizer.step()
    if epoch % 100 == 0:
        print(f"Epoch {epoch}, Loss: {loss.item():.6f}")

# Plot result
t_test = torch.linspace(0, 10, 200).reshape(-1, 1)
with torch.no_grad():
    x_pred = model(t_test).numpy()
t_test = t_test.numpy()
plt.plot(t_test, x_pred, label="PINN Solution")
plt.plot(t_test, np.cos(t_test), '--', label="True Solution (cos(t))")
plt.legend()
plt.xlabel("t")
plt.ylabel("x(t)")
plt.show()