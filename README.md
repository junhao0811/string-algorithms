# 🔎 String Algorithms

Four ways to find a pattern in text, each implemented from scratch in Python and each making a different trade-off: exact vs. approximate, preprocessing the pattern vs. preprocessing the text, deterministic vs. randomised.

| Folder | Algorithm | Finds | Preprocesses |
|---|---|---|---|
| [`exact-search/`](./exact-search) | Right-to-left KMP-style matcher | Exact matches | The pattern |
| [`approximate-search/`](./approximate-search) | Burrows–Wheeler Transform + FM-index backward search | Matches within **one edit** (insert, delete, substitute or swap) | The text |
| [`suffix-tree/`](./suffix-tree) | **Ukkonen's** linear-time suffix tree | The longest-common-prefix (LCP) array of all suffixes | The text |
| [`rabin-karp/`](./rabin-karp) | Rabin–Karp rolling hash with a **random prime** modulus | Exact matches | Nothing (hashing) |

---

## 1. Exact search: right-to-left KMP variant
Scans the pattern **right to left** while sliding it **leftwards** across the text, using a reversed failure function (computed with the **Z-algorithm**) to decide safe shifts after a mismatch. It also writes a run log of every comparison window.

```bash
cd exact-search
python exact_search.py tests/testcase_1_text.asc tests/testcase_1_pattern.asc
# output.txt -> 1-based match positions, runlog.txt -> comparison log
```

## 2. Approximate search: BWT + FM-index
Builds the **Burrows–Wheeler Transform** and suffix array of the text, then uses **backward search** to find every place the pattern occurs **exactly or within one edit**, including adjacent transpositions. Exact matches take priority over one-edit matches at the same position.

```bash
cd approximate-search
python approximate_search.py tests/insertion_text.asc tests/insertion_pattern.asc
# output.txt -> "<position> <distance>" per match
```

## 3. Ukkonen's suffix tree
Builds a suffix tree in **linear time** with Ukkonen's algorithm (active point, suffix links, the skip/count trick and the global-end trick), then derives the **LCP array** with a single depth-first traversal.

```bash
cd suffix-tree
echo -n "banana" > input.txt
python suffix_tree.py input.txt
# output.txt -> LCP array: 0 0 1 3 0 0 2
```
See [`suffix-tree/report.pdf`](./suffix-tree/report.pdf) for the design and complexity analysis.

## 4. Rabin–Karp with random primes
Classic rolling-hash matching, but the hash modulus is a **randomly chosen large prime**, found with the **Miller–Rabin** primality test and fast **modular exponentiation**. Random primes make adversarial hash collisions extremely unlikely, and every hash hit is double-checked to rule out false positives.

```bash
cd rabin-karp
python rabin_karp.py example_text.txt example_pattern.txt
# output.txt -> 1-based match positions
```
See [`rabin-karp/report.pdf`](./rabin-karp/report.pdf) for the analysis.

---

## ✅ Testing
Every algorithm was checked against a brute-force reference on hundreds of random inputs (exact search, Rabin–Karp and the suffix tree's LCP array against naive computation; approximate search against true edit distance), with no mismatches.

## 🛠️ Tech
Python 3, no external libraries.
