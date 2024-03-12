def funcTimeDelayStep(lenght_max, value_max, current_point):
  #? [0, lenght_max] -> [-1, 1]
  x_norm = (2/lenght_max) * current_point - 1
  
  #? f(x) = value_max*X^2
  func = lambda x: value_max*x**2 
  
  #? x = [0, lenght_max/2] => v = vmax 
  #? x = [lenght_max/2, lenght_max] => v = vmax - v(value_max*x**2)  
  time_add = None
  if x_norm > 0:
    time_add = func(x_norm)
  elif x_norm <= 0:
    time_add = 0 
  return time_add