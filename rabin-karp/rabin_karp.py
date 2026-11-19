import sys
import random

# alphabet size
β = 128


def mod_exp(base, exp, n):
    """
    Function description:
        Computes base^exp mod n using modular exponentiation by repeated squaring, using the alternative method by scanning the binary representation of exp from MSB to LSB.

    Approach description:
        1. Convert exp to its binary representation.
        2. Initialise result r = 1.
        3. For each bit from MSB to LSB: square r, then multiply by base if the bit is 1.
        4. Apply mod n at each step to keep intermediate values bounded.

    Input:
        base (int): the base
        exp  (int): the exponent
        n    (int): the modulus

    Output:
        int: base^exp mod n
    """
    binary_rep = bin(exp)[2:]
    r = 1
    for bit in binary_rep:  # MSB -> LSB
        r = (r * r) % n  # square
        if bit == "1":
            r = (r * base) % n  # multiply
    return r


def is_even(n):
    """
    Function description:
        Returns True if n is even, False otherwise.

    Input:
        n (int): integer to check

    Output:
        bool: True if n is even
    """
    return n % 2 == 0


def factor_n_minus_one(n):
    """
    Function description:
        Factor n - 1 as 2^s * t, where t is odd.
        Required as a preprocessing step for the Miller-Rabin primality test.

    Approach description:
        Repeatedly divide n - 1 by 2, counting divisions, until the result is odd.

    Input:
        n (int): an odd integer

    Output:
        (s, t): tuple where s (int) is the exponent of 2 and t (int) is the odd remainder, satisfying n - 1 = 2^s * t
    """
    s, t = 0, n - 1
    while is_even(t):
        s += 1
        t //= 2
    return s, t


def miller_rabin_pass(a, n, s, t):
    """
    Function description:
        Performs a single Miller-Rabin witness test for base a against candidate n.
        Returns True if n is probably prime with respect to base a, False if n is definitively composite.

    Approach description:
        Given n - 1 = 2^s * t (t odd), compute the sequence:
            x_0 = a^t mod n, x_1 = x_0^2 mod n, ..., x_s = x_{s-1}^2 mod n
        Apply four cases:
            Case 1: x_s != 1                         -> composite
            Case 2: x_i = 1 and x_{i-1} != n-1       -> composite
            Case 3: x_i = 1 and x_{i-1} = n-1        -> probably prime
            Case 4: x_0 = 1                          -> probably prime

    Input:
        a (int): witness base, 2 <= a <= n-2
        n (int): odd candidate integer
        s (int): exponent of 2 in the factorisation n-1 = 2^s * t
        t (int): odd part of n-1

    Output:
        bool: True if n passes this witness test (probably prime), False if composite
    """
    # compute x_0
    # x_0 = a^t mod n
    x = mod_exp(a, t, n)

    # case 4: x_0 = 1 -> probably prime
    if x == 1:
        return True

    # compute from x_1 until x_s
    for _ in range(s):
        x_prev, x = x, (x * x) % n

        if x == 1:
            # case 2: x_i = 1 and x_{i-1} != n - 1 -> composite
            if x_prev != n - 1:
                return False

            # case 3: x_i = 1 and x_{i-1} = n - 1 -> probably prime
            return True

    # case 1: x_s != 1 -> composite
    return False


def is_prime(n, k=20):
    """
    Function description:
        Probabilistic Miller-Rabin primality test. Returns True if n is probably prime, False if n is definitively composite.

    Approach description:
        1. Handle base cases: n < 2 is not prime, n = 2 or 3 are prime, an even n is not prime.
        2. Factor n - 1 = 2^s * t.
        3. Run k rounds, each choosing a random witness base a in [2, n-2] and
           calling miller_rabin_pass. If any round returns False, n is composite.
        4. If all k rounds pass, n is probably prime.

    Input:
        n (int): candidate integer to test
        k (int): number of witness rounds

    Output:
        bool: True if n is probably prime, False if composite
    """
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if is_even(n):
        return False

    # factor n - 1 as 2^s * t, where t is odd
    s, t = factor_n_minus_one(n)

    # conduct k random tests
    for _ in range(k):
        a = random.randint(2, n - 2)
        if not miller_rabin_pass(a, n, s, t):
            return False
    return True


def find_prime(t):
    """
    Function description:
        Randomly samples odd integers from [2^(t-1), 2^t - 1] until a probable prime is found, then returns it.

    Approach description:
        1. Compute lo and hi.
        2. Ensure lo is odd (+1 if even).
        3. Repeatedly draw a random odd candidate via randrange(lo, hi+1, 2) and test it with is_prime until a prime is found.

    Input:
        t (int): bit-length parameter where samples are drawn from the t-bit range

    Output:
        int: probably a prime integer in [2^(t-1), 2^t - 1]
    """
    lo = 1 << (t - 1)  # 2^(t-1)
    hi = (1 << t) - 1  # 2^t - 1

    # make sure lo is odd to skip even numbers
    if is_even(lo):
        lo += 1

    while True:
        # sample uniformly from odd numbers in [lo, hi]
        candidate = random.randrange(lo, hi + 1, 2)
        if is_prime(candidate):
            return candidate


def rabin_karp(txt, pat, out):
    """
    Function description:
        Finds all positions where pat occurs in txt using the Rabin-Karp semi-numerical pattern matching algorithm with a rolling hash, and each match position to the output file.

    Approach description:
        1. Generate a random t-bit prime p (t = max(32, m)) as the hash modulus.
        2. Compute the hash of the pattern:
               r(pat) = sum(ord(pat[i]) * β^(m-1-i) for i in 0..m-1) mod p
        3. Compute the hash of the initial text window txt[0..m-1] using the same formula.
        4. Slide the window across txt. At each position j (0-indexed):
               - If r(txt) == r(pat), verify character-by-character to eliminate false positives.
               - Roll the hash forward in O(1) using:
                     r_new = (r_old - ord(txt[j]) * β^(m-1)) * β + ord(txt[j+m]) mod p
        5. Output matching positions using 1-based indexing.

    Input:
        txt (str): the text string to search in
        pat (str): the pattern string to search for
        out (file): open output file to write match positions to

    Output:
        Writes each 1-based match position to out, one per line.
        If no matches are found, nothing is written.
    """
    n, m = len(txt), len(pat)

    if m > n:
        return

    # choose prime modulus
    t = max(32, m)
    p = find_prime(t)

    # precompute β^(m-1) mod p (needed for rolling hash subtraction)
    β_m1 = mod_exp(β, m - 1, p)

    # compute hash of pattern
    r_pat = 0
    for c in pat:
        r_pat = (r_pat * β + ord(c)) % p

    # compute initial window hash: txt[0..m-1]
    r_txt = 0
    for i in range(m):
        r_txt = (r_txt * β + ord(txt[i])) % p

    for j in range(n - m + 1):
        # hash match, verify to eliminate false positives
        if r_txt == r_pat:
            if txt[j : j + m] == pat:
                out.write(str(j + 1) + "\n")  # 1-based indexing

        # roll hash to next window
        if j < n - m:
            r_txt = (r_txt - ord(txt[j]) * β_m1) % p
            r_txt = (r_txt * β + ord(txt[j + m])) % p


# this function reads a file and return its content
def read_file(filename: str) -> str:
    f = open(filename, "r")
    line = f.readline().rstrip("\n")
    f.close()
    return line


def main():
    # get filenames from CLI
    if len(sys.argv) != 3:
        print("Usage: python rabin_karp.py <text_filename> <pattern_filename>")
        sys.exit(1)

    # retrieve the file paths from the command line arguments
    _, text_file, pattern_file = sys.argv

    # read files
    txt = read_file(text_file)
    pat = read_file(pattern_file)

    with open("output.txt", "w") as out:
        rabin_karp(txt, pat, out)


if __name__ == "__main__":
    main()
