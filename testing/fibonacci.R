# Generate and print the first 10 Fibonacci numbers

fibonacci <- function(n) {
  if (n <= 0) {
    return(numeric(0))
  } else if (n == 1) {
    return(1)
  } else if (n == 2) {
    return(c(1, 1))
  }
  
  fib <- c(1, 1)
  for (i in 3:n) {
    fib[i] <- fib[i-1] + fib[i-2]
  }
  return(fib)
}

# Get first 10 Fibonacci numbers
result <- fibonacci(10)

# Print the result
print("First 10 Fibonacci numbers:")
print(result)
