import sys

ASCII_START = 36
ASCII_END = 126
Σ = ASCII_END - ASCII_START + 1
TERMINAL = "$"

# The input's terminal character is unique and should not be generated as
# part of a candidate pattern.  The remaining printable ASCII characters are
# treated as the constant-size alphabet for one-edit variants.
ALPHABET = [chr(i) for i in range(ASCII_START, ASCII_END + 1) if chr(i) != TERMINAL]


def construct_bwt(text: str):
    # add '$' behind text
    text += TERMINAL

    # generate suffixes and get their suffix ids
    suffixes = []
    for i in range(len(text)):
        suffixes.append((text[i:], i))

    # sort suffixes lexicographically
    suffixes.sort()

    # build suffix array
    sa = [suffix_id for _, suffix_id in suffixes]

    # construct BWT from last column of sorted suffixes, a.k.a. the character preceding the suffix
    bwt = []
    for suffix_id in sa:
        if suffix_id == 0:
            bwt.append(TERMINAL)
        else:
            bwt.append(text[suffix_id - 1])

    return "".join(bwt), sa


def preprocess_bwt(l: str):
    """
    time and space: O(n * |Σ|) => O(n) since |Σ| is a constant
    """
    n = len(l)

    # build count array
    count = [0] * Σ
    for c in l:
        count[ord(c) - ASCII_START] += 1

    # build rank array
    rank = [0] * Σ
    total = 0
    for i in range(Σ):
        rank[i] = total
        total += count[i]

    # initialize 2D nOccurrences table
    n_occ = [[0] * n for _ in range(Σ)]

    # loop through L/bwt to populate nOccurrences table
    for j in range(n):
        char_pos = ord(l[j]) - ASCII_START

        # loop through unique characters to copy previous number of occurrences
        for i in range(Σ):
            if j > 0:
                n_occ[i][j] = n_occ[i][j - 1]

        # increment current character's number of occurrence
        n_occ[char_pos][j] += 1

    return count, rank, n_occ


def backward_search(
    count: list[int], rank: list[int], n_occ: list[list[int]], sa: list[int], pat: str
):
    """
    time: O(m) where m is |pat|, space: O(1)
    """
    sp, ep = 0, len(sa) - 1

    for i in range(len(pat) - 1, -1, -1):
        char_pos = ord(pat[i]) - ASCII_START

        # Any character outside the indexed alphabet cannot be matched.
        if char_pos < 0 or char_pos >= Σ:
            return []

        if count[char_pos] == 0:
            return []  # pattern not found

        # calculate multiplicity
        sp = rank[char_pos] + (n_occ[char_pos][sp - 1] if sp > 0 else 0)
        ep = rank[char_pos] + n_occ[char_pos][ep] - 1

        if ep < sp:
            return []

    return [sa[i] for i in range(sp, ep + 1)]


def generate_distance_one_variants(pat: str):
    """
    Generate every unique pattern string that is exactly one edit away from pat.
    The returned candidates are intended to be searched exactly with the BWT
    index.  Each operation is defined from the pattern's point of view, matching
    the problem specification.

    time: O(|Σ| * m^2), where m is |pat|, because each generated string can
    require slicing/copying O(m) characters. Since |Σ| is constant, this is
    O(m^2). space: O(|Σ| * m^2) in the worst case to store the unique variants.
    """
    variants = set()
    m = len(pat)

    # Substitution: replace exactly one pattern character with a different
    # alphabet character. The length remains m.
    for i in range(m):
        for c in ALPHABET:
            if c != pat[i]:
                variants.add(pat[:i] + c + pat[i + 1 :])

    # Transposition: swap one adjacent pair of distinct characters. Equal
    # adjacent characters are skipped because swapping them changes nothing.
    for i in range(m - 1):
        if pat[i] != pat[i + 1]:
            variants.add(pat[:i] + pat[i + 1] + pat[i] + pat[i + 2 :])

    # Insertion into the pattern: insert one alphabet character at any gap.
    # These candidates match text substrings of length m + 1.
    for i in range(m + 1):
        for c in ALPHABET:
            variants.add(pat[:i] + c + pat[i:])

    # Deletion from the pattern: remove one pattern character. These candidates
    # match text substrings of length m - 1. When m == 1 this would create the
    # empty string, which is not searched as a text substring here.
    if m > 1:
        for i in range(m):
            variants.add(pat[:i] + pat[i + 1 :])

    # Guard against any accidental exact-pattern candidate, so exact matches can
    # be handled separately with distance 0 precedence.
    variants.discard(pat)
    return variants


def distance_at_most_one_search(
    count: list[int], rank: list[int], n_occ: list[list[int]], sa: list[int], pat: str
):
    """
    Search pat against the BWT index under match-distance <= 1.
    Exact matches are searched first and stored with distance 0. Every one-edit
    variant is then exact-searched; a position already holding distance 0 is left
    unchanged to satisfy the required precedence rule.
    """
    matches = {}

    # Distance 0: exact pattern match.
    for pos in backward_search(count, rank, n_occ, sa, pat):
        matches[pos] = 0

    # Distance 1: exact-search each generated one-edit variant.
    for variant in generate_distance_one_variants(pat):
        for pos in backward_search(count, rank, n_occ, sa, variant):
            if pos not in matches:
                matches[pos] = 1

    return sorted(matches.items())


# this function reads a file and return its content
def read_file(filename: str) -> str:
    f = open(filename, "r")
    line = f.readline().strip()
    f.close()
    return line


def write_output(results, filename="output.txt"):
    with open(filename, "w") as f:
        for pos, dist in results:
            f.write(f"{pos + 1} {dist}\n")  # convert to 1-based index


def main():
    # get filenames from CLI
    if len(sys.argv) != 3:
        print("Usage: python approximate_search.py <text file> <pattern file>")
        return

    _, text_file, pattern_file = sys.argv

    # read files
    text = read_file(text_file)
    pat = read_file(pattern_file)

    # logic
    bwt, sa = construct_bwt(text)
    count, rank, n_occ = preprocess_bwt(bwt)
    res = distance_at_most_one_search(count, rank, n_occ, sa, pat)

    # write output
    write_output(res)


if __name__ == "__main__":
    main()
