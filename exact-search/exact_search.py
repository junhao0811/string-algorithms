import sys


def z_algo(s: str):
    """
    Function description: Computes the Z-array of a given string using Gusfield's Z-Algorithm, where z[i] is the length of the longest substring starting at s[i] that matches a prefix of s.

    Approach description:
        1. Maintain a Z-box [l, r] representing the rightmost matching window found so far, where s[l..r] matches s[0..r-l].

        2. For each index i, z[i] is determined using 2 cases:

            Case 1 (i > r): i is outside the Z-box, no prior info is available, so need to explicitly compare characters from s[0] and s[i] until a mismatch, then update Z-box if a match was found.

            Case 2 (i <= r): i is inside the Z-box:
                Case 2a:   z[k] < remaining space in Z-box -> z[i] = z[k]
                Case 2b.1: z[k] > remaining space -> z[i] = remaining
                Case 2b.2: z[k] == remaining space -> z[i] starts at remaining, then explicitly compare characters beyond the Z-box and update Z-box

    Input:
        s: a string to compute Z-array for

    Output: a list representing the Z-array, where z[i] is the length of the longest substring starting at s[i] that matches a prefix of s.

    Time complexity: O(N), where N is the length of s
    Time complexity analysis:
        The total time is proportional to the sum of iterations, successful explicit matches, and explicit mismatches. There are N-1 iterations. Successful explicit comparisons always advance the Z-box right boundary r, which never exceeds N, meaning there are at most N explicit matches globally. Explicit comparisons end immediately upon finding a mismatch, resulting in at most N-1 total mismatches. Thus, operations are bounded at O(N).

    Space complexity: O(N), where N is the length of s
    Space complexity analysis:
        The Z-array requires O(N) space to store one value per character in s.
        All other variables (l, r, k, remaining) require O(1) space.
    """
    n = len(s)
    z = [0] * n
    z[0] = None
    l, r = 0, 0

    for i in range(1, n):
        # CASE 1: Outside the Z-box (i > r)
        if i > r:
            # Explicitly compare characters as we know nothing
            while i + z[i] < n and s[z[i]] == s[i + z[i]]:
                z[i] += 1

            # Create a Z-box if we found a match
            if z[i] > 0:
                l, r = i, i + z[i] - 1

        # CASE 2: Inside the Z-box (i <= r)
        else:
            k, remaining = i - l, r - i + 1

            # CASE 2a: the previously computed match length is less than the remaining space in the Z-box
            if z[k] < remaining:
                z[i] = z[k]

            # CASE 2b.1: the previously computed match length is greater than the remaining space in the Z-box
            elif z[k] > remaining:
                z[i] = remaining

            # CASE 2b.2: the previously computed match length is exactly equal to the remaining space in the Z-box
            else:
                # The current match length is at least the amount of remaining space in the Z-box
                z[i] = remaining

                # Explicitly compare the unknown characters outside the Z-box
                while i + z[i] < n and s[z[i]] == s[i + z[i]]:
                    z[i] += 1

                # Update Z-box
                l, r = i, i + z[i] - 1

    return z


def compute_sp(pat: str):
    """
    Function description: Builds a SP array for a given pattern string, where sp[i] is the length of the longest proper suffix of pat[0..i] that matches a prefix of pat, such that the next character after the match differs.

    Approach description:
        1. Compute the Z-array of pat using z_algo, where Z[i] is the length of the longest substring starting at pat[i] that matches a prefix of pat.

        2. Loop from the end of pat down to index 1, and for each non-zero Z[i], compute the endpoint i = j + Z[j] - 1 of the matched prefix-suffix block.

        3. Store the Z-value at the endpoint, giving the length of the longest proper prefix-suffix match ending at that position and the next char should differ.

    Input:
        pat: a string representing the pattern to preprocess

    Output: a list of integers of length m, where sp[i] is the length of the longest proper suffix of pat[0..i] that matches a prefix of pat and the next character after the match differs

    Time complexity: O(M), where M is the length of pat
    Time complexity analysis: z_algo runs in O(M), and the loop iterates at most M-1 times performing O(1) work per iteration, giving O(M) + O(M) = O(M) total.

    Space complexity: O(M), where M is the length of pat
    Space complexity analysis: The sp array and Z-array each require O(M) space.
    """
    m = len(pat)
    z = z_algo(pat)
    sp = [0] * m

    # loop from end of pat down to 1 and populate sp array
    for j in range(m - 1, 0, -1):
        if z[j] > 0:
            # calculate endpoint of the longest suffix that matches the prefix
            i = j + z[j] - 1
            # throw the Z-value into sp at the endpoint
            sp[i] = z[j]
    return sp


def q1_search(
    txt: str,
    pat: str,
    output_filename: str = "output.txt",
    runlog_filename: str = "runlog.txt",
) -> None:
    """
    Function description: Finds all occurrences of pat in txt using a right-to-left scanning algorithm with leftward shifting, based on KMP concepts with Galil's optimization to achieve linear time complexity.

    Approach description:
        1. Preprocess pat by computing sp_rev = compute_sp(pat[::-1]), which captures suffix-suffix relationships in pat needed for the shift rule.

        2. Align the right end of pat with the right end of txt (j = n - m), and scan right-to-left comparing pat against txt[j..j+m-1].

        3. On full match (k < 0): log the match, then use the β fallback approach on sp_rev to find the longest valid β satisfying condition 2 (pat[p-1] == txt[j-1]), shift left by p, and apply Galil's optimization (k = p-1) to skip β characters.

        4. On mismatch at rightmost char (k == m-1): no alpha exists, shift left by 1.

        5. On mismatch at k < m-1: alpha, pat[k+1..m-1] is already matched. Use β fallback on sp_rev to find the longest valid β satisfying condition 2 (pat[p-1] == txt[j+k]), shift left by alpha-β, apply Galil's optimization (k = p-1).

        6. The β fallback chain tries progressively shorter β candidates via sp_rev[β-1] until condition 2 is satisfied or β reaches 0. If no valid β is found, shift by full alpha length with no reuse.

    Input:
        txt: a string representing the text to search in
        pat: a string representing the pattern to search for

    Output:
        Writes match positions to output_filename (one per line, 1-based) and
        writes runlog tuples <j> <k+1> <p> to runlog_filename (one per line, 0-based)

    Time complexity: O(N + M), where N is the length of txt and M is the length of pat
    Time complexity analysis:
        Preprocessing: compute_sp(pat[::-1]) runs z_algo internally in O(M) and constructs sp_rev in O(M), and pat[::-1] creates a reversed copy in O(M).
        Total preprocessing: O(M).

        Outer while loop (while j >= 0): j starts at n-m and decrements by at least 1 each iteration via j -= shift_distance, so the loop runs at most O(N) iterations.

        Inner while loop (while k >= 0 and txt[j+k] == pat[k]): Each k decrement corresponds to one character comparison at txt[j+k]. Galil's optimization
        (k = p-1) ensures β chars are skipped at the start of each iteration, so no txt position is ever recompared. Total k decrements across all iterations <= N.
        Total inner scan: O(N) amortised.

        β fallback chain (while β > 0): O(N) amortised across the entire search. Each fallback step decrements β by at least 1 via sp_rev[β-1], and β is bounded by the number of characters matched in prior iterations because of Galil's optimization (k = p-1). Since total number of characters matched across the entire search cannot exceed N, total β decrements across all fallback chains cannot exceed N either.
        Total fallback chain: O(N) amortised.

        The outer loop O(N) is already counted inside the inner loop and β fallback. The outer loop itself just bounds the number of iterations and it doesn't independently contribute O(N) work on top of the inner loops.

        Overall: O(M) + O(N) + O(N) = O(N + M)

    Space complexity: O(M), where M is the length of pat
    Space complexity analysis: sp_rev requires O(M) space. The reversed pat copy requires O(M) space.
    """
    n, m = len(txt), len(pat)

    with open(output_filename, "w") as output_file, open(runlog_filename, "w") as runlog_file:

        # edge cases
        if m == 0 or n == 0 or m > n:
            return

        # preprocess the whole pat and identify all sp[i] values - O(M) time and space
        sp_rev = compute_sp(pat[::-1])

        j = n - m  # current starting position in txt with the right end aligned
        k = m - 1  # tracks mismatch position starting from right end of pat

        # continue looping while there's enough room for a full pattern match
        while j >= 0:

            # scanning in the right-to-left direction using pat[m-1..0] against a region of txt[j..j+m-1], which is the text chunk corresponding to the length of pat
            # when the characters match, we move k leftwards to check the next character to the left
            while k >= 0 and txt[j + k] == pat[k]:
                k -= 1

            # for logging purposes
            k1 = k + 1

            # full match found, α = entire pat
            if k < 0:

                # log the matching index in txt via 1-based indexing
                output_file.write(f"{j + 1}\n")

                # look up longest reusable suffix length β for full match
                β = sp_rev[m - 1]

                # β fallback - O(N) amortized across entire search
                while β > 0:

                    # calc start of β in pat
                    p = m - β

                    # check condition 2: pat[p - 1] == txt[j - 1]
                    if j - 1 >= 0 and pat[p - 1] == txt[j - 1]:
                        break  # both condition 1 and condition 2 satisfied

                    # condition 2 not satisfied for this β, try next shorter β candidate
                    β = sp_rev[β - 1]

                # if no valid p found, β=0 -> p=m -> shift by full m, no reuse
                # if valid p found, β>0 -> p<m -> shift by p, reuse β characters
                p = m - β

                # shift pat leftwards by the non-reusable portion of α
                shift_distance = max(1, p)

                # skip re-comparing the β portion we already know match in the next iteration
                k = p - 1

            # mismatch at rightmost character of pat, no α exists, nothing matched, just shift by 1
            elif k == m - 1:
                shift_distance = 1
                p = m

            # mismatch at k, α = pat[k+1..m-1] already matched right side
            else:  # k < m - 1

                # α := length of matched suffix block pat[k+1..m-1]
                alpha = m - 1 - k

                # look up longest reusable suffix length β
                β = sp_rev[alpha - 1]

                # β fallback - O(N) amortized across entire search
                while β > 0:

                    # calc start of β in pat
                    p = m - β

                    # check condition 2: pat[p - 1] == txt[j + k]
                    if j + k < n and pat[p - 1] == txt[j + k]:
                        break  # both condition 1 and condition 2 satisfied

                    # condition 2 not satisfied for this β, try next shorter β candidate
                    β = sp_rev[β - 1]

                # if no valid p found, β=0 -> p=m -> shift by full α, no reuse
                # if valid p found, β>0 -> p<m -> shift by α-β, reuse β characters
                p = m - β

                # shift pat leftwards by the non-reusable portion of α
                shift_distance = max(1, alpha - β)

                # skip re-comparing the β portion we already know match in the next iteration
                k = p - 1

            # log current iteration variables j, k+1, p
            runlog_file.write(f"{j} {k1} {p}\n")

            # shift pat leftwards
            j -= shift_distance


# this function reads a file and return its content
def read_file(filename: str) -> str:
    f = open(filename, 'r')
    line = f.readline()
    f.close()

    return line


def main():
    # get filenames from CLI
    if len(sys.argv) != 3:
        print("Usage: python exact_search.py <text file> <pattern file>")
        return

    # retrive the file paths from the command line arguments
    _, text_file, pattern_file = sys.argv

    # read files
    text = read_file(text_file)
    pat = read_file(pattern_file)

    # run the algorithm
    q1_search(text, pat)


if __name__ == "__main__":
    main()
