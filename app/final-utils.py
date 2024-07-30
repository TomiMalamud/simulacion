import numpy as np

def f(t, y, z):
    return z

def g(t, y, z):
    return 4 * z**2 + 6 * y + 8 * t

def rk4_step(t, y, z, h):
    k1 = h * f(t, y, z)
    l1 = h * g(t, y, z)
    
    k2 = h * f(t + 0.5*h, y + 0.5*k1, z + 0.5*l1)
    l2 = h * g(t + 0.5*h, y + 0.5*k1, z + 0.5*l1)
    
    k3 = h * f(t + 0.5*h, y + 0.5*k2, z + 0.5*l2)
    l3 = h * g(t + 0.5*h, y + 0.5*k2, z + 0.5*l2)
    
    k4 = h * f(t + h, y + k3, z + l3)
    l4 = h * g(t + h, y + k3, z + l3)
    
    y_new = y + (k1 + 2*k2 + 2*k3 + k4) / 6
    z_new = z + (l1 + 2*l2 + 2*l3 + l4) / 6
    
    return y_new, z_new

# Initial conditions
t = 0
y = 0  # Initial amount unloaded
z = 0  # Initial unloading rate
h = 0.01  # Step size

while y < 10:
    y, z = rk4_step(t, y, z, h)
    t += h

print(f"Time to unload 10 tons: {t:.2f} hours")
print(f"Final unloading rate: {z:.2f} tons/hour")