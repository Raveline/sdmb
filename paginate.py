
def paginate(from_, size, maximum):
   previous = (from_ - size) 
   previous = -1 if previous < 0 else previous
   next = (from_ + size) 
   next = 0 if next > (maximum - 1) else next
   return (previous, next)


