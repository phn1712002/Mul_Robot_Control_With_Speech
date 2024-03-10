def funcTimeDelayStep(lenght_max, value_max, current_point, slow=0.5):
  func = lambda x: value_max*slow*x**2
  x_norm = (2/lenght_max) * current_point - 1
  return func(x_norm)